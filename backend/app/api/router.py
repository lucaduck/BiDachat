from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.chatbots import router as chatbots_router
from app.api.queries import router as queries_router
from app.api.settings import router as settings_router
from app.schemas.health import HealthResponse

router = APIRouter()
router.include_router(auth_router)
router.include_router(chatbots_router)
router.include_router(queries_router)
router.include_router(settings_router)


@router.get("/health", response_model=HealthResponse, tags=["health"])
def get_health() -> HealthResponse:
    return HealthResponse()
