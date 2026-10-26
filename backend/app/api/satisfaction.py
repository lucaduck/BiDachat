from collections import defaultdict, deque
from datetime import datetime
from time import monotonic
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    CurrentSession,
    get_current_session,
    get_database_session,
)
from app.api.queries import require_widget_origin
from app.schemas.satisfaction import (
    SatisfactionMetricsResponse,
    SurveyCommentsPage,
    SurveyOfferRequest,
    SurveyResponseRequest,
    SurveyStateResponse,
)
from app.services.metrics_service import (
    ChatbotMetricsNotFoundError,
    MetricsInterval,
    MetricsPeriodValidationError,
)
from app.services.satisfaction_metrics_service import SatisfactionMetricsService
from app.services.satisfaction_service import (
    SatisfactionService,
    SurveyAlreadyAnsweredError,
    SurveyConversationUnavailableError,
)
from app.services.widget_identity_service import (
    InvalidWidgetIdentityError,
    verify_widget_identity,
)

router = APIRouter(tags=["satisfaction"])
_requests: dict[tuple[str, UUID], deque[float]] = defaultdict(deque)


def _check_limit(request: Request, chatbot_id: UUID) -> None:
    key = (request.client.host if request.client else "unknown", chatbot_id)
    now = monotonic()
    recent = _requests[key]
    while recent and now - recent[0] > 60:
        recent.popleft()
    if len(recent) >= 20:
        raise HTTPException(
            status_code=429,
            detail="Demasiadas solicitudes. Inténtalo en un minuto.",
            headers={"Retry-After": "60"},
        )
    recent.append(now)


def _identity_hash(
    request: Request, chatbot_id: UUID, origin: str, token: str | None
) -> str | None:
    if token is None:
        return None
    try:
        return verify_widget_identity(
            request.app.state.settings,
            chatbot_id=chatbot_id,
            origin=origin,
            token=token,
        )
    except InvalidWidgetIdentityError as exc:
        raise HTTPException(
            status_code=401, detail="La identidad del sitio no es válida o ha vencido."
        ) from exc


def _unavailable() -> HTTPException:
    return HTTPException(status_code=404, detail="La conversación no está disponible.")


@router.post("/chatbots/{chatbot_id}/survey-offers", response_model=SurveyStateResponse)
async def offer_survey(
    chatbot_id: UUID,
    payload: SurveyOfferRequest,
    request: Request,
    origin: Annotated[str, Depends(require_widget_origin)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> SurveyStateResponse:
    _check_limit(request, chatbot_id)
    identity_hash = _identity_hash(request, chatbot_id, origin, payload.identity_token)
    try:
        feedback = await SatisfactionService().offer(
            session,
            chatbot_id=chatbot_id,
            conversation_id=payload.conversation_id,
            origin=origin,
            identity_hash=identity_hash,
        )
        await session.commit()
    except SurveyConversationUnavailableError as exc:
        raise _unavailable() from exc
    return SurveyStateResponse(
        state="submitted" if feedback.submitted_at else "offered"
    )


@router.post(
    "/chatbots/{chatbot_id}/survey-responses", response_model=SurveyStateResponse
)
async def submit_survey(
    chatbot_id: UUID,
    payload: SurveyResponseRequest,
    request: Request,
    origin: Annotated[str, Depends(require_widget_origin)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> SurveyStateResponse:
    _check_limit(request, chatbot_id)
    identity_hash = _identity_hash(request, chatbot_id, origin, payload.identity_token)
    try:
        await SatisfactionService().submit(
            session,
            chatbot_id=chatbot_id,
            conversation_id=payload.conversation_id,
            origin=origin,
            identity_hash=identity_hash,
            satisfaction_score=payload.satisfaction_score,
            resolution=payload.resolution,
            clarity_score=payload.clarity_score,
            comment=payload.comment,
        )
        await session.commit()
    except SurveyConversationUnavailableError as exc:
        raise _unavailable() from exc
    except SurveyAlreadyAnsweredError as exc:
        raise HTTPException(
            status_code=409, detail="Esta conversación ya tiene una valoración."
        ) from exc
    return SurveyStateResponse(state="submitted")


def _invalid_period() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail="Selecciona fechas con zona horaria y un rango de hasta 1000 periodos.",
    )


@router.get(
    "/chatbots/{chatbot_id}/satisfaction-metrics",
    response_model=SatisfactionMetricsResponse,
)
async def get_satisfaction_metrics(
    chatbot_id: UUID,
    _: Annotated[CurrentSession, Depends(get_current_session)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
    started_at: datetime | None = None,
    ended_at: datetime | None = None,
    interval: MetricsInterval = "day",
) -> SatisfactionMetricsResponse:
    try:
        return await SatisfactionMetricsService().get_metrics(
            session,
            chatbot_id=chatbot_id,
            started_at=started_at,
            ended_at=ended_at,
            interval=interval,
        )
    except ChatbotMetricsNotFoundError as exc:
        raise HTTPException(
            status_code=404, detail="El chatbot solicitado no existe."
        ) from exc
    except MetricsPeriodValidationError as exc:
        raise _invalid_period() from exc


@router.get(
    "/chatbots/{chatbot_id}/survey-responses", response_model=SurveyCommentsPage
)
async def get_survey_comments(
    chatbot_id: UUID,
    _: Annotated[CurrentSession, Depends(get_current_session)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
    started_at: datetime | None = None,
    ended_at: datetime | None = None,
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> SurveyCommentsPage:
    try:
        return await SatisfactionMetricsService().get_comments(
            session,
            chatbot_id=chatbot_id,
            started_at=started_at,
            ended_at=ended_at,
            limit=limit,
            offset=offset,
        )
    except ChatbotMetricsNotFoundError as exc:
        raise HTTPException(
            status_code=404, detail="El chatbot solicitado no existe."
        ) from exc
    except MetricsPeriodValidationError as exc:
        raise _invalid_period() from exc
