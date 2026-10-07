import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import Settings
from app.main import create_app


def test_health_and_api_schema():
    with TestClient(create_app(Settings(_env_file=None, app_env="test"))) as client:
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
        schema = client.get("/api/v1/openapi.json").json()
        assert "/api/v1/health" in schema["paths"]
        assert "/api/v1/auth/login" in schema["paths"]
        assert "/api/v1/auth/logout" in schema["paths"]
        assert "/api/v1/chatbots" in schema["paths"]
        assert "/api/v1/chatbots/{chatbot_id}" in schema["paths"]
        assert "/api/v1/chatbots/{chatbot_id}/documents" in schema["paths"]
        assert "/api/v1/llm-models" in schema["paths"]
        assert client.get("/api/v1/docs").status_code == 200


def test_production_disables_docs_and_debug():
    application = create_app(Settings(_env_file=None, app_env="production"))
    assert application.debug is False
    with TestClient(application) as client:
        assert client.get("/api/v1/health").status_code == 200
        assert client.get("/api/v1/docs").status_code == 404
        assert client.get("/api/v1/openapi.json").status_code == 404


def test_environment_overrides_dotenv(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "APP_ENV=development\n"
        "POSTGRES_PASSWORD=private\n"
        "DATABASE_URL=postgresql://user:private@localhost/bidachat\n"
    )
    monkeypatch.setenv("APP_ENV", "production")
    settings = Settings(_env_file=env_file)
    assert settings.app_env == "production"
    assert "POSTGRES_PASSWORD" not in settings.model_dump()
    assert "private" not in str(settings)


def test_invalid_environment_is_rejected(monkeypatch):
    monkeypatch.setenv("APP_ENV", "invalid")
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_internal_error_does_not_expose_details():
    application = create_app(Settings(_env_file=None, app_env="test"))

    @application.get("/failure", include_in_schema=False)
    def fail():
        raise RuntimeError("private connection credentials")

    with TestClient(application, raise_server_exceptions=False) as client:
        response = client.get("/failure")
        assert response.status_code == 500
        assert response.json() == {
            "detail": "Ocurrió un error interno al procesar la solicitud."
        }
        assert "private" not in response.text
