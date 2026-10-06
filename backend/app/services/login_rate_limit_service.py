import hashlib
from datetime import UTC, datetime, timedelta
from math import ceil

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import LoginAttempt

GLOBAL_KEY = "global"
GLOBAL_MAX_FAILURES = 60
GLOBAL_WINDOW = timedelta(minutes=1)
ACCOUNT_MAX_FAILURES = 5
ACCOUNT_WINDOW = timedelta(minutes=15)


class LoginRateLimitService:
    async def check(
        self, session: AsyncSession, email: str, now: datetime | None = None
    ) -> tuple[LoginAttempt, LoginAttempt] | int:
        current_time = now or datetime.now(UTC)
        global_attempt = await self._lock_attempt(session, GLOBAL_KEY, current_time)
        global_retry = self._retry_after(
            global_attempt, GLOBAL_MAX_FAILURES, GLOBAL_WINDOW, current_time
        )
        if global_retry:
            return global_retry

        await session.execute(
            delete(LoginAttempt).where(
                LoginAttempt.key.like("account:%"),
                LoginAttempt.window_started_at < current_time - ACCOUNT_WINDOW,
            )
        )
        account_attempt = await self._lock_attempt(
            session, self._account_key(email), current_time
        )
        account_retry = self._retry_after(
            account_attempt, ACCOUNT_MAX_FAILURES, ACCOUNT_WINDOW, current_time
        )
        if account_retry:
            return account_retry
        return global_attempt, account_attempt

    @staticmethod
    def record_failure(attempts: tuple[LoginAttempt, LoginAttempt]) -> None:
        for attempt in attempts:
            attempt.failed_attempts += 1

    @staticmethod
    async def clear_account(
        session: AsyncSession, attempts: tuple[LoginAttempt, LoginAttempt]
    ) -> None:
        await session.delete(attempts[1])

    @staticmethod
    async def _lock_attempt(
        session: AsyncSession, key: str, now: datetime
    ) -> LoginAttempt:
        await session.execute(
            insert(LoginAttempt)
            .values(key=key, failed_attempts=0, window_started_at=now)
            .on_conflict_do_nothing(index_elements=[LoginAttempt.key])
        )
        attempt = await session.scalar(
            select(LoginAttempt).where(LoginAttempt.key == key).with_for_update()
        )
        if attempt is None:
            raise RuntimeError("Login attempt counter could not be locked")
        return attempt

    @staticmethod
    def _retry_after(
        attempt: LoginAttempt, limit: int, window: timedelta, now: datetime
    ) -> int:
        expires_at = attempt.window_started_at + window
        if expires_at <= now:
            attempt.failed_attempts = 0
            attempt.window_started_at = now
            return 0
        if attempt.failed_attempts >= limit:
            return max(1, ceil((expires_at - now).total_seconds()))
        return 0

    @staticmethod
    def _account_key(email: str) -> str:
        normalized_email = email.strip().lower()
        return "account:" + hashlib.sha256(normalized_email.encode("utf-8")).hexdigest()
