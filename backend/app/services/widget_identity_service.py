import base64
import hashlib
import hmac
import re
import time
from uuid import UUID

from app.core.config import Settings
from app.services.conversation_memory_service import normalize_origin

TOKEN_PATTERN = re.compile(r"^v1\.([0-9a-f]{64})\.([0-9]{10,12})\.([A-Za-z0-9_-]{43})$")
MAX_TOKEN_LIFETIME_SECONDS = 600


class InvalidWidgetIdentityError(Exception):
    pass


def scoped_signing_key(
    settings: Settings, chatbot_id: UUID, origin: str | None
) -> bytes:
    normalized = normalize_origin(origin)
    if settings.widget_identity_master_key is None or normalized == "same-origin":
        raise InvalidWidgetIdentityError
    scope = f"bidachat-widget-identity-v1\n{chatbot_id}\n{normalized}".encode()
    return hmac.digest(
        settings.widget_identity_master_key.get_secret_value().encode(), scope, "sha256"
    )


def verify_widget_identity(
    settings: Settings,
    *,
    chatbot_id: UUID,
    origin: str | None,
    token: str,
    now: int | None = None,
) -> str:
    match = TOKEN_PATTERN.fullmatch(token)
    if match is None:
        raise InvalidWidgetIdentityError
    subject, expiry_text, signature = match.groups()
    current = int(time.time()) if now is None else now
    expiry = int(expiry_text)
    if expiry <= current or expiry > current + MAX_TOKEN_LIFETIME_SECONDS:
        raise InvalidWidgetIdentityError
    key = scoped_signing_key(settings, chatbot_id, origin)
    message = f"v1.{subject}.{expiry_text}".encode()
    expected = base64.urlsafe_b64encode(hmac.digest(key, message, "sha256")).rstrip(
        b"="
    )
    if not hmac.compare_digest(expected.decode(), signature):
        raise InvalidWidgetIdentityError
    return hmac.new(
        key, b"bidachat-identity-hash-v1\n" + subject.encode(), hashlib.sha256
    ).hexdigest()
