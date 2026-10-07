from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    CurrentSession,
    get_current_session,
    get_database_session,
)
from app.core.config import Settings
from app.schemas.auth import LoginRequest, SessionResponse
from app.services.authentication_service import AuthenticationService
from app.services.login_rate_limit_service import LoginRateLimitService

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login", response_model=SessionResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> SessionResponse:
    settings: Settings = request.app.state.settings
    now = datetime.now(UTC)
    limiter = LoginRateLimitService()
    attempts = await limiter.check(session, payload.email, now)
    if isinstance(attempts, int):
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiados intentos de inicio de sesión. Inténtalo más tarde.",
            headers={"Retry-After": str(attempts)},
        )
    issued_session = await AuthenticationService().login(
        session,
        email=payload.email,
        password=payload.password,
        expires_at=now + timedelta(minutes=settings.session_ttl_minutes),
        now=now,
    )
    if issued_session is None:
        limiter.record_failure(attempts)
        await session.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Las credenciales no son válidas.",
        )

    await limiter.clear_account(session, attempts)
    await session.commit()
    return SessionResponse(
        access_token=issued_session.token,
        expires_at=issued_session.expires_at,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    current_session: Annotated[CurrentSession, Depends(get_current_session)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> Response:
    revoked = await AuthenticationService().logout(session, current_session.token)
    if not revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No se pudo validar la sesión.",
        )
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
