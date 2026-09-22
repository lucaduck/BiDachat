import asyncio
import sys
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.core.config import Settings
from app.core.security import hash_password, hash_session_token
from app.database.session import Database
from app.models import AuthSession, User
from app.services.authentication_service import AuthenticationService


@pytest.mark.integration
def test_session_login_revocation_expiration_and_user_deactivation():
    settings = Settings()
    if settings.database_url is None:
        pytest.skip("DATABASE_URL is not configured")

    loop_factory = asyncio.SelectorEventLoop if sys.platform == "win32" else None
    with asyncio.Runner(loop_factory=loop_factory) as runner:
        runner.run(_exercise_session_lifecycle(settings))


async def _exercise_session_lifecycle(settings: Settings) -> None:
    database = Database.from_settings(settings)
    service = AuthenticationService()
    active_user_id = uuid4()
    inactive_user_id = uuid4()
    now = datetime.now(UTC)
    password = "valid integration password"

    try:
        async with database.session() as session:
            session.add_all(
                [
                    User(
                        id=active_user_id,
                        email=f"active-{active_user_id}@bidachat.test",
                        password_hash=hash_password(password),
                    ),
                    User(
                        id=inactive_user_id,
                        email=f"inactive-{inactive_user_id}@bidachat.test",
                        password_hash=hash_password(password),
                        is_active=False,
                    ),
                ]
            )
            await session.commit()

        async with database.session() as session:
            invalid_login = await service.login(
                session,
                email=f"active-{active_user_id}@bidachat.test",
                password="invalid password",
                expires_at=now + timedelta(hours=1),
                now=now,
            )
            inactive_login = await service.login(
                session,
                email=f"inactive-{inactive_user_id}@bidachat.test",
                password=password,
                expires_at=now + timedelta(hours=1),
                now=now,
            )
            assert invalid_login is None
            assert inactive_login is None

            issued_session = await service.login(
                session,
                email=f"active-{active_user_id}@bidachat.test",
                password=password,
                expires_at=now + timedelta(hours=1),
                now=now,
            )
            assert issued_session is not None
            await session.commit()

        async with database.session() as session:
            assert (
                await service.authenticate_session(
                    session,
                    "unknown-session-token",
                    now=now,
                )
                is None
            )
            authenticated_user = await service.authenticate_session(
                session,
                issued_session.token,
                now=now,
            )
            assert authenticated_user is not None
            assert authenticated_user.id == active_user_id

            assert await service.logout(session, issued_session.token, now=now)
            await session.commit()

        async with database.session() as session:
            assert (
                await service.authenticate_session(
                    session,
                    issued_session.token,
                    now=now,
                )
                is None
            )

            expired_token = "expired-integration-session"
            session.add(
                AuthSession(
                    user_id=active_user_id,
                    token_hash=hash_session_token(expired_token),
                    created_at=now - timedelta(hours=2),
                    expires_at=now - timedelta(hours=1),
                )
            )
            second_session = await service.login(
                session,
                email=f"active-{active_user_id}@bidachat.test",
                password=password,
                expires_at=now + timedelta(hours=1),
                now=now,
            )
            assert second_session is not None
            await session.commit()

        async with database.session() as session:
            assert (
                await service.authenticate_session(session, expired_token, now=now)
                is None
            )
            active_user = await session.get(User, active_user_id)
            assert active_user is not None
            active_user.is_active = False
            await session.commit()

        async with database.session() as session:
            assert (
                await service.authenticate_session(
                    session,
                    second_session.token,
                    now=now,
                )
                is None
            )
    finally:
        async with database.session() as session:
            for user_id in (active_user_id, inactive_user_id):
                user = await session.get(User, user_id)
                if user is not None:
                    await session.delete(user)
            await session.commit()
        await database.dispose()
