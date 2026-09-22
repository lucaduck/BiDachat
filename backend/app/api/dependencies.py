from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import Database
from app.models import User
from app.services.authentication_service import AuthenticationService

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True, slots=True)
class CurrentSession:
    user: User
    token: str


def get_database(request: Request) -> Database:
    database = getattr(request.app.state, "database", None)
    if database is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El servicio de base de datos no está configurado.",
        )
    return database


async def get_database_session(
    database: Annotated[Database, Depends(get_database)],
) -> AsyncIterator[AsyncSession]:
    async with database.session() as session:
        yield session


async def get_current_session(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> CurrentSession:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized_error()

    token = credentials.credentials
    user = await AuthenticationService().authenticate_session(session, token)
    if user is None:
        raise _unauthorized_error()
    return CurrentSession(user=user, token=token)


def _unauthorized_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar la sesión.",
        headers={"WWW-Authenticate": "Bearer"},
    )
