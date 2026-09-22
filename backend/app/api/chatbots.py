from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Request,
    Response,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    CurrentSession,
    get_current_session,
    get_database_session,
)
from app.schemas.chatbot import (
    ChatbotCreate,
    ChatbotResponse,
    ChatbotUpdate,
    LlmModelResponse,
)
from app.schemas.document import DocumentResponse
from app.schemas.metrics import MetricsResponse
from app.services.chatbot_deletion_service import (
    ChatbotDeletionNotFoundError,
    ChatbotDeletionService,
)
from app.services.chatbot_service import (
    ChatbotDetails,
    ChatbotNotFoundError,
    ChatbotService,
    LlmModelNotFoundError,
)
from app.services.document_service import (
    ChatbotDocumentNotFoundError,
    DocumentService,
    DocumentUploadValidationError,
    UploadDocument,
)
from app.services.metrics_service import (
    ChatbotMetricsNotFoundError,
    MetricsPeriodValidationError,
    MetricsService,
)

router = APIRouter(tags=["chatbots"])


@router.get("/llm-models", response_model=list[LlmModelResponse])
async def list_llm_models(
    _: Annotated[CurrentSession, Depends(get_current_session)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> list[LlmModelResponse]:
    llm_models = await ChatbotService().list_llm_models(session)
    return [LlmModelResponse.model_validate(llm_model) for llm_model in llm_models]


@router.get("/chatbots", response_model=list[ChatbotResponse])
async def list_chatbots(
    _: Annotated[CurrentSession, Depends(get_current_session)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> list[ChatbotResponse]:
    chatbots = await ChatbotService().list_chatbots(session)
    return [_to_response(chatbot) for chatbot in chatbots]


@router.post(
    "/chatbots",
    response_model=ChatbotResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_chatbot(
    payload: ChatbotCreate,
    current_session: Annotated[CurrentSession, Depends(get_current_session)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> ChatbotResponse:
    try:
        chatbot = await ChatbotService().create_chatbot(
            session,
            created_by=current_session.user.id,
            configured_llm_model_id=payload.configured_llm_model_id,
            name=payload.name,
            description=payload.description,
            behavior_instructions=payload.behavior_instructions,
        )
    except LlmModelNotFoundError as exc:
        raise _llm_model_not_found() from exc
    await session.commit()
    return _to_response(chatbot)


@router.get("/chatbots/{chatbot_id}", response_model=ChatbotResponse)
async def get_chatbot(
    chatbot_id: UUID,
    _: Annotated[CurrentSession, Depends(get_current_session)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> ChatbotResponse:
    try:
        chatbot = await ChatbotService().get_chatbot(session, chatbot_id)
    except ChatbotNotFoundError as exc:
        raise _chatbot_not_found() from exc
    return _to_response(chatbot)


@router.put("/chatbots/{chatbot_id}", response_model=ChatbotResponse)
async def update_chatbot(
    chatbot_id: UUID,
    payload: ChatbotUpdate,
    _: Annotated[CurrentSession, Depends(get_current_session)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> ChatbotResponse:
    try:
        chatbot = await ChatbotService().update_chatbot(
            session,
            chatbot_id,
            configured_llm_model_id=payload.configured_llm_model_id,
            name=payload.name,
            description=payload.description,
            behavior_instructions=payload.behavior_instructions,
        )
    except ChatbotNotFoundError as exc:
        raise _chatbot_not_found() from exc
    except LlmModelNotFoundError as exc:
        raise _llm_model_not_found() from exc
    await session.commit()
    return _to_response(chatbot)


@router.delete("/chatbots/{chatbot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chatbot(
    chatbot_id: UUID,
    request: Request,
    _: Annotated[CurrentSession, Depends(get_current_session)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> Response:
    deletion_service = ChatbotDeletionService(request.app.state.settings)
    try:
        deletion = await deletion_service.delete_chatbot(session, chatbot_id)
    except ChatbotDeletionNotFoundError as exc:
        raise _chatbot_not_found() from exc
    await session.commit()
    deletion_service.clean_private_files(deletion)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/chatbots/{chatbot_id}/documents",
    response_model=list[DocumentResponse],
)
async def list_documents(
    chatbot_id: UUID,
    request: Request,
    _: Annotated[CurrentSession, Depends(get_current_session)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> list[DocumentResponse]:
    try:
        documents = await DocumentService(request.app.state.settings).list_documents(
            session,
            chatbot_id,
        )
    except ChatbotDocumentNotFoundError as exc:
        raise _chatbot_not_found() from exc
    return [DocumentResponse.model_validate(document) for document in documents]


@router.post(
    "/chatbots/{chatbot_id}/documents",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    chatbot_id: UUID,
    request: Request,
    file: Annotated[UploadFile, File(description="Documento permitido de hasta 20 MB")],
    _: Annotated[CurrentSession, Depends(get_current_session)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> DocumentResponse:
    try:
        document = await DocumentService(request.app.state.settings).upload_document(
            session,
            chatbot_id=chatbot_id,
            upload=UploadDocument(
                filename=file.filename,
                media_type=file.content_type,
                content=await file.read(),
            ),
        )
    except ChatbotDocumentNotFoundError as exc:
        raise _chatbot_not_found() from exc
    except DocumentUploadValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="El documento no cumple el tipo, contenido o tamaño permitido.",
        ) from exc
    await session.commit()
    return DocumentResponse.model_validate(document)


@router.get(
    "/chatbots/{chatbot_id}/metrics",
    response_model=MetricsResponse,
)
async def get_chatbot_metrics(
    chatbot_id: UUID,
    _: Annotated[CurrentSession, Depends(get_current_session)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
    started_at: datetime | None = None,
    ended_at: datetime | None = None,
) -> MetricsResponse:
    try:
        metrics = await MetricsService().get_metrics(
            session,
            chatbot_id=chatbot_id,
            started_at=started_at,
            ended_at=ended_at,
        )
    except ChatbotMetricsNotFoundError as exc:
        raise _chatbot_not_found() from exc
    except MetricsPeriodValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="El periodo de mÃ©tricas no es vÃ¡lido.",
        ) from exc
    return MetricsResponse.model_validate(metrics, from_attributes=True)


def _to_response(details: ChatbotDetails) -> ChatbotResponse:
    chatbot = details.chatbot
    return ChatbotResponse(
        id=chatbot.id,
        created_by=chatbot.created_by,
        name=chatbot.name,
        description=chatbot.description,
        behavior_instructions=chatbot.behavior_instructions,
        configured_llm_model=LlmModelResponse.model_validate(details.llm_model),
        created_at=chatbot.created_at,
        updated_at=chatbot.updated_at,
    )


def _chatbot_not_found() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="El chatbot solicitado no existe.",
    )


def _llm_model_not_found() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail="El modelo de lenguaje seleccionado no está disponible.",
    )
