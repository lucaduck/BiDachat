from fastapi.testclient import TestClient

from app.api.dependencies import get_current_session, get_database_session
from app.core.config import Settings
from app.main import create_app


def test_settings_require_authentication():
    app = create_app(Settings(database_url=None))

    async def fake_database():
        yield object()

    app.dependency_overrides[get_database_session] = fake_database
    with TestClient(app) as client:
        assert client.get("/api/v1/settings").status_code == 401


def test_settings_return_configuration_without_secrets():
    app = create_app(
        Settings(
            database_url=None,
            gemini_api_key="private-gemini-key",
            openai_api_key=" ",
            openrouter_api_key="private-openrouter-key",
            widget_allowed_origins=" https://dashboard.example, ",
        )
    )
    app.dependency_overrides[get_current_session] = lambda: object()
    with TestClient(app) as client:
        response = client.get("/api/v1/settings")
    assert response.status_code == 200
    assert response.json()["gemini_configured"] is True
    assert response.json()["openai_configured"] is False
    assert response.json()["openrouter_configured"] is True
    assert response.json()["widget_allowed_origins"] == ["https://dashboard.example"]
    assert "private-gemini-key" not in response.text
    assert "private-openrouter-key" not in response.text
    assert set(response.json()) == {
        "gemini_configured",
        "openai_configured",
        "openrouter_configured",
        "embedding_provider",
        "embedding_model",
        "embedding_dimensions",
        "document_max_size_bytes",
        "session_ttl_minutes",
        "widget_allowed_origins",
    }
