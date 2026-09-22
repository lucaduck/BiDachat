import asyncio
import sys
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select

from app.core.config import Settings
from app.database.session import Database, normalize_database_url
from app.models import User


def test_database_url_is_normalized_without_exposing_password():
    url = normalize_database_url(
        "postgresql://database_user:private_password@localhost:5433/bidachat"
    )

    assert url.drivername == "postgresql+psycopg"
    assert "private_password" not in str(url)


def test_database_url_rejects_other_database_drivers():
    with pytest.raises(ValueError, match="PostgreSQL"):
        normalize_database_url("sqlite:///bidachat.db")


def test_all_migration_tables_have_models():
    assert set(User.metadata.tables) == {
        "auth_sessions",
        "chatbots",
        "document_chunks",
        "documents",
        "llm_models",
        "queries",
        "users",
    }


@pytest.mark.integration
def test_persistence_and_transaction_rollback():
    settings = Settings()
    if settings.database_url is None:
        pytest.skip("DATABASE_URL is not configured")

    loop_factory = asyncio.SelectorEventLoop if sys.platform == "win32" else None
    with asyncio.Runner(loop_factory=loop_factory) as runner:
        persisted_id, rolled_back_id = runner.run(
            _exercise_persistence_and_rollback(settings)
        )

    assert isinstance(persisted_id, UUID)
    assert isinstance(rolled_back_id, UUID)


async def _exercise_persistence_and_rollback(settings: Settings) -> tuple[UUID, UUID]:
    database = Database.from_settings(settings)
    persisted_id = uuid4()
    rolled_back_id = uuid4()
    persisted_user = User(
        id=persisted_id,
        email=f"integration-persisted-{persisted_id}@bidachat.test",
        password_hash="integration-hash",
    )
    rolled_back_user = User(
        id=rolled_back_id,
        email=f"integration-rolled-back-{rolled_back_id}@bidachat.test",
        password_hash="integration-hash",
    )

    try:
        async with database.session() as session:
            session.add(persisted_user)
            await session.commit()

        async with database.session() as session:
            stored_user = await session.scalar(
                select(User).where(User.id == persisted_user.id)
            )
            assert stored_user is not None
            assert stored_user.email == persisted_user.email

        with pytest.raises(RuntimeError, match="force rollback"):
            async with database.session() as session:
                session.add(rolled_back_user)
                await session.flush()
                raise RuntimeError("force rollback")

        async with database.session() as session:
            missing_user = await session.scalar(
                select(User).where(User.id == rolled_back_user.id)
            )
            assert missing_user is None

        return persisted_user.id, rolled_back_user.id
    finally:
        async with database.session() as session:
            stored_user = await session.get(User, persisted_user.id)
            if stored_user is not None:
                await session.delete(stored_user)
                await session.commit()
        await database.dispose()
