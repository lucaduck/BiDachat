"""Vertex contract: RF-08, RF-12/13, RF-21, RS-04 and RS-09."""

import asyncio
import json

import httpx
import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.llm.provider import LlmProvider, ProviderConfigurationError, ProviderError
from app.models import LlmModel
from app.services.chatbot_service import ChatbotService
from app.services.document_processing_service import DocumentProcessingService

MODEL = "gemini-3.1-flash-lite"
KEY = "sk-" + "test-only-gateway-key-" * 3


def settings(**overrides):
    return Settings(
        _env_file=None,
        **(
            {
                "vertex_enabled": True,
                "vertex_model": MODEL,
                "litellm_master_key": KEY,
            }
            | overrides
        ),
    )


def install_transport(monkeypatch, handler):
    client = httpx.AsyncClient
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kwargs: client(
            transport=httpx.MockTransport(handler),
            **kwargs,
        ),
    )


def ask(config=None, **overrides):
    return asyncio.run(
        LlmProvider(config or settings()).answer(
            **(
                {
                    "provider": "vertex",
                    "model": MODEL,
                    "question": "¿Total?",
                    "instructions": "Responde en español",
                    "context": "Total 42",
                    "page_context": "Dashboard actual",
                    "image": None,
                    "image_mime_type": None,
                }
                | overrides
            )
        )
    )


def result(**overrides):
    return {
        "model": MODEL,
        "choices": [
            {
                "finish_reason": "stop",
                "message": {"content": "Total 42"},
            }
        ],
    } | overrides


@pytest.mark.parametrize("mime", [None, "image/png", "image/jpeg", "image/webp"])
def test_vertex_contract_preserves_context_and_private_auth(monkeypatch, mime):
    def respond(request):
        assert str(request.url) == "http://litellm:4000/v1/chat/completions"
        assert request.headers["authorization"] == f"Bearer {KEY}"
        payload = json.loads(request.content)
        assert payload["model"] == f"vertex/{MODEL}"
        assert payload["stream"] is False
        assert "untrusted evidence" in payload["messages"][0]["content"]
        parts = payload["messages"][1]["content"]
        if mime:
            prompt = parts[0]["text"]
            assert parts[1]["image_url"]["url"] == f"data:{mime};base64,aW1hZ2U="
        else:
            prompt = parts
        assert "Total 42" in prompt
        assert "Dashboard actual" in prompt
        assert "Patricio" in prompt
        assert KEY not in request.content.decode()
        return httpx.Response(200, json=result())

    install_transport(monkeypatch, respond)
    assert (
        ask(
            image=b"image" if mime else None,
            image_mime_type=mime,
            conversation_history=[("user", "Me llamo Patricio")],
        )
        == "Total 42"
    )


def test_multiple_vertex_models_are_explicitly_available():
    second = "gemini-3.1-pro-preview"
    config = settings(vertex_models=f"{MODEL},{second}")
    assert config.configured_vertex_models == (MODEL, second)
    assert config.vertex_model_available(MODEL)
    assert config.vertex_model_available(second)
    assert not config.vertex_model_available("gemini-unconfigured")


@pytest.mark.parametrize("status", [401, 403, 429, 503])
def test_vertex_failure_does_not_retry_or_expose_body(monkeypatch, status):
    calls = []

    def respond(request):
        calls.append(request)
        return httpx.Response(status, text="private provider detail " + KEY)

    install_transport(monkeypatch, respond)
    with pytest.raises(ProviderError) as error:
        ask()
    assert KEY not in str(error.value)
    assert "private provider detail" not in str(error.value)
    assert len(calls) == 1


@pytest.mark.parametrize(
    "response",
    [
        {},
        [],
        result(model="unexpected-model"),
        result(choices=[]),
        result(
            choices=[{"finish_reason": "content_filter", "message": {"content": "x"}}]
        ),
        result(
            choices=[{"finish_reason": "length", "message": {"content": "partial"}}]
        ),
        result(choices=[{"finish_reason": "stop", "message": {"content": " "}}]),
        result(choices=[{"finish_reason": "stop", "message": {"content": None}}]),
    ],
)
def test_invalid_or_incomplete_result_is_not_success(monkeypatch, response):
    install_transport(monkeypatch, lambda _: httpx.Response(200, json=response))
    with pytest.raises(ProviderError, match="Invalid or incomplete gateway"):
        ask()


def test_timeout_is_safe(monkeypatch):
    def respond(request):
        raise httpx.ReadTimeout(KEY, request=request)

    install_transport(monkeypatch, respond)
    with pytest.raises(ProviderError, match="gateway request timed out"):
        ask()


def test_disabled_or_removed_model_never_calls_network(monkeypatch):
    install_transport(monkeypatch, lambda _: pytest.fail("Unexpected request"))
    with pytest.raises(ProviderConfigurationError):
        ask(Settings(_env_file=None, vertex_enabled=False))
    with pytest.raises(ProviderConfigurationError):
        ask(model="gemini-retired")
    service = ChatbotService(settings())
    assert service.model_available(LlmModel(provider="vertex", model=MODEL))
    assert not service.model_available(LlmModel(provider="vertex", model="retired"))
    assert service.model_available(LlmModel(provider="ollama", model="existing"))


def test_vertex_configuration_fails_early_and_redacts_key():
    assert KEY not in repr(settings())
    for overrides in (
        {"vertex_model": ""},
        {"litellm_master_key": "short"},
        {"litellm_base_url": "http://user:password@host"},
        {"vision_provider": "vertex", "vision_model": "other"},
    ):
        with pytest.raises(ValidationError):
            settings(**overrides)


@pytest.mark.parametrize("mime", ["image/png", "image/jpeg", "image/webp"])
def test_source_image_uses_explicit_vertex_profile(monkeypatch, tmp_path, mime):
    install_transport(monkeypatch, lambda _: httpx.Response(200, json=result()))
    path = tmp_path / "source"
    path.write_bytes(b"image")
    processor = DocumentProcessingService(
        settings(vision_provider="vertex", vision_model=MODEL)
    )
    assert asyncio.run(processor._extract_content(path, mime)) == "Total 42"
