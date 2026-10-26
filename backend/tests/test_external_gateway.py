"""Contract tests for centralized external AI generation."""

import asyncio
import json

import httpx
import pytest

from app.core.config import Settings
from app.llm.errors import ProviderConfigurationError, ProviderError
from app.llm.external_gateway import ExternalGateway

KEY = "sk-" + "gateway-test-key-" * 3


def settings(**overrides):
    values = {
        "external_ai_gateway_providers": "openai,gemini,openrouter",
        "litellm_master_key": KEY,
        "openai_model": "gpt-test",
        "gemini_model": "gemini-test",
        "openrouter_model": "openai/gpt-test",
    } | overrides
    return Settings(
        _env_file=None,
        **values,
    )


def install_transport(monkeypatch, handler):
    client = httpx.AsyncClient
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kwargs: client(transport=httpx.MockTransport(handler), **kwargs),
    )


def ask(config, provider, model, **overrides):
    return asyncio.run(
        ExternalGateway(config).answer(
            **(
                {
                    "provider": provider,
                    "model": model,
                    "prompt": "Total 42",
                    "instructions": "Answer in Spanish.",
                    "image": None,
                    "image_mime_type": None,
                }
                | overrides
            )
        )
    )


def test_openai_responses_preserves_store_false_and_gateway_auth(monkeypatch):
    def respond(request):
        assert str(request.url) == "http://litellm:4000/v1/responses"
        assert request.headers["authorization"] == f"Bearer {KEY}"
        payload = json.loads(request.content)
        assert payload["model"] == "openai/gpt-test"
        assert payload["store"] is False
        assert payload["instructions"] == "Answer in Spanish."
        assert KEY not in request.content.decode()
        return httpx.Response(
            200,
            json={
                "model": "openai/gpt-test",
                "status": "completed",
                "output": [
                    {
                        "type": "message",
                        "content": [{"type": "output_text", "text": "42"}],
                    }
                ],
            },
        )

    install_transport(monkeypatch, respond)
    assert ask(settings(), "openai", "gpt-test") == "42"


@pytest.mark.parametrize(
    ("provider", "model", "gateway_model"),
    [
        ("gemini", "gemini-test", "gemini/gemini-test"),
        ("openrouter", "openai/gpt-test", "openrouter/openai/gpt-test"),
    ],
)
def test_chat_providers_use_private_gateway(
    monkeypatch, provider, model, gateway_model
):
    def respond(request):
        assert str(request.url) == "http://litellm:4000/v1/chat/completions"
        payload = json.loads(request.content)
        assert payload["model"] == gateway_model
        assert payload["messages"][0]["role"] == "system"
        return httpx.Response(
            200,
            json={
                "model": gateway_model,
                "choices": [{"finish_reason": "stop", "message": {"content": "42"}}],
            },
        )

    install_transport(monkeypatch, respond)
    assert ask(settings(), provider, model) == "42"


def test_gateway_rejects_unconfigured_model_before_network(monkeypatch):
    install_transport(monkeypatch, lambda _: pytest.fail("Unexpected network call"))
    with pytest.raises(ProviderConfigurationError):
        ask(settings(), "openai", "not-approved")


@pytest.mark.parametrize(
    "overrides",
    [
        {"litellm_master_key": "short"},
        {"openrouter_model": ""},
        {"external_ai_gateway_providers": "openai,unsupported"},
    ],
)
def test_gateway_configuration_rejects_incomplete_or_unknown_provider(overrides):
    with pytest.raises(ValueError):
        settings(**overrides)


@pytest.mark.parametrize("status", [401, 403, 429, 503])
def test_gateway_error_is_safe_and_not_retried(monkeypatch, status):
    calls = []

    def respond(request):
        calls.append(request)
        return httpx.Response(status, text="provider secret " + KEY)

    install_transport(monkeypatch, respond)
    with pytest.raises(ProviderError) as error:
        ask(settings(), "gemini", "gemini-test")
    assert KEY not in str(error.value)
    assert "provider secret" not in str(error.value)
    assert len(calls) == 1


def test_vision_payload_and_incomplete_response_are_rejected(monkeypatch):
    def respond(request):
        payload = json.loads(request.content)
        assert payload["messages"][1]["content"][1] == {
            "type": "image_url",
            "image_url": {"url": "data:image/png;base64,aW1hZ2U="},
        }
        return httpx.Response(
            200,
            json={
                "model": "gemini/gemini-test",
                "choices": [
                    {
                        "finish_reason": "length",
                        "message": {"content": "partial"},
                    }
                ],
            },
        )

    install_transport(monkeypatch, respond)
    with pytest.raises(ProviderError, match="Invalid or incomplete"):
        ask(
            settings(),
            "gemini",
            "gemini-test",
            image=b"image",
            image_mime_type="image/png",
        )
