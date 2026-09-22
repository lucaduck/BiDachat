import asyncio
import sys
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import func, select

from app.core.config import Settings
from app.database.session import Database
from app.models import Chatbot, Document, LlmModel, Query, User
from app.services.chatbot_deletion_service import ChatbotDeletionService
from app.services.document_service import (
    ChatbotDocumentNotFoundError,
    DocumentService,
    UploadDocument,
)
from app.services.query_service import ChatbotQueryNotFoundError, QueryService


@pytest.mark.integration
def test_chatbot_deletion_cascades_after_commit_and_preserves_files_on_rollback(
    tmp_path: Path,
):
    settings = Settings(document_storage_path=tmp_path)
    if settings.database_url is None:
        pytest.skip("DATABASE_URL is not configured")

    loop_factory = asyncio.SelectorEventLoop if sys.platform == "win32" else None
    with asyncio.Runner(loop_factory=loop_factory) as runner:
        runner.run(_exercise_chatbot_deletion(settings, tmp_path))


async def _exercise_chatbot_deletion(settings: Settings, storage_path: Path) -> None:
    database = Database.from_settings(settings)
    deletion_service = ChatbotDeletionService(settings)
    user_id = uuid4()
    model_id = uuid4()
    chatbot_id = uuid4()
    document_id = uuid4()
    storage_key = f"documents/{document_id}.txt"
    stored_file = storage_path / f"{document_id}.txt"

    try:
        storage_path.mkdir(parents=True, exist_ok=True)
        stored_file.write_bytes(b"private document")
        async with database.session() as session:
            session.add_all(
                [
                    User(
                        id=user_id,
                        email=f"deletion-{user_id}@bidachat.test",
                        password_hash="integration-hash",
                    ),
                    LlmModel(
                        id=model_id,
                        provider="test-provider",
                        model=f"deletion-model-{model_id}",
                    ),
                ]
            )
            await session.flush()
            session.add(
                Chatbot(
                    id=chatbot_id,
                    created_by=user_id,
                    configured_llm_model_id=model_id,
                    name="Chatbot para borrar",
                )
            )
            session.add(
                Document(
                    id=document_id,
                    chatbot_id=chatbot_id,
                    original_filename="private.txt",
                    storage_key=storage_key,
                    media_type="text/plain",
                    size_bytes=16,
                )
            )
            session.add(
                Query(
                    chatbot_id=chatbot_id,
                    executed_llm_model_id=model_id,
                    question="Consulta que se elimina",
                )
            )
            await session.commit()

        async with database.session() as session:
            deletion = await deletion_service.delete_chatbot(session, chatbot_id)
            await session.rollback()
        assert deletion.storage_keys == (storage_key,)
        assert stored_file.exists()

        async with database.session() as session:
            deletion = await deletion_service.delete_chatbot(session, chatbot_id)
            query_attempt = asyncio.create_task(
                _attempt_query_admission(database, chatbot_id)
            )
            upload_attempt = asyncio.create_task(
                _attempt_document_upload(database, settings, chatbot_id)
            )
            with pytest.raises(TimeoutError):
                await asyncio.wait_for(asyncio.shield(query_attempt), timeout=0.1)
            with pytest.raises(TimeoutError):
                await asyncio.wait_for(asyncio.shield(upload_attempt), timeout=0.1)
            await session.commit()
        assert await query_attempt == "not-found"
        assert await upload_attempt == "not-found"
        deletion_service.clean_private_files(deletion)
        assert not stored_file.exists()

        async with database.session() as session:
            assert await session.get(Chatbot, chatbot_id) is None
            assert (
                await session.scalar(
                    select(func.count(Document.id)).where(
                        Document.chatbot_id == chatbot_id
                    )
                )
                == 0
            )
            assert (
                await session.scalar(
                    select(func.count(Query.id)).where(Query.chatbot_id == chatbot_id)
                )
                == 0
            )
    finally:
        async with database.session() as session:
            user = await session.get(User, user_id)
            if user is not None:
                await session.delete(user)
            model = await session.get(LlmModel, model_id)
            if model is not None:
                await session.delete(model)
            await session.commit()
        stored_file.unlink(missing_ok=True)
        storage_path.rmdir() if storage_path.exists() else None
        await database.dispose()


async def _attempt_query_admission(Database: Database, chatbot_id):
    async with Database.session() as session:
        try:
            await QueryService().start_query(
                session,
                chatbot_id=chatbot_id,
                question="Consulta concurrente",
                has_image=False,
            )
        except ChatbotQueryNotFoundError:
            return "not-found"
    return "admitted"


async def _attempt_document_upload(Database: Database, settings: Settings, chatbot_id):
    async with Database.session() as session:
        try:
            await DocumentService(settings).upload_document(
                session,
                chatbot_id=chatbot_id,
                upload=UploadDocument(
                    filename="concurrent.txt",
                    media_type="text/plain",
                    content=b"concurrent document",
                ),
            )
        except ChatbotDocumentNotFoundError:
            return "not-found"
    return "admitted"
