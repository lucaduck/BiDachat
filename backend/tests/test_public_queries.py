import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_database_session
from app.api.queries import _requests
from app.core.config import Settings
from app.llm.provider import LlmProvider, ProviderConfigurationError
from app.main import create_app
from app.schemas.query import QueryRequest
from app.services.conversation_service import ConversationService
from app.services.document_processing_service import DocumentProcessingService


def test_query_image_validation_rejects_type_mismatch() -> None:
    with pytest.raises(ValueError):
        QueryRequest(
            question="¿Qué muestra el gráfico?",
            image_base64="aGVsbG8=",
            image_mime_type="image/png",
        )


def test_embedding_request_uses_embedding_two_task_prefix(monkeypatch):
    provider = LlmProvider(
        Settings(embedding_provider="gemini", gemini_api_key="test-key")
    )
    captured = []

    async def fake_post(url, payload, headers):
        captured.append(payload)
        return {"embedding": {"values": [1.0] * 768}}

    monkeypatch.setattr(provider, "_post", fake_post)
    asyncio.run(provider.embed("¿Cuál fue el total?", task_type="RETRIEVAL_QUERY"))
    asyncio.run(provider.embed("Total: 10", task_type="RETRIEVAL_DOCUMENT"))
    assert captured[0]["content"]["parts"][0]["text"].startswith(
        "task: question answering | query: "
    )
    assert captured[1]["content"]["parts"][0]["text"].startswith("title: none | text: ")
    assert "taskType" not in captured[0]
    assert captured[0]["output_dimensionality"] == 768


def test_public_query_endpoint_returns_answer_without_admin_token(monkeypatch):
    _requests.clear()
    app = create_app(Settings(database_url=None))
    chatbot_id = uuid4()

    async def fake_session():
        yield object()

    async def fake_ask(self, session, **kwargs):
        assert kwargs["chatbot_id"] == chatbot_id
        assert kwargs["question"] == "Hola"
        return SimpleNamespace(
            id=uuid4(),
            answer="Respuesta de prueba",
            response_time_ms=12,
            completed_at=datetime.now(UTC),
        )

    app.dependency_overrides[get_database_session] = fake_session
    monkeypatch.setattr(ConversationService, "ask", fake_ask)
    with TestClient(app) as client:
        response = client.post(
            f"/api/v1/chatbots/{chatbot_id}/queries", json={"question": "Hola"}
        )
    assert response.status_code == 200
    assert response.json()["answer"] == "Respuesta de prueba"


def test_public_query_endpoint_limits_repeated_requests(monkeypatch):
    _requests.clear()
    app = create_app(Settings(database_url=None))

    async def fake_session():
        yield object()

    async def fake_ask(self, session, **kwargs):
        return SimpleNamespace(
            id=uuid4(), answer="OK", response_time_ms=1, completed_at=datetime.now(UTC)
        )

    app.dependency_overrides[get_database_session] = fake_session
    monkeypatch.setattr(ConversationService, "ask", fake_ask)
    with TestClient(app) as client:
        url = f"/api/v1/chatbots/{uuid4()}/queries"
        for _ in range(10):
            assert client.post(url, json={"question": "Hola"}).status_code == 200
        assert client.post(url, json={"question": "Hola"}).status_code == 429
    _requests.clear()


def test_document_processing_extracts_utf8_text(tmp_path):
    source = tmp_path / "source.txt"
    source.write_text("Información del dashboard", encoding="utf-8")
    assert DocumentProcessingService._extract_text(source, "text/plain") == (
        "Información del dashboard"
    )


def test_image_source_is_described_and_embedded(tmp_path):
    source = tmp_path / "chart.png"
    source.write_bytes(b"\x89PNG\r\n\x1a\nimage")
    service = DocumentProcessingService(
        Settings(document_storage_path=tmp_path, ollama_model="qwen3-vl:2b")
    )
    service.provider.answer = AsyncMock(return_value="Gráfico: ventas, enero 10")
    service.provider.embed_documents = AsyncMock(return_value=[[1.0] * 768])
    service.knowledge.begin_processing = AsyncMock()
    service.knowledge.publish_chunks = AsyncMock(
        return_value=SimpleNamespace(status="ready")
    )
    session = SimpleNamespace(commit=AsyncMock(), rollback=AsyncMock())
    document = SimpleNamespace(
        id=uuid4(), storage_key="chart.png", media_type="image/png"
    )

    result = asyncio.run(
        service.process(session, document=document, chatbot_id=uuid4())
    )

    assert result.status == "ready"
    assert service.provider.answer.await_args.kwargs["image"] == source.read_bytes()
    assert service.provider.embed_documents.await_args.args == (
        ["Gráfico: ventas, enero 10"],
    )
    assert service.knowledge.publish_chunks.await_args.kwargs["chunks"][0].content == (
        "Gráfico: ventas, enero 10"
    )


def test_gemini_key_is_required_for_embeddings():
    provider = LlmProvider(Settings(gemini_api_key=None))
    with pytest.raises(ProviderConfigurationError):
        provider._gemini_key()


def test_document_processing_reports_missing_embedding_key(tmp_path):
    source = tmp_path / "source.txt"
    source.write_text("Conocimiento de prueba", encoding="utf-8")
    service = DocumentProcessingService(
        Settings(
            document_storage_path=tmp_path,
            embedding_provider="gemini",
            gemini_api_key=None,
        )
    )
    service.knowledge.begin_processing = AsyncMock()
    service.knowledge.mark_failed = AsyncMock(
        return_value=SimpleNamespace(status="failed")
    )
    session = SimpleNamespace(commit=AsyncMock(), rollback=AsyncMock())
    document = SimpleNamespace(
        id=uuid4(), storage_key="source.txt", media_type="text/plain"
    )
    chatbot_id = uuid4()

    result = asyncio.run(
        service.process(session, document=document, chatbot_id=chatbot_id)
    )

    assert result.status == "failed"
    assert service.knowledge.mark_failed.await_args.kwargs["error_code"] == (
        "embedding_not_configured"
    )
