"""OpenRouter selection and multimodal answers: RF-08, RF-21, RS-04."""

import asyncio
from contextlib import asynccontextmanager
from types import SimpleNamespace

import httpx
import pytest

import app.bootstrap as bootstrap_module
from app.core.config import Settings
from app.llm.provider import LlmProvider, ProviderConfigurationError, ProviderError


def ask(provider, **overrides):
    arguments = {
        "provider": "openrouter",
        "model": "openai/gpt-4.1-mini",
        "question": "What is the total?",
        "instructions": "Answer in Spanish.",
        "context": "Total: 42",
        "image": None,
        "image_mime_type": None,
    }
    return asyncio.run(provider.answer(**(arguments | overrides)))


def install_transport(monkeypatch, handler):
    original_client = httpx.AsyncClient
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kwargs: original_client(
            transport=httpx.MockTransport(handler), **kwargs
        ),
    )


def test_openrouter_sends_private_multimodal_chat_request(monkeypatch):
    import json

    provider = LlmProvider(
        Settings(
            _env_file=None,
            openrouter_api_key="private-test-key",
            openrouter_site_url="https://bidachat.example",
        )
    )

    def respond(request):
        assert str(request.url) == "https://openrouter.ai/api/v1/chat/completions"
        assert request.headers["Authorization"] == "Bearer private-test-key"
        assert request.headers["HTTP-Referer"] == "https://bidachat.example"
        assert request.headers["X-OpenRouter-Title"] == "BIDACHAT"
        payload = json.loads(request.content)
        assert payload["model"] == "openai/gpt-4.1-mini"
        assert payload["temperature"] == 0.2
        assert payload["messages"][0] == {
            "role": "system",
            "content": "Answer in Spanish.",
        }
        content = payload["messages"][1]["content"]
        assert "Total: 42" in content[0]["text"]
        assert content[1] == {
            "type": "image_url",
            "image_url": {"url": "data:image/png;base64,aW1hZ2U="},
        }
        assert "private-test-key" not in request.content.decode()
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "Total: 42"}}]},
        )

    install_transport(monkeypatch, respond)
    assert ask(provider, image=b"image", image_mime_type="image/png") == "Total: 42"


@pytest.mark.parametrize("key", [None, "", "   "])
def test_missing_openrouter_key_fails_before_network(key, monkeypatch):
    provider = LlmProvider(Settings(_env_file=None, openrouter_api_key=key))
    install_transport(monkeypatch, lambda request: pytest.fail("Unexpected request"))
    with pytest.raises(ProviderConfigurationError, match="not configured"):
        ask(provider)


def test_openrouter_invalid_response_is_rejected(monkeypatch):
    provider = LlmProvider(
        Settings(_env_file=None, openrouter_api_key="private-test-key")
    )
    install_transport(monkeypatch, lambda request: httpx.Response(200, json={}))
    with pytest.raises(ProviderError, match="Invalid OpenRouter response"):
        ask(provider)


def test_bootstrap_registers_openrouter_model_for_admin_selector(monkeypatch):
    settings = Settings(
        _env_file=None,
        database_url="postgresql+psycopg://user:password@localhost/test",
        openrouter_api_key="private-test-key",
        openrouter_model="openai/gpt-4.1-mini",
    )
    added = []

    class Session:
        async def scalar(self, statement):
            return None

        def add(self, model):
            added.append(model)

        async def commit(self):
            pass

    @asynccontextmanager
    async def session():
        yield Session()

    async def dispose():
        pass

    database = SimpleNamespace(session=session, dispose=dispose)
    monkeypatch.setattr(bootstrap_module, "get_settings", lambda: settings)
    monkeypatch.setattr(
        bootstrap_module.Database, "from_settings", lambda settings: database
    )
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)
    monkeypatch.setenv("ADMIN_EMAIL", "researcher@example.test")
    monkeypatch.setenv("ADMIN_PASSWORD", "test-admin-password")
    asyncio.run(bootstrap_module.bootstrap())
    assert added[0].provider == "openrouter"
    assert added[0].model == "openai/gpt-4.1-mini"


def test_openrouter_key_is_redacted_from_settings():
    settings = Settings(_env_file=None, openrouter_api_key="private-test-key")
    assert "private-test-key" not in repr(settings)
