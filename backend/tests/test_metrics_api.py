import asyncio
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

from app.core.config import Settings
from app.core.security import hash_password
from app.main import create_app
from app.models import Chatbot, LlmModel, Query, User


@pytest.mark.integration
def test_metrics_charts_filters_isolation_validation_and_authorization():
    settings = Settings(session_ttl_minutes=60)
    if settings.database_url is None:
        pytest.skip("DATABASE_URL is not configured")
    asyncio.run(_exercise_metrics(settings))


async def _exercise_metrics(settings):
    application = create_app(settings)
    user_id, model_id, bot_a, bot_b = [uuid4() for _ in range(4)]
    email, password = f"charts-{user_id}@bidachat.test", "metrics test password"
    first = datetime(2026, 1, 31, 23, 30, tzinfo=UTC)
    last = datetime(2026, 2, 2, 12, tzinfo=UTC)
    async with application.router.lifespan_context(application):
        database = application.state.database
        try:
            async with database.session() as session:
                session.add_all(
                    [
                        User(
                            id=user_id,
                            email=email,
                            password_hash=hash_password(password),
                        ),
                        LlmModel(
                            id=model_id,
                            provider="test-provider",
                            model=f"charts-{model_id}",
                        ),
                    ]
                )
                await session.flush()
                session.add_all(
                    [
                        Chatbot(
                            id=id_,
                            created_by=user_id,
                            configured_llm_model_id=model_id,
                            name=f"Chart {id_}",
                        )
                        for id_ in (bot_a, bot_b)
                    ]
                )
                await session.flush()
                for bot_id, timestamp, status, elapsed in [
                    (bot_a, first, "completed", 100),
                    (bot_a, last, "completed", 300),
                    (bot_a, last, "failed", 50),
                    (bot_a, last, "processing", None),
                    (bot_b, first, "completed", 900),
                ]:
                    session.add(
                        Query(
                            chatbot_id=bot_id,
                            executed_llm_model_id=model_id,
                            question="Fixture question",
                            received_at=timestamp,
                            status=status,
                            response_time_ms=elapsed,
                            answer="Fixture answer" if status == "completed" else None,
                            error_code="LLM_TIMEOUT" if status == "failed" else None,
                            completed_at=timestamp + timedelta(milliseconds=elapsed)
                            if elapsed is not None
                            else None,
                        )
                    )
                await session.commit()
            async with AsyncClient(
                transport=ASGITransport(app=application), base_url="http://testserver"
            ) as client:
                endpoint = f"/api/v1/chatbots/{bot_a}/metrics"
                assert (await client.get(endpoint)).status_code == 401
                login = await client.post(
                    "/api/v1/auth/login", json={"email": email, "password": password}
                )
                assert login.status_code == 200
                headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
                params = {
                    "started_at": "2026-01-31T00:00:00Z",
                    "ended_at": "2026-02-03T00:00:00Z",
                    "include_series": "true",
                }
                response = await client.get(endpoint, headers=headers, params=params)
                assert response.status_code == 200, response.text
                data = response.json()
                assert data["total_queries"] == 4
                assert data["average_response_time_ms"] == 200
                assert data["measured_response_count"] == 2
                assert [p["total_queries"] for p in data["series"]] == [1, 0, 3]
                assert [p["average_response_time_ms"] for p in data["series"]] == [
                    100,
                    None,
                    300,
                ]
                assert (
                    sum(p["failed_queries"] for p in data["series"])
                    == data["failed_queries"]
                    == 1
                )
                filtered = (
                    await client.get(
                        endpoint,
                        headers=headers,
                        params={**params, "query_status": "failed"},
                    )
                ).json()
                assert filtered["total_queries"] == 1
                assert filtered["average_response_time_ms"] is None
                assert [p["total_queries"] for p in filtered["series"]] == [0, 0, 1]
                for grouping in ("week", "month"):
                    grouped = (
                        await client.get(
                            endpoint,
                            headers=headers,
                            params={**params, "interval": grouping},
                        )
                    ).json()
                    assert [p["total_queries"] for p in grouped["series"]] == [1, 3]
                    assert grouped["series"][0]["period_start"].startswith(
                        "2026-01-26" if grouping == "week" else "2026-01-01"
                    )
                offset = (
                    await client.get(
                        endpoint,
                        headers=headers,
                        params={**params, "started_at": "2026-01-31T00:00:00-05:00"},
                    )
                ).json()
                assert offset["series"][0]["period_start"].startswith(
                    "2026-01-31T00:00:00"
                )
                empty = (
                    await client.get(
                        endpoint,
                        headers=headers,
                        params={
                            **params,
                            "started_at": "2026-03-01T00:00:00Z",
                            "ended_at": "2026-03-03T00:00:00Z",
                        },
                    )
                ).json()
                assert empty["total_queries"] == 0
                assert len(empty["series"]) == 2
                assert all(
                    p["average_response_time_ms"] is None for p in empty["series"]
                )
                # The end boundary is exclusive; Feb 2 records must not leak in.
                bounded = (
                    await client.get(
                        endpoint,
                        headers=headers,
                        params={**params, "ended_at": "2026-02-02T00:00:00Z"},
                    )
                ).json()
                assert bounded["total_queries"] == 1
                for invalid in [
                    {"interval": "year"},
                    {"query_status": "unknown"},
                    {"started_at": "2026-02-04T00:00:00Z"},
                    {"started_at": "2026-01-31T00:00:00"},
                    {"started_at": "2020-01-01T00:00:00Z"},
                ]:
                    assert (
                        await client.get(
                            endpoint, headers=headers, params={**params, **invalid}
                        )
                    ).status_code == 422
                assert (
                    await client.get(
                        f"/api/v1/chatbots/{uuid4()}/metrics", headers=headers
                    )
                ).status_code == 404
                plain = (await client.get(endpoint, headers=headers)).json()
                assert plain["series"] == [] and plain["total_queries"] == 4
        finally:
            async with database.session() as session:
                await session.execute(
                    delete(Chatbot).where(Chatbot.created_by == user_id)
                )
                await session.execute(delete(User).where(User.id == user_id))
                await session.execute(delete(LlmModel).where(LlmModel.id == model_id))
                await session.commit()
