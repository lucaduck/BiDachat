from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from pydantic import SecretStr
from sqlalchemy.engine import URL, make_url
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import Settings


def normalize_database_url(database_url: SecretStr | str) -> URL:
    raw_url = (
        database_url.get_secret_value()
        if isinstance(database_url, SecretStr)
        else database_url
    )
    url = make_url(raw_url)
    if url.drivername in {"postgres", "postgresql"}:
        return url.set(drivername="postgresql+psycopg")
    if url.drivername != "postgresql+psycopg":
        raise ValueError("DATABASE_URL must use PostgreSQL with the psycopg driver")
    return url


class Database:
    def __init__(self, database_url: SecretStr | str) -> None:
        self.engine: AsyncEngine = create_async_engine(
            normalize_database_url(database_url),
            connect_args={"connect_timeout": 5},
            pool_pre_ping=True,
        )
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    @classmethod
    def from_settings(cls, settings: Settings) -> "Database":
        if settings.database_url is None:
            raise ValueError("DATABASE_URL is required to configure the database")
        return cls(settings.database_url)

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        async with self.session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

    async def dispose(self) -> None:
        await self.engine.dispose()
