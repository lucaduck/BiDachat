import asyncio
import sys
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings
from app.core.security import hash_password
from app.main import create_app
from app.models import User


@pytest.mark.integration
def test_login_and_logout_api_flow():
    settings = Settings(session_ttl_minutes=60)
    if settings.database_url is None:
        pytest.skip("DATABASE_URL is not configured")

    loop_factory = asyncio.SelectorEventLoop if sys.platform == "win32" else None
    with asyncio.Runner(loop_factory=loop_factory) as runner:
        runner.run(_exercise_login_and_logout_api(settings))


async def _exercise_login_and_logout_api(settings: Settings) -> None:
    application = create_app(settings)
    user_id = uuid4()
    email = f"api-auth-{user_id}@bidachat.test"
    password = "valid API integration password"

    async with application.router.lifespan_context(application):
        database = application.state.database
        try:
            async with database.session() as session:
                session.add(
                    User(
                        id=user_id,
                        email=email,
                        password_hash=hash_password(password),
                    )
                )
                await session.commit()

            transport = ASGITransport(app=application)
            async with AsyncClient(
                transport=transport,
                base_url="http://testserver",
            ) as client:
                invalid_response = await client.post(
                    "/api/v1/auth/login",
                    json={"email": email, "password": "invalid"},
                )
                assert invalid_response.status_code == 401

                unauthorized_logout = await client.post("/api/v1/auth/logout")
                assert unauthorized_logout.status_code == 401

                login_response = await client.post(
                    "/api/v1/auth/login",
                    json={"email": email, "password": password},
                )
                assert login_response.status_code == 200
                login_payload = login_response.json()
                assert login_payload["token_type"] == "bearer"
                access_token = login_payload["access_token"]

                logout_response = await client.post(
                    "/api/v1/auth/logout",
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                assert logout_response.status_code == 204

                revoked_response = await client.post(
                    "/api/v1/auth/logout",
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                assert revoked_response.status_code == 401
        finally:
            async with database.session() as session:
                user = await session.get(User, user_id)
                if user is not None:
                    await session.delete(user)
                    await session.commit()
