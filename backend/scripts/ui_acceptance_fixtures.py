"""Create and clean isolated fixtures for browser acceptance against the local stack."""

import argparse
import asyncio
import json
import secrets
from pathlib import Path
from uuid import UUID, uuid4

from sqlalchemy import delete, select

from app.core.config import get_settings
from app.core.security import hash_password
from app.database.session import Database
from app.models import Chatbot, Document, LlmModel, User


async def run(action: str, user_id: str | None) -> None:
    settings = get_settings()
    database = Database.from_settings(settings)
    try:
        async with database.session() as session:
            if action == "create":
                identifier = uuid4()
                email = f"ui-qa-{identifier}@bidachat.test"
                password = secrets.token_urlsafe(24)
                model = await session.scalar(
                    select(LlmModel).where(
                        LlmModel.provider == "ollama",
                        LlmModel.model == "qwen3-vl:2b-instruct",
                    )
                )
                if model is None:
                    raise ValueError("The local vision model must be registered first")
                session.add(
                    User(
                        id=identifier,
                        email=email,
                        password_hash=hash_password(password),
                    )
                )
                await session.commit()
                print(
                    json.dumps(
                        {
                            "userId": str(identifier),
                            "email": email,
                            "password": password,
                            "modelId": str(model.id),
                            "botIds": [],
                        }
                    )
                )
                return
            if user_id is None:
                raise ValueError("Cleanup requires the exact fixture user identifier")
            identifier = UUID(user_id)
            user = await session.get(User, identifier)
            if user is None:
                return
            if user.email != f"ui-qa-{identifier}@bidachat.test":
                raise ValueError("Cleanup only permits a dedicated acceptance fixture")
            chatbot_ids = select(Chatbot.id).where(Chatbot.created_by == identifier)
            files = list(
                await session.scalars(
                    select(Document.storage_key).where(
                        Document.chatbot_id.in_(chatbot_ids)
                    )
                )
            )
            await session.execute(
                delete(Chatbot).where(Chatbot.created_by == identifier)
            )
            await session.delete(user)
            await session.commit()
            root = Path(settings.document_storage_path).resolve()
            for key in files:
                path = (root / key).resolve()
                if path.is_relative_to(root):
                    path.unlink(missing_ok=True)
            print("Isolated acceptance fixtures cleaned.")
    finally:
        await database.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["create", "cleanup"])
    parser.add_argument("--user-id")
    arguments = parser.parse_args()
    asyncio.run(run(arguments.action, arguments.user_id))
