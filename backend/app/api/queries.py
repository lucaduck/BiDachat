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

router = APIRouter(tags=["queries"])
_requests: dict[str, deque[float]] = defaultdict(deque)


@router.post("/chatbots/{chatbot_id}/queries", response_model=QueryResponse)
async def create_query(
    chatbot_id: UUID,
    payload: QueryRequest,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> QueryResponse:
    client = request.client.host if request.client else "unknown"
    key = client
    now = monotonic()
    recent = _requests[key]
    while recent and now - recent[0] > 60:
        recent.popleft()
    if len(recent) >= 10:
        raise HTTPException(
            status_code=429, detail="Demasiadas consultas. Inténtalo en un minuto."
        )
    recent.append(now)
    try:
        query = await ConversationService(request.app.state.settings).ask(
            session,
            chatbot_id=chatbot_id,
            question=payload.question,
            image=payload.image_bytes(),
            image_mime_type=payload.image_mime_type,
        )
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
