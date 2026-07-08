import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.auth import router as auth_router
from app.api.v1.cattle import router as cattle_router
from app.api.v1.calls import router as calls_router
from app.api.v1.chat import router as chat_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.sessions import router as sessions_router
from app.api.v1.websocket import router as websocket_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.firebase import initialize_firebase_admin
from app.core.logging import configure_logging
from app.services.deleted_chat_cleanup import run_deleted_chat_cleanup


@asynccontextmanager
async def lifespan(_: FastAPI):
    stop_event = asyncio.Event()
    cleanup_task = asyncio.create_task(run_deleted_chat_cleanup(stop_event))
    try:
        yield
    finally:
        stop_event.set()
        await cleanup_task


def create_app() -> FastAPI:
    configure_logging()
    initialize_firebase_admin()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        docs_url="/docs",
        lifespan=lifespan,
        redoc_url="/redoc",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Accept", "Authorization", "Content-Type"],
    )
    register_exception_handlers(app)

    app.include_router(auth_router, prefix=settings.api_v1_prefix)
    app.include_router(cattle_router, prefix=settings.api_v1_prefix)
    app.include_router(sessions_router, prefix=settings.api_v1_prefix)
    app.include_router(chat_router, prefix=settings.api_v1_prefix)
    app.include_router(calls_router, prefix=settings.api_v1_prefix)
    app.include_router(notifications_router, prefix=settings.api_v1_prefix)
    app.include_router(websocket_router, prefix=settings.api_v1_prefix)

    @app.get("/health", tags=["health"])
    async def health_check() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
