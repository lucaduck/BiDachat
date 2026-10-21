import argparse
import base64
from uuid import UUID

from app.core.config import get_settings
from app.services.widget_identity_service import (
    InvalidWidgetIdentityError,
    scoped_signing_key,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Derive a signing key for one chatbot and origin"
    )
    parser.add_argument("chatbot_id", type=UUID)
    parser.add_argument("origin")
    args = parser.parse_args()
    try:
        key = scoped_signing_key(get_settings(), args.chatbot_id, args.origin)
    except InvalidWidgetIdentityError:
        parser.error("Configure the master key and provide a valid HTTP(S) origin")
    print(base64.urlsafe_b64encode(key).rstrip(b"=").decode())


if __name__ == "__main__":
    main()
