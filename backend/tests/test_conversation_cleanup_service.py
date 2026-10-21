import asyncio
from contextlib import asynccontextmanager

from app.core.config import Settings
from app.services import conversation_cleanup_service


def test_cleanup_runs_immediately_and_retries_after_failure(monkeypatch):
    events = []

    class Session:
        async def commit(self):
            events.append("commit")

    class Database:
        @asynccontextmanager
        async def session(self):
            yield Session()

    class Service:
        def __init__(self, settings):
            pass

        async def cleanup_expired(self, session):
            events.append("cleanup")
            if events.count("cleanup") == 1:
                raise RuntimeError("temporary failure")
            return 1

    async def sleep(seconds):
        events.append(seconds)
        if events.count(60) == 2:
            raise asyncio.CancelledError

    monkeypatch.setattr(
        conversation_cleanup_service, "ConversationMemoryService", Service
    )
    monkeypatch.setattr(conversation_cleanup_service.asyncio, "sleep", sleep)
    try:
        asyncio.run(
            conversation_cleanup_service.run_conversation_cleanup(
                Database(),
                Settings(_env_file=None, conversation_cleanup_interval_minutes=1),
            )
        )
    except asyncio.CancelledError:
        pass
    assert events == ["cleanup", 60, "cleanup", "commit", 60]
