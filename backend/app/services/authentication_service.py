from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    generate_session_token,
    hash_session_token,
    verify_password,
)
from app.models import AuthSession, User


@dataclass(frozen=True, slots=True)
class IssuedSession:
    token: str
    expires_at: datetime


class AuthenticationService:
    async def login(
        self,
        session: AsyncSession,
        *,
        email: str,
        password: str,
        expires_at: datetime,
        now: datetime | None = None,
    ) -> IssuedSession | None:
        current_time = _get_aware_time(now)
        _require_future_expiration(expires_at, current_time)
        normalized_email = email.strip().lower()
        user = await session.scalar(select(User).where(User.email == normalized_email))

        if user is None or not user.is_active:
            _consume_password_verification(password)
            return None
        if not verify_password(password, user.password_hash):
            return None

        token = generate_session_token()
        session.add(
            AuthSession(
                user_id=user.id,
                token_hash=hash_session_token(token),
                created_at=current_time,
                expires_at=expires_at,
            )
        )
        await session.flush()
        return IssuedSession(token=token, expires_at=expires_at)

    async def authenticate_session(
        self,
        session: AsyncSession,
        token: str,
        *,
        now: datetime | None = None,
    ) -> User | None:
        current_time = _get_aware_time(now)
        statement = (
            select(User)
            .join(AuthSession, AuthSession.user_id == User.id)
            .where(
                AuthSession.token_hash == hash_session_token(token),
                AuthSession.revoked_at.is_(None),
                AuthSession.expires_at > current_time,
                User.is_active.is_(True),
            )
        )
        return await session.scalar(statement)

    async def logout(
        self,
        session: AsyncSession,
        token: str,
        *,
        now: datetime | None = None,
    ) -> bool:
        current_time = _get_aware_time(now)
        auth_session = await session.scalar(
            select(AuthSession)
            .where(
                AuthSession.token_hash == hash_session_token(token),
                AuthSession.revoked_at.is_(None),
            )
            .with_for_update()
        )
        if auth_session is None:
            return False

        auth_session.revoked_at = current_time
        await session.flush()
        return True


def _get_aware_time(value: datetime | None) -> datetime:
    result = value if value is not None else datetime.now(UTC)
    if result.utcoffset() is None:
        raise ValueError("Datetime values must include a timezone")
    return result


def _require_future_expiration(expires_at: datetime, now: datetime) -> None:
    if expires_at.utcoffset() is None:
        raise ValueError("Session expiration must include a timezone")
    if expires_at <= now:
        raise ValueError("Session expiration must be in the future")


def _consume_password_verification(password: str) -> None:
    verify_password(
        password,
        "scrypt$16384$8$1$AAAAAAAAAAAAAAAAAAAAAA==$"
        "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        "AAAAAAAAAAAAAAAAAAAAAA==",
    )
