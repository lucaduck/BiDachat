import asyncio
import sys
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

from app.core.config import Settings
from app.core.security import hash_password
from app.main import create_app
from app.models import Chatbot, LlmModel, User


@pytest.mark.integration
def test_authenticated_chatbot_crud_preserves_identifier_and_configuration():
    settings = Settings(session_ttl_minutes=60)
    if settings.database_url is None:
        pytest.skip("DATABASE_URL is not configured")

    loop_factory = asyncio.SelectorEventLoop if sys.platform == "win32" else None
    with asyncio.Runner(loop_factory=loop_factory) as runner:
        runner.run(_exercise_chatbot_crud(settings))


async def _exercise_chatbot_crud(settings: Settings) -> None:
    application = create_app(settings)
    user_id = uuid4()
    first_model_id = uuid4()
    second_model_id = uuid4()
    email = f"chatbot-api-{user_id}@bidachat.test"
    password = "valid chatbot API password"

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
                            id=first_model_id,
                            provider="test-provider",
                            model=f"model-a-{first_model_id}",
                        ),
                        LlmModel(
                            id=second_model_id,
                            provider="test-provider",
                            model=f"model-b-{second_model_id}",
                        ),
                    ]
                )
                await session.commit()

            transport = ASGITransport(app=application)
            async with AsyncClient(
                transport=transport,
                base_url="http://testserver",
            ) as client:
                assert (await client.get("/api/v1/chatbots")).status_code == 401

                login_response = await client.post(
                    "/api/v1/auth/login",
                    json={"email": email, "password": password},
                )
                access_token = login_response.json()["access_token"]
                headers = {"Authorization": f"Bearer {access_token}"}

                models_response = await client.get(
                    "/api/v1/llm-models",
                    headers=headers,
                )
                assert models_response.status_code == 200
                model_ids = {item["id"] for item in models_response.json()}
                assert str(first_model_id) in model_ids
                assert str(second_model_id) in model_ids

                blank_name_response = await client.post(
                    "/api/v1/chatbots",
                    headers=headers,
                    json={
                        "name": "   ",
                        "configured_llm_model_id": str(first_model_id),
                    },
                )
                assert blank_name_response.status_code == 422

                create_response = await client.post(
                    "/api/v1/chatbots",
                    headers=headers,
                    json={
                        "name": "Dashboard financiero",
                        "description": "Indicadores institucionales",
                        "behavior_instructions": "Responde de forma concisa.",
                        "configured_llm_model_id": str(first_model_id),
                    },
                )
                assert create_response.status_code == 201
                created = create_response.json()
                chatbot_id = created["id"]
                assert created["created_by"] == str(user_id)
                assert created["configured_llm_model"]["id"] == str(first_model_id)

                assert (
                    await client.get(f"/api/v1/chatbots/{chatbot_id}/metrics")
                ).status_code == 401
                metrics_response = await client.get(
                    f"/api/v1/chatbots/{chatbot_id}/metrics",
                    headers=headers,
                )
                assert metrics_response.status_code == 200
                assert metrics_response.json()["total_queries"] == 0
                assert metrics_response.json()["average_response_time_ms"] is None

                list_response = await client.get("/api/v1/chatbots", headers=headers)
                assert list_response.status_code == 200
                assert chatbot_id in {item["id"] for item in list_response.json()}

                get_response = await client.get(
                    f"/api/v1/chatbots/{chatbot_id}",
                    headers=headers,
                )
                assert get_response.status_code == 200

                update_response = await client.put(
                    f"/api/v1/chatbots/{chatbot_id}",
                    headers=headers,
                    json={
                        "name": "Dashboard financiero actualizado",
                        "description": None,
                        "behavior_instructions": "Explica los indicadores.",
                        "configured_llm_model_id": str(second_model_id),
                    },
                )
                assert update_response.status_code == 200
                updated = update_response.json()
                assert updated["id"] == chatbot_id
                assert updated["name"] == "Dashboard financiero actualizado"
                assert updated["configured_llm_model"]["id"] == str(second_model_id)

                invalid_model_response = await client.put(
                    f"/api/v1/chatbots/{chatbot_id}",
                    headers=headers,
                    json={
                        "name": "Dashboard financiero actualizado",
                        "description": None,
                        "behavior_instructions": "Explica los indicadores.",
                        "configured_llm_model_id": str(uuid4()),
                    },
                )
                assert invalid_model_response.status_code == 422

                delete_response = await client.delete(
                    f"/api/v1/chatbots/{chatbot_id}",
                    headers=headers,
                )
                assert delete_response.status_code == 204
                assert (
                    await client.get(
                        f"/api/v1/chatbots/{chatbot_id}",
                        headers=headers,
                    )
                ).status_code == 404
        finally:
            async with database.session() as session:
                await session.execute(
                    delete(Chatbot).where(Chatbot.created_by == user_id)
                )
                user = await session.get(User, user_id)
                if user is not None:
                    await session.delete(user)
                for model_id in (first_model_id, second_model_id):
                    llm_model = await session.get(LlmModel, model_id)
                    if llm_model is not None:
                        await session.delete(llm_model)
                await session.commit()
