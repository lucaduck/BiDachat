from collections import defaultdict, deque
from time import monotonic
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_database_session
from app.llm.provider import ProviderError
from app.schemas.query import QueryRequest, QueryResponse
from app.services.conversation_service import ConversationService
from app.services.query_service import ChatbotQueryNotFoundError
from app.services.widget_identity_service import (
    InvalidWidgetIdentityError,
    verify_widget_identity,
)

router = APIRouter(tags=["queries"])
_requests: dict[str, deque[float]] = defaultdict(deque)


def require_widget_origin(request: Request) -> str:
    origins = request.headers.getlist("origin")
    allowed = request.app.state.settings.widget_allowed_origins.split(",")
    if len(origins) != 1 or not origins[0] or origins[0] not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Este origen no está autorizado para consultar el chatbot.",
        )
    return origins[0]


def _check_query_limit(client: str) -> None:
    now = monotonic()
    recent = _requests[client]
    while recent and now - recent[0] > 60:
        recent.popleft()
    if len(recent) >= 10:
        raise HTTPException(
            status_code=429,
            detail="Demasiadas consultas. Inténtalo en un minuto.",
            headers={"Retry-After": "60"},
        )
    recent.append(now)


@router.post("/chatbots/{chatbot_id}/queries", response_model=QueryResponse)
async def create_query(
    chatbot_id: UUID,
    payload: QueryRequest,
    request: Request,
    origin: Annotated[str, Depends(require_widget_origin)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> QueryResponse:
    _check_query_limit(request.client.host if request.client else "unknown")
    try:
        identity_hash = (
            verify_widget_identity(
                request.app.state.settings,
                chatbot_id=chatbot_id,
                origin=origin,
                token=payload.identity_token,
            )
            if payload.identity_token is not None
            else None
        )
        query = await ConversationService(request.app.state.settings).ask(
            session,
            chatbot_id=chatbot_id,
            question=payload.question,
            page_context=payload.page_context,
            conversation_id=payload.conversation_id,
            origin=origin,
            identity_hash=identity_hash,
            image=payload.image_bytes(),
            image_mime_type=payload.image_mime_type,
        )
    except InvalidWidgetIdentityError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="La identidad del sitio no es válida o ha vencido.",
        ) from exc
    except ChatbotQueryNotFoundError as exc:
        raise HTTPException(
            status_code=404, detail="El chatbot solicitado no existe."
        ) from exc
    except ProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El asistente no está disponible en este momento.",
        ) from exc
    return QueryResponse.model_validate(query, from_attributes=True)
