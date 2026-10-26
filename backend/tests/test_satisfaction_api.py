import asyncio
import base64
import hmac
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from app.api.satisfaction import _requests
from app.core.config import Settings
from app.core.security import hash_password
from app.main import create_app
from app.models import (
    Chatbot,
    Conversation,
    ConversationFeedback,
    LlmModel,
    Query,
    User,
)
from app.services.satisfaction_metrics_service import SatisfactionMetricsService
from app.services.satisfaction_service import SatisfactionService
from app.services.widget_identity_service import (
    scoped_signing_key,
    verify_widget_identity,
)


@pytest.mark.integration
def test_satisfaction_lifecycle_and_isolation():
    source = Settings()
    if source.database_url is None:
        pytest.skip("DATABASE_URL is not configured")
    settings = Settings(
        app_env="test",
        database_url=source.database_url,
        widget_allowed_origins="http://testserver,https://other.test",
        widget_identity_master_key="x" * 48,
    )
    asyncio.run(_exercise_satisfaction(settings))


async def _exercise_satisfaction(settings: Settings):
    _requests.clear()
    application = create_app(settings)
    ids = [uuid4() for _ in range(9)]
    (
        user_id,
        model_id,
        bot_a,
        bot_b,
        conversation_id,
        other_id,
        empty_id,
        expired_id,
        identity_id,
    ) = ids
    now = datetime.now(UTC)
    subject = "a" * 64
    expiry = str(int(now.timestamp()) + 300)
    signed_message = f"v1.{subject}.{expiry}"
    signature = (
        base64.urlsafe_b64encode(
            hmac.digest(
                scoped_signing_key(settings, bot_a, "http://testserver"),
                signed_message.encode(),
                "sha256",
            )
        )
        .rstrip(b"=")
        .decode()
    )
    identity_token = f"{signed_message}.{signature}"
    identity_hash = verify_widget_identity(
        settings, chatbot_id=bot_a, origin="http://testserver", token=identity_token
    )
    email, password = f"survey-{user_id}@bidachat.test", "survey test password"
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
                            model=f"survey-{model_id}",
                        ),
                    ]
                )
                await session.flush()
                session.add_all(
                    [
                        Chatbot(
                            id=bot_id,
                            created_by=user_id,
                            configured_llm_model_id=model_id,
                            name=f"Survey {bot_id}",
                        )
                        for bot_id in (bot_a, bot_b)
                    ]
                )
                await session.flush()
                for conv_id, bot_id, origin, expiry, identity in (
                    (
                        conversation_id,
                        bot_a,
                        "http://testserver",
                        now + timedelta(hours=1),
                        None,
                    ),
                    (
                        other_id,
                        bot_b,
                        "http://testserver",
                        now + timedelta(hours=1),
                        None,
                    ),
                    (
                        empty_id,
                        bot_a,
                        "http://testserver",
                        now + timedelta(hours=1),
                        None,
                    ),
                    (
                        expired_id,
                        bot_a,
                        "http://testserver",
                        now - timedelta(minutes=1),
                        None,
                    ),
                    (
                        identity_id,
                        bot_a,
                        "http://testserver",
                        now + timedelta(hours=1),
                        identity_hash,
                    ),
                ):
                    session.add(
                        Conversation(
                            id=conv_id,
                            chatbot_id=bot_id,
                            origin=origin,
                            identity_hash=identity,
                            created_at=now - timedelta(hours=2),
                            last_active_at=now - timedelta(minutes=1),
                            expires_at=expiry,
                        )
                    )
                await session.flush()
                for conv_id, bot_id in (
                    (conversation_id, bot_a),
                    (other_id, bot_b),
                    (expired_id, bot_a),
                    (identity_id, bot_a),
                ):
                    session.add(
                        Query(
                            chatbot_id=bot_id,
                            conversation_id=conv_id,
                            executed_llm_model_id=model_id,
                            question="A question",
                            answer="An answer",
                            status="completed",
                            received_at=now - timedelta(minutes=5),
                            completed_at=now - timedelta(minutes=4),
                            response_time_ms=100,
                        )
                    )
                await session.commit()

            async with AsyncClient(
                transport=ASGITransport(app=application), base_url="http://testserver"
            ) as client:
                base = f"/api/v1/chatbots/{bot_a}"
                origin = {"Origin": "http://testserver"}
                offer = {"conversation_id": str(conversation_id)}
                response = {
                    **offer,
                    "satisfaction_score": 4,
                    "resolution": "yes",
                    "clarity_score": 5,
                    "comment": "<script>alert(1)</script>",
                }
                for path in ("survey-offers", "survey-responses"):
                    assert (
                        await client.post(f"{base}/{path}", json=response)
                    ).status_code == 403
                    assert (
                        await client.post(
                            f"{base}/{path}",
                            json=response,
                            headers={"Origin": "https://other.test"},
                        )
                    ).status_code == 404
                    assert (
                        await client.post(
                            f"/api/v1/chatbots/{bot_b}/{path}",
                            json=response,
                            headers=origin,
                        )
                    ).status_code == 404
                    for invalid_id in (empty_id, expired_id, identity_id, uuid4()):
                        assert (
                            await client.post(
                                f"{base}/{path}",
                                json={**response, "conversation_id": str(invalid_id)},
                                headers=origin,
                            )
                        ).status_code == 404

                first, second = await asyncio.gather(
                    *(
                        client.post(f"{base}/survey-offers", json=offer, headers=origin)
                        for _ in range(2)
                    )
                )
                assert first.status_code == second.status_code == 200
                assert first.json() == second.json() == {"state": "offered"}
                assert (
                    await client.post(
                        f"{base}/survey-responses", json=response, headers=origin
                    )
                ).status_code == 200
                assert (
                    await client.post(
                        f"{base}/survey-responses", json=response, headers=origin
                    )
                ).status_code == 200
                assert (
                    await client.post(
                        f"{base}/survey-responses",
                        json={**response, "satisfaction_score": 1},
                        headers=origin,
                    )
                ).status_code == 409
                for invalid in (
                    {**response, "satisfaction_score": 0},
                    {**response, "clarity_score": 6},
                    {**response, "resolution": "unknown"},
                    {**response, "comment": "x" * 1001},
                    {**response, "comment": "texto\x00inválido"},
                ):
                    assert (
                        await client.post(
                            f"{base}/survey-responses", json=invalid, headers=origin
                        )
                    ).status_code == 422

                metrics_url = f"{base}/satisfaction-metrics"
                comments_url = f"{base}/survey-responses"
                assert (await client.get(metrics_url)).status_code == 401
                assert (await client.get(comments_url)).status_code == 401
                login = await client.post(
                    "/api/v1/auth/login", json={"email": email, "password": password}
                )
                assert login.status_code == 200
                auth = {"Authorization": f"Bearer {login.json()['access_token']}"}
                metrics = (await client.get(metrics_url, headers=auth)).json()
                assert metrics["offers"] == metrics["responses"] == 1
                assert metrics["participation_rate"] == 1
                assert metrics["csat_rate"] == 1
                assert metrics["average_clarity"] == 5
                assert metrics["resolution_rate"] == 1
                assert metrics["scores"]["4"] == 1
                period = {
                    "started_at": (now - timedelta(days=1)).isoformat(),
                    "ended_at": (now + timedelta(days=1)).isoformat(),
                    "interval": "day",
                }
                grouped = (
                    await client.get(metrics_url, headers=auth, params=period)
                ).json()
                assert len(grouped["series"]) >= 2
                assert sum(point["offers"] for point in grouped["series"]) == 1
                assert grouped["offers"] == 1
                outside = (
                    await client.get(
                        metrics_url,
                        headers=auth,
                        params={
                            "started_at": (now + timedelta(days=2)).isoformat(),
                            "ended_at": (now + timedelta(days=3)).isoformat(),
                        },
                    )
                ).json()
                assert outside["offers"] == 0
                assert outside["csat_rate"] is None
                assert (
                    await client.get(
                        metrics_url,
                        headers=auth,
                        params={**period, "started_at": "2026-01-01T00:00:00"},
                    )
                ).status_code == 422
                assert (
                    await client.get(
                        f"/api/v1/chatbots/{bot_b}/satisfaction-metrics", headers=auth
                    )
                ).json()["offers"] == 0
                comments = (await client.get(comments_url, headers=auth)).json()
                assert comments["total"] == 1
                assert comments["items"][0]["comment"] == response["comment"]
                assert "conversation_id" not in str(comments)
                assert (
                    await client.get(comments_url, headers=auth, params={"limit": 51})
                ).status_code == 422
                signed_offer = {
                    "conversation_id": str(identity_id),
                    "identity_token": identity_token,
                }
                assert (
                    await client.post(
                        f"{base}/survey-offers", json=signed_offer, headers=origin
                    )
                ).status_code == 200
                assert (
                    await client.post(
                        f"{base}/survey-responses",
                        json={**signed_offer, "satisfaction_score": 2},
                        headers=origin,
                    )
                ).status_code == 200
                assert (
                    await client.post(
                        f"{base}/survey-offers",
                        json={
                            **signed_offer,
                            "identity_token": identity_token[:-1]
                            + ("x" if identity_token[-1] != "x" else "y"),
                        },
                        headers=origin,
                    )
                ).status_code == 401
                limited = [
                    (
                        await client.post(
                            f"{base}/survey-offers",
                            json={"conversation_id": str(uuid4())},
                            headers=origin,
                        )
                    ).status_code
                    for _ in range(22)
                ]
                assert 429 in limited

            async with database.session() as session:
                feedback = await session.scalar(
                    select(ConversationFeedback).where(
                        ConversationFeedback.conversation_id == conversation_id
                    )
                )
                feedback.offered_at = now - timedelta(days=91)
                feedback.submitted_at = now - timedelta(days=91)
                conversation = await session.get(Conversation, conversation_id)
                conversation.expires_at = now - timedelta(seconds=1)
                await session.commit()
            async with database.session() as session:
                assert (
                    await SatisfactionService().redact_expired_comments(
                        session, now=now
                    )
                    == 1
                )
                await session.execute(
                    delete(Conversation).where(Conversation.id == conversation_id)
                )
                await session.commit()
            async with database.session() as session:
                feedback = await session.scalar(
                    select(ConversationFeedback).where(
                        ConversationFeedback.conversation_id == conversation_id
                    )
                )
                assert feedback is not None and feedback.comment is None
                result = await SatisfactionMetricsService().get_metrics(
                    session,
                    chatbot_id=bot_a,
                    started_at=None,
                    ended_at=None,
                    interval="day",
                )
                assert result.offers == result.responses == 2
                await session.execute(delete(Chatbot).where(Chatbot.id == bot_a))
                await session.commit()
                assert (
                    await session.scalar(
                        select(ConversationFeedback).where(
                            ConversationFeedback.conversation_id == conversation_id
                        )
                    )
                    is None
                )
        finally:
            async with database.session() as session:
                await session.execute(
                    delete(Chatbot).where(Chatbot.created_by == user_id)
                )
                await session.execute(delete(User).where(User.id == user_id))
                await session.execute(delete(LlmModel).where(LlmModel.id == model_id))
                await session.commit()
