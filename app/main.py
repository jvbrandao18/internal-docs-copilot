from contextlib import asynccontextmanager
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.routes import audit, documents, health, queries
from app.core.config import Settings, get_settings
from app.core.exceptions import AppError
from app.core.logging import configure_logging, get_logger, log_event
from app.database.session import build_engine, build_session_factory, init_database
from app.infra.llm.chat_client import ChatClient
from app.infra.llm.embeddings_client import EmbeddingsClient
from app.infra.vectorstore.chroma_store import ChromaStore

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings: Settings = app.state.settings
    configure_logging(settings.log_level)
    settings.ensure_directories()

    engine = build_engine(settings.sqlite_url)
    init_database(engine)

    app.state.engine = engine
    app.state.session_factory = build_session_factory(engine)
    app.state.embeddings_client = app.state.embeddings_client or EmbeddingsClient(
        api_key=settings.openai_api_key,
        model=settings.openai_embedding_model,
    )
    app.state.chat_client = app.state.chat_client or ChatClient(
        api_key=settings.openai_api_key,
        model=settings.openai_chat_model,
    )
    app.state.chroma_store = app.state.chroma_store or ChromaStore(settings.chroma_persist_dir)

    log_event(
        logger,
        "application_started",
        status="success",
        details={"environment": settings.app_env},
    )
    try:
        yield
    finally:
        engine.dispose()
        log_event(logger, "application_stopped", status="success")


def create_app(
    *,
    settings: Settings | None = None,
    embeddings_client: EmbeddingsClient | None = None,
    chat_client: ChatClient | None = None,
    chroma_store: ChromaStore | None = None,
) -> FastAPI:
    resolved_settings = settings or get_settings()
    app = FastAPI(
        title=resolved_settings.app_name,
        debug=resolved_settings.app_debug,
        lifespan=lifespan,
    )

    app.state.settings = resolved_settings
    app.state.embeddings_client = embeddings_client
    app.state.chat_client = chat_client
    app.state.chroma_store = chroma_store

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        request_id = uuid4().hex
        started_at = perf_counter()
        try:
            response = await call_next(request)
        except AppError:
            raise
        except Exception as exc:
            latency_ms = int((perf_counter() - started_at) * 1000)
            log_event(
                logger,
                "request_failed",
                status="failed",
                latency_ms=latency_ms,
                error_type=type(exc).__name__,
                details={"path": request.url.path, "method": request.method},
            )
            raise

        latency_ms = int((perf_counter() - started_at) * 1000)
        response.headers["X-Request-ID"] = request_id
        log_event(
            logger,
            "request_completed",
            status="success",
            latency_ms=latency_ms,
            details={
                "path": request.url.path,
                "method": request.method,
                "status_code": response.status_code,
            },
        )
        return response

    @app.exception_handler(AppError)
    async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        log_event(
            logger,
            "application_error",
            status="failed",
            error_type=exc.code,
            details=exc.message,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message, "code": exc.code},
        )

    app.include_router(health.router)
    app.include_router(documents.router)
    app.include_router(queries.router)
    app.include_router(audit.router)
    return app


app = create_app()
