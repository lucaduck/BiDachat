from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.api.dependencies import CurrentSession, get_current_session
from app.schemas.settings import SystemSettingsResponse

router = APIRouter(tags=["settings"])


@router.get("/settings", response_model=SystemSettingsResponse)
def get_system_settings(
    request: Request,
    _: Annotated[CurrentSession, Depends(get_current_session)],
) -> SystemSettingsResponse:
    settings = request.app.state.settings
    return SystemSettingsResponse(
        gemini_configured=bool(
            settings.gemini_api_key
            and settings.gemini_api_key.get_secret_value().strip()
        ),
        openai_configured=bool(
            settings.openai_api_key
            and settings.openai_api_key.get_secret_value().strip()
        ),
        openrouter_configured=bool(
            settings.openrouter_api_key
            and settings.openrouter_api_key.get_secret_value().strip()
        ),
        embedding_provider=settings.embedding_provider,
        embedding_model=settings.embedding_model,
        embedding_dimensions=settings.embedding_dimensions,
        document_max_size_bytes=settings.document_max_size_bytes,
        session_ttl_minutes=settings.session_ttl_minutes,
        widget_allowed_origins=[
            origin.strip()
            for origin in settings.widget_allowed_origins.split(",")
            if origin.strip()
        ],
    )
