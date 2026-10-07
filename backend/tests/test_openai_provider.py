"""OpenAI selection and multimodal answers: RF-08, RF-21, RS-04, CA-UC07-02."""

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
        "provider": "openai",
        "model": "test-vision-model",
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


def test_openai_sends_private_multimodal_request_and_reads_message(monkeypatch):
    import json

    provider = LlmProvider(Settings(_env_file=None, openai_api_key="private-test-key"))

    def respond(request):
        assert str(request.url) == "https://api.openai.com/v1/responses"
        assert request.headers["Authorization"] == "Bearer private-test-key"
        payload = json.loads(request.content)
        assert payload["store"] is False
        assert payload["model"] == "test-vision-model"
        assert payload["instructions"] == "Answer in Spanish."
        content = payload["input"][0]["content"]
        assert "Total: 42" in content[0]["text"]
        assert "What is the total?" in content[0]["text"]
        assert content[1] == {
            "type": "input_image",
            "image_url": "data:image/png;base64,aW1hZ2U=",
        }
        assert "private-test-key" not in request.content.decode()
        return httpx.Response(
            200,
            json={
                "status": "completed",
                "output": [
                    {"type": "reasoning", "summary": []},
                    {
                        "type": "message",
                        "content": [
                            {"type": "output_text", "text": "Total: "},
                            {"type": "output_text", "text": "42"},
                        ],
                    },
                ],
            },
        )

    install_transport(monkeypatch, respond)
    assert ask(provider, image=b"image", image_mime_type="image/png") == "Total: 42"


@pytest.mark.parametrize("key", [None, "", "   "])
def test_missing_openai_key_fails_before_network(key, monkeypatch):
    provider = LlmProvider(Settings(_env_file=None, openai_api_key=key))

    def unexpected_request(request):
        pytest.fail("A missing key must not send a request")

    install_transport(monkeypatch, unexpected_request)
    with pytest.raises(ProviderConfigurationError, match="not configured"):
        ask(provider)


@pytest.mark.parametrize(
    "body",
    [
        {"status": "incomplete", "output": []},
        {"status": "completed", "output": []},
        {"status": "completed", "output": None},
        {"status": "completed", "output": [{"type": "message", "content": None}]},
        {
            "status": "completed",
            "output": [
                {"type": "message", "content": [{"type": "refusal", "refusal": "No"}]}
            ],
        },
    ],
)
def test_openai_invalid_or_incomplete_output_is_rejected(body, monkeypatch):
    provider = LlmProvider(Settings(_env_file=None, openai_api_key="private-test-key"))
    install_transport(monkeypatch, lambda request: httpx.Response(200, json=body))
    with pytest.raises(ProviderError, match="Invalid OpenAI response"):
        ask(provider)


def test_openai_http_failure_does_not_expose_provider_details(monkeypatch):
    provider = LlmProvider(Settings(_env_file=None, openai_api_key="private-test-key"))
    install_transport(
        monkeypatch,
        lambda request: httpx.Response(
            401, json={"error": {"message": "private-provider-details"}}
        ),
    )
    with pytest.raises(ProviderError) as caught:
        ask(provider)
    assert str(caught.value) == "LLM provider request failed"


def test_bootstrap_registers_openai_model_for_admin_selector(monkeypatch):
    settings = Settings(
        _env_file=None,
        database_url="postgresql+psycopg://user:password@localhost/test",
        openai_api_key="private-test-key",
        openai_model="test-vision-model",
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
    assert added[0].provider == "openai"
    assert added[0].model == "test-vision-model"
    assert added[1].email == "researcher@example.test"


def test_openai_key_is_redacted_from_settings():
    settings = Settings(_env_file=None, openai_api_key="private-test-key")
    assert "private-test-key" not in repr(settings)
