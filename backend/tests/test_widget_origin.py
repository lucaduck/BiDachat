from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_database_session
from app.api.queries import _requests
from app.core.config import Settings
from app.main import create_app
from app.services.conversation_service import ConversationService


@pytest.mark.parametrize(
    "value",
    [
        "*",
        "null",
        "file:///tmp",
        "https://*.test",
        "https://user@site.test",
        "https://site.test/path",
        "https://site.test?x",
        "https://site.test#x",
        "https://site.test:bad",
        "https://site.test\\evil",
    ],
)
def test_invalid_origin_configuration(value):
    with pytest.raises(ValueError):
        Settings(_env_file=None, widget_allowed_origins=value)


def test_configuration_canonicalizes_origins():
    settings = Settings(
        _env_file=None,
        widget_allowed_origins="HTTPS://SITE.TEST:443/, https://site.test, http://localhost:4173",
    )
    assert settings.widget_allowed_origins == "https://site.test,http://localhost:4173"


def test_origin_boundary_blocks_before_database_and_provider(monkeypatch):
    _requests.clear()
    calls = []
    app = create_app(
        Settings(
            _env_file=None,
            database_url=None,
            widget_allowed_origins="https://panel.test,https://dashboard.test",
        )
    )

    async def session():
        calls.append("database")
        yield object()

    async def ask(self, session, **kwargs):
        calls.append("provider")
        return SimpleNamespace(
            id=uuid4(),
            answer="OK",
            response_time_ms=1,
            completed_at=datetime.now(UTC),
            conversation_id=uuid4(),
        )

    app.dependency_overrides[get_database_session] = session
    monkeypatch.setattr(ConversationService, "ask", ask)
    url = f"/api/v1/chatbots/{uuid4()}/queries"
    with TestClient(app) as client:
        for headers in (
            {},
            {"Origin": "null"},
            {"Origin": "https://evil.test"},
            {"Origin": "https://dashboard.test.evil"},
            {"Origin": "https://sub.dashboard.test"},
            {"Origin": "https://dashboard.test/path"},
            {"Origin": "https://dashboard.test, https://evil.test"},
            [("Origin", "https://dashboard.test"), ("Origin", "https://evil.test")],
            {
                "Origin": "https://evil.test",
                "Host": "evil.test",
                "X-Forwarded-Host": "dashboard.test",
                "X-Forwarded-Proto": "https",
            },
        ):
            assert (
                client.post(url, headers=headers, json={"question": "Hola"}).status_code
                == 403
            )
            assert calls == []
        for origin in ("https://panel.test", "https://dashboard.test"):
            response = client.post(
                url, headers={"Origin": origin}, json={"question": "Hola"}
            )
            assert response.status_code == 200
            assert response.headers["access-control-allow-origin"] == origin
        preflight = client.options(
            url,
            headers={
                "Origin": "https://dashboard.test",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        assert preflight.status_code == 200
        denied = client.options(
            url,
            headers={
                "Origin": "https://evil.test",
                "Access-Control-Request-Method": "POST",
            },
        )
        assert denied.status_code == 400
        app.state.settings.widget_allowed_origins = ""
        assert (
            client.post(
                url,
                headers={"Origin": "https://dashboard.test"},
                json={"question": "Hola"},
            ).status_code
            == 403
        )
    assert calls == ["database", "provider", "database", "provider"]
