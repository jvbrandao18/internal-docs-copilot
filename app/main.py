from contextlib import asynccontextmanager
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.routes import audit, documents, health, queries
from app.core.config import get_settings
from app.core.container import AppContainer
from app.core.exceptions import AppError
from app.core.logging import configure_logging, get_logger

settings = get_settings()
configure_logging(settings.log_level)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    container = AppContainer(settings)
    container.initialize()
    app.state.container = container
    logger.info(
        "application_started",
        extra={"app_name": settings.app_name, "environment": settings.app_env},
    )
    try:
        yield
    finally:
        container.close()
        logger.info("application_stopped", extra={"app_name": settings.app_name})


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        debug=settings.debug,
        lifespan=lifespan,
    )

    @app.middleware("http")
    async def request_logging_middleware(request: Request, call_next):
        request_id = uuid4().hex
        started_at = perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            duration_ms = round((perf_counter() - started_at) * 1000, 2)
            logger.exception(
                "request_failed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": duration_ms,
                },
            )
            raise

        duration_ms = round((perf_counter() - started_at) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "request_completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        return response

    @app.exception_handler(AppError)
    async def handle_application_error(_: Request, exc: AppError) -> JSONResponse:
        logger.warning(
            "application_error",
            extra={"error_code": exc.code, "detail": exc.message, "status_code": exc.status_code},
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message, "code": exc.code},
        )

    app.include_router(health.router, prefix=settings.api_prefix)
    app.include_router(documents.router, prefix=settings.api_prefix)
    app.include_router(queries.router, prefix=settings.api_prefix)
    app.include_router(audit.router, prefix=settings.api_prefix)

    return app


app = create_app()
