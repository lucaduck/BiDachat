import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import router
from app.core.config import Settings, get_settings
from app.database.session import Database
from app.services.conversation_cleanup_service import run_conversation_cleanup

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings if settings is not None else get_settings()
    docs_enabled = settings.app_env != "production"

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        database = getattr(application.state, "database", None)
        cleanup_task = (
            asyncio.create_task(run_conversation_cleanup(database, settings))
            if database is not None and settings.app_env != "test"
            else None
        )
        try:
            yield
        finally:
            if cleanup_task is not None:
                cleanup_task.cancel()
                with suppress(asyncio.CancelledError):
                    await cleanup_task
            if database is not None:
                await database.dispose()

    application = FastAPI(
        title="BIDACHAT API",
        version="0.1.0",
        debug=False,
        docs_url="/api/v1/docs" if docs_enabled else None,
        redoc_url=None,
        openapi_url="/api/v1/openapi.json" if docs_enabled else None,
        lifespan=lifespan,
    )
    application.state.settings = settings
    allowed_origins = [
        origin.strip()
        for origin in settings.widget_allowed_origins.split(",")
        if origin.strip()
    ]
    if allowed_origins:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=allowed_origins,
            allow_methods=["POST", "OPTIONS"],
            allow_headers=["Content-Type"],
        )
    if settings.database_url is not None:
        application.state.database = Database.from_settings(settings)
    application.include_router(router, prefix="/api/v1")

    @application.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        logger.error("Unhandled API error", exc_info=exc)
        return JSONResponse(
            status_code=500,
            content={"detail": "Ocurrió un error interno al procesar la solicitud."},
        )

    return application


app = create_app()
