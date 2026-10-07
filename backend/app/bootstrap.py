import asyncio
import os
from uuid import uuid4

from sqlalchemy import select

from app.core.config import get_settings
from app.core.security import hash_password
from app.database.session import Database
from app.llm.provider import LlmProvider
from app.models import LlmModel, User


async def bootstrap() -> None:
    settings = get_settings()
    if settings.database_url is None:
        raise RuntimeError("DATABASE_URL is required")
    database = Database.from_settings(settings)
    try:
        async with database.session() as session:
            models = []
            if os.getenv("GEMINI_API_KEY", "").strip():
                models.append(("gemini", os.getenv("GEMINI_MODEL", "gemini-2.5-flash")))
            ollama_model = os.getenv("OLLAMA_MODEL", "").strip()
            if ollama_model:
                await LlmProvider(settings).validate_ollama_model(
                    ollama_model, has_image=False
                )
                models.append(("ollama", ollama_model))
            if (
                settings.openai_api_key is not None
                and settings.openai_api_key.get_secret_value().strip()
            ):
                openai_model = settings.openai_model.strip()
                if not openai_model:
                    raise RuntimeError("Configure OPENAI_MODEL with OPENAI_API_KEY")
                models.append(("openai", openai_model))
            if (
                settings.openrouter_api_key is not None
                and settings.openrouter_api_key.get_secret_value().strip()
            ):
                openrouter_model = settings.openrouter_model.strip()
                if not openrouter_model:
                    raise RuntimeError(
                        "Configure OPENROUTER_MODEL with OPENROUTER_API_KEY"
                    )
                models.append(("openrouter", openrouter_model))
            if (
                not models
                and await session.scalar(select(LlmModel.id).limit(1)) is None
            ):
                raise RuntimeError(
                    "Configure GEMINI_API_KEY, OLLAMA_MODEL, or "
                    "OPENAI_API_KEY with OPENAI_MODEL, or OPENROUTER_API_KEY "
                    "with OPENROUTER_MODEL"
                )
            for provider, model in models:
                existing = await session.scalar(
                    select(LlmModel).where(
                        LlmModel.provider == provider, LlmModel.model == model
                    )
                )
                if existing is None:
                    session.add(LlmModel(id=uuid4(), provider=provider, model=model))
            email = os.getenv("ADMIN_EMAIL", "").strip().lower()
            password = os.getenv("ADMIN_PASSWORD", "")
            if (not email or not password) and await session.scalar(
                select(User.id).limit(1)
            ) is None:
                raise RuntimeError("Configure ADMIN_EMAIL and ADMIN_PASSWORD")
            if email and password:
                existing_user = await session.scalar(
                    select(User).where(User.email == email)
                )
                if existing_user is None:
                    session.add(
                        User(
                            id=uuid4(),
                            email=email,
                            password_hash=hash_password(password),
                        )
                    )
            await session.commit()
    finally:
        await database.dispose()


if __name__ == "__main__":
    asyncio.run(bootstrap())
