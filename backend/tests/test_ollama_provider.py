"""Local inference and embeddings: RF-08, RF-12, RF-14–17, RF-21, RS-04."""

import asyncio
import base64
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import httpx
import pytest

from app.core.config import Settings
from app.llm.provider import LlmProvider, ProviderConfigurationError, ProviderError
from app.services.conversation_service import ConversationService


def install_transport(monkeypatch, handler):
    original = httpx.AsyncClient
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kw: original(transport=httpx.MockTransport(handler), **kw),
    )


def local_settings(**overrides):
    return Settings(
        _env_file=None,
        embedding_provider="ollama",
        embedding_model="embeddinggemma:300m",
        **overrides,
    )


def test_local_embeddings_without_gemini(monkeypatch):
    calls = []

    def handler(request):
        assert request.url.path == "/api/embed"
        assert "x-goog-api-key" not in request.headers
        payload = json.loads(request.content)
        calls.append(payload)
        assert payload["dimensions"] == 768
        assert payload["keep_alive"] == 0
        assert payload["truncate"] is False
        return httpx.Response(200, json={"embeddings": [[0.1] * 768]})

    install_transport(monkeypatch, handler)
    provider = LlmProvider(local_settings())
    for task in ("RETRIEVAL_QUERY", "RETRIEVAL_DOCUMENT"):
        assert len(asyncio.run(provider.embed("Ventas", task_type=task))) == 768
    assert calls[0]["input"].startswith("task: question answering | query:")
    assert calls[1]["input"].startswith("title: none | text:")


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"embeddings": []},
        {"embeddings": [[1]]},
        {"embeddings": [[0] * 768]},
        {"embeddings": [["nan"] * 768]},
    ],
)
def test_invalid_vectors_rejected(body, monkeypatch):
    install_transport(monkeypatch, lambda r: httpx.Response(200, json=body))
    with pytest.raises(ProviderError, match="Invalid embedding"):
        asyncio.run(
            LlmProvider(local_settings()).embed("x", task_type="RETRIEVAL_QUERY")
        )


def test_vision_request_and_memory_limits(monkeypatch):
    def handler(request):
        payload = json.loads(request.content)
        if request.url.path == "/api/show":
            return httpx.Response(200, json={"capabilities": ["completion", "vision"]})
        assert request.url.path == "/api/chat"
        assert payload["messages"][-1]["images"] == [
            base64.b64encode(b"image").decode()
        ]
        assert payload["options"]["num_ctx"] == 2048
        assert payload["keep_alive"] == 0
        assert payload["stream"] is False
        assert payload["think"] is False
        return httpx.Response(200, json={"message": {"content": "Total: 42"}})

    install_transport(monkeypatch, handler)
    answer = asyncio.run(
        LlmProvider(local_settings()).answer(
            provider="ollama",
            model="qwen3-vl:2b",
            question="Total?",
            instructions="Spanish",
            context="Total 42",
            image=b"image",
            image_mime_type="image/png",
        )
    )
    assert answer == "Total: 42"


def test_page_context_is_separate_from_documents_in_provider_prompt(monkeypatch):
    def handler(request):
        payload = json.loads(request.content)
        if request.url.path == "/api/show":
            return httpx.Response(200, json={"capabilities": ["completion"]})
        prompt = payload["messages"][-1]["content"]
        assert "Relevant chatbot documents" in prompt
        assert "Document total: 18" in prompt
        assert "Visible page context selected by the host site" in prompt
        assert "Current dashboard total: 42" in prompt
        assert "untrusted data" in prompt
        return httpx.Response(200, json={"message": {"content": "42"}})

    install_transport(monkeypatch, handler)
    answer = asyncio.run(
        LlmProvider(local_settings()).answer(
            provider="ollama",
            model="qwen3-vl:2b",
            question="Current total?",
            instructions="Spanish",
            context="Document total: 18",
            page_context="Current dashboard total: 42",
            image=None,
            image_mime_type=None,
        )
    )
    assert answer == "42"


def test_text_only_model_rejects_image_before_inference(monkeypatch):
    def handler(request):
        assert request.url.path == "/api/show"
        return httpx.Response(200, json={"capabilities": ["completion"]})

    install_transport(monkeypatch, handler)
    with pytest.raises(ProviderConfigurationError):
        asyncio.run(
            LlmProvider(local_settings()).answer(
                provider="ollama",
                model="text-only",
                question="?",
                instructions="",
                context="",
                image=b"image",
                image_mime_type="image/png",
            )
        )


@pytest.mark.parametrize("code", [404, 500])
def test_provider_failure_is_safe(code, monkeypatch):
    install_transport(
        monkeypatch, lambda r: httpx.Response(code, json={"error": "private details"})
    )
    with pytest.raises(ProviderError) as exc:
        asyncio.run(
            LlmProvider(local_settings()).validate_ollama_model(
                "missing", has_image=False
            )
        )
    assert str(exc.value) == "LLM provider request failed"


@pytest.mark.parametrize(
    "url",
    ["file:///tmp/a", "http://u:p@host", "http://host?key=secret", "http://host/api"],
)
def test_invalid_ollama_origin_rejected(url):
    with pytest.raises(ValueError):
        local_settings(ollama_base_url=url)


def test_local_conversation_retrieves_context_without_gemini():
    service = ConversationService(local_settings())
    chatbot_id, model_id, query_id = uuid4(), uuid4(), uuid4()
    service.queries.start_query = AsyncMock(
        return_value=SimpleNamespace(id=query_id, executed_llm_model_id=model_id)
    )
    service.queries.complete_query = AsyncMock(return_value="completed")
    service.queries.fail_query = AsyncMock()
    service.provider.embed = AsyncMock(return_value=[0.1] * 768)
    service.provider.answer = AsyncMock(return_value="Answer")
    service.knowledge.retrieve_chunks = AsyncMock(
        return_value=[SimpleNamespace(content="Private context")]
    )
    session = SimpleNamespace(
        execute=AsyncMock(
            return_value=SimpleNamespace(
                one=lambda: ("Spanish", "ollama", "qwen3-vl:2b")
            )
        ),
        commit=AsyncMock(),
        rollback=AsyncMock(),
    )
    result = asyncio.run(
        service.ask(
            session,
            chatbot_id=chatbot_id,
            question="Question",
            image=None,
            image_mime_type=None,
            page_context="Dashboard total 42",
        )
    )
    assert result == "completed"
    assert (
        service.knowledge.retrieve_chunks.await_args.kwargs["chatbot_id"] == chatbot_id
    )
    assert service.provider.answer.await_args.kwargs["context"] == "Private context"
    assert (
        service.provider.answer.await_args.kwargs["page_context"]
        == "Dashboard total 42"
    )
    assert service.provider.answer.await_args.kwargs["model"] == "qwen3-vl:2b"
    answer_instructions = service.provider.answer.await_args.kwargs["instructions"]
    assert "Spanish" in answer_instructions
    assert "párrafos breves" in answer_instructions
    statement = session.execute.await_args.args[0]
    assert model_id in statement.compile().params.values()
    assert "configured_llm_model_id" not in str(statement)


def test_failed_conversation_records_completion_time():
    service = ConversationService(local_settings())
    chatbot_id, model_id, query_id = uuid4(), uuid4(), uuid4()
    service.queries.start_query = AsyncMock(
        return_value=SimpleNamespace(id=query_id, executed_llm_model_id=model_id)
    )
    service.queries.fail_query = AsyncMock()
    service.provider.embed = AsyncMock(side_effect=ProviderError("unavailable"))
    session = SimpleNamespace(
        execute=AsyncMock(
            return_value=SimpleNamespace(
                one=lambda: ("Spanish", "ollama", "qwen3-vl:2b")
            )
        ),
        commit=AsyncMock(),
        rollback=AsyncMock(),
    )

    with pytest.raises(ProviderError):
        asyncio.run(
            service.ask(
                session,
                chatbot_id=chatbot_id,
                question="Question",
                image=None,
                image_mime_type=None,
            )
        )

    assert service.queries.fail_query.await_args.kwargs["query_id"] == query_id
    assert service.queries.fail_query.await_args.kwargs["completed_at"] is not None


def test_document_embedding_batches_preserve_order(monkeypatch):
    sizes = []

    def handler(request):
        payload = json.loads(request.content)
        sizes.append(len(payload["input"]))
        return httpx.Response(
            200,
            json={
                "embeddings": [
                    [float(text.rsplit(" ", 1)[-1])] * 768 for text in payload["input"]
                ]
            },
        )

    install_transport(monkeypatch, handler)
    vectors = asyncio.run(
        LlmProvider(local_settings()).embed_documents(
            [str(index) for index in range(1, 19)]
        )
    )
    assert sizes == [16, 2]
    assert [vector[0] for vector in vectors] == list(range(1, 19))


def test_connection_error_is_safe(monkeypatch):
    def handler(request):
        raise httpx.ConnectError("private host", request=request)

    install_transport(monkeypatch, handler)
    with pytest.raises(ProviderError, match="LLM provider request failed"):
        asyncio.run(
            LlmProvider(local_settings()).validate_ollama_model(
                "qwen3-vl:2b", has_image=False
            )
        )
