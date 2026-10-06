import asyncio
import sys
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import delete

from app.core.config import Settings
from app.database.session import Database
from app.models import LoginAttempt
from app.services import login_rate_limit_service as rate_limits
from app.services.login_rate_limit_service import LoginRateLimitService


@pytest.mark.integration
def test_login_limits_are_atomic_persistent_and_expire(monkeypatch):
    settings = Settings()
    if settings.database_url is None:
        pytest.skip("DATABASE_URL is not configured")
    global_key = f"test-global-{uuid4()}"
    monkeypatch.setattr(rate_limits, "GLOBAL_KEY", global_key)
    monkeypatch.setattr(rate_limits, "ACCOUNT_MAX_FAILURES", 2)
    monkeypatch.setattr(rate_limits, "GLOBAL_MAX_FAILURES", 3)
    loop_factory = asyncio.SelectorEventLoop if sys.platform == "win32" else None
    with asyncio.Runner(loop_factory=loop_factory) as runner:
        runner.run(_exercise_limits(settings, global_key))


async def _exercise_limits(settings: Settings, global_key: str) -> None:
    database = Database.from_settings(settings)
    email = f"limit-{uuid4()}@bidachat.test"
    other_email = f"limit-{uuid4()}@bidachat.test"
    now = datetime.now(UTC)
    limiter = LoginRateLimitService()

    async def fail_attempt(account: str, timestamp: datetime) -> bool:
        async with database.session() as session:
            attempts = await LoginRateLimitService().check(session, account, timestamp)
            if isinstance(attempts, int):
                await session.rollback()
                return False
            limiter.record_failure(attempts)
            await session.commit()
            return True

    try:
        admitted = await asyncio.gather(*(fail_attempt(email, now) for _ in range(5)))
        assert sum(admitted) == 2
        async with database.session() as session:
            retry = await LoginRateLimitService().check(
                session, f"  {email.upper()}  ", now
            )
            assert retry == 900
        assert await fail_attempt(other_email, now)
        async with database.session() as session:
            assert await limiter.check(session, f"new-{uuid4()}@test", now) == 60

        later = now + timedelta(minutes=1, seconds=1)
        async with database.session() as session:
            assert isinstance(await limiter.check(session, email, later), int)
        async with database.session() as session:
            attempts = await limiter.check(session, other_email, later)
            assert not isinstance(attempts, int)
            await limiter.clear_account(session, attempts)
            await session.commit()

        expired = now + timedelta(minutes=15, seconds=1)
        assert await fail_attempt(email, expired)
    finally:
        async with database.session() as session:
            await session.execute(
                delete(LoginAttempt).where(
                    LoginAttempt.key.in_(
                        [
                            global_key,
                            limiter._account_key(email),
                            limiter._account_key(other_email),
                        ]
                    )
                )
            )
            await session.commit()
        await database.dispose()
