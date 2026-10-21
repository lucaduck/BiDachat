import base64
import hmac
import importlib.util
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_database_session
from app.api.queries import _requests
from app.core.config import Settings
from app.main import create_app
from app.services.conversation_service import ConversationService
from app.services.widget_identity_service import (
    InvalidWidgetIdentityError,
    scoped_signing_key,
    verify_widget_identity,
)


def make_token(key: bytes, subject: str, expiry: int) -> str:
    message = f"v1.{subject}.{expiry}"
    signature = base64.urlsafe_b64encode(hmac.digest(key, message.encode(), "sha256"))
    return f"{message}.{signature.rstrip(b'=').decode()}"


def test_signed_identity_is_scoped_and_expires():
    settings = Settings(
        _env_file=None,
        widget_identity_master_key="x" * 48,
        widget_allowed_origins="https://dashboard.example",
    )
    bot = uuid4()
    origin = "https://dashboard.example"
    subject = "a" * 64
    key = scoped_signing_key(settings, bot, origin)
    token = make_token(key, subject, 1_800_000_300)
    identity = verify_widget_identity(
        settings, chatbot_id=bot, origin=origin, token=token, now=1_800_000_000
    )
    assert len(identity) == 64
    assert identity != subject
    assert identity == verify_widget_identity(
        settings,
        chatbot_id=bot,
        origin=origin,
        token=make_token(key, subject, 1_800_000_400),
        now=1_800_000_000,
    )
    for other_bot, other_origin, other_token, now in (
        (uuid4(), origin, token, 1_800_000_000),
        (bot, "https://other.example", token, 1_800_000_000),
        (bot, None, token, 1_800_000_000),
        (bot, origin, token[:-1] + ("A" if token[-1] != "A" else "B"), 1_800_000_000),
        (bot, origin, token, 1_800_000_300),
        (bot, origin, token, 1_799_999_000),
    ):
        with pytest.raises(InvalidWidgetIdentityError):
            verify_widget_identity(
                settings,
                chatbot_id=other_bot,
                origin=other_origin,
                token=other_token,
                now=now,
            )
    with pytest.raises(InvalidWidgetIdentityError):
        verify_widget_identity(
            Settings(_env_file=None),
            chatbot_id=bot,
            origin=origin,
            token=token,
            now=1_800_000_000,
        )


def test_host_example_issues_compatible_pseudonymous_tokens():
    example = (
        Path(__file__).resolve().parents[2] / "docs/examples/sign_widget_identity.py"
    )
    spec = importlib.util.spec_from_file_location("widget_host_example", example)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    settings = Settings(
        _env_file=None,
        widget_identity_master_key="x" * 48,
        widget_allowed_origins="https://dashboard.example",
    )
    bot = uuid4()
    origin = "https://dashboard.example"
    key = scoped_signing_key(settings, bot, origin)
    encoded = base64.urlsafe_b64encode(key).rstrip(b"=").decode()
    token = module.issue_widget_identity(
        signing_key=encoded,
        pseudonym_key=b"y" * 32,
        account_id="user@example.test",
        now=1_800_000_000,
    )
    assert "user@example.test" not in token
    assert verify_widget_identity(
        settings, chatbot_id=bot, origin=origin, token=token, now=1_800_000_001
    )


def test_invalid_identity_fails_before_query_and_valid_identity_reaches_service(
    monkeypatch,
):
    _requests.clear()
    settings = Settings(
        _env_file=None,
        widget_identity_master_key="x" * 48,
        widget_allowed_origins="https://dashboard.example",
    )
    app = create_app(settings)
    bot = uuid4()
    origin = "https://dashboard.example"
    calls = []

    async def fake_session():
        yield object()

    async def fake_ask(self, session, **kwargs):
        calls.append(kwargs)
        return SimpleNamespace(
            id=uuid4(),
            answer="OK",
            response_time_ms=1,
            completed_at=datetime.now(UTC),
            conversation_id=uuid4(),
        )

    app.dependency_overrides[get_database_session] = fake_session
    monkeypatch.setattr(ConversationService, "ask", fake_ask)
    key = scoped_signing_key(settings, bot, origin)
    expiry = int(datetime.now(UTC).timestamp()) + 300
    token = make_token(key, "b" * 64, expiry)
    with TestClient(app) as client:
        url = f"/api/v1/chatbots/{bot}/queries"
        invalid = client.post(
            url,
            headers={"Origin": origin},
            json={"question": "Hola", "identity_token": "invalid"},
        )
        assert invalid.status_code == 401
        assert calls == []
        valid = client.post(
            url,
            headers={"Origin": origin},
            json={"question": "Hola", "identity_token": token},
        )
        assert valid.status_code == 200
    assert len(calls[0]["identity_hash"]) == 64
    assert "b" * 64 not in str(calls)
