"""Sign a widget identity after the host has authenticated its user.

Keep this module, both keys and the authenticated account identifier on the
host server. Never expose the signing or pseudonym keys to the browser.
"""

import base64
import hashlib
import hmac
import time


def issue_widget_identity(
    *, signing_key: str, pseudonym_key: bytes, account_id: str, now: int | None = None
) -> str:
    if len(pseudonym_key) < 32 or not account_id:
        raise ValueError("A strong pseudonym key and an authenticated account are required")
    key = base64.urlsafe_b64decode(signing_key + "=" * (-len(signing_key) % 4))
    if len(key) != 32:
        raise ValueError("Invalid scoped signing key")
    subject = hmac.new(pseudonym_key, account_id.encode(), hashlib.sha256).hexdigest()
    expiry = (int(time.time()) if now is None else now) + 300
    message = f"v1.{subject}.{expiry}"
    signature = base64.urlsafe_b64encode(hmac.digest(key, message.encode(), "sha256"))
    return f"{message}.{signature.rstrip(b'=').decode()}"
