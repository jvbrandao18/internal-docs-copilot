from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.logging import get_logger
from app.db.session import build_engine, build_session_factory, init_db
from app.domain.services.audit_service import AuditService
from app.domain.services.chunking import ChunkingService
from app.domain.services.document_service import DocumentService
from app.domain.services.query_service import QueryService
from app.infra.openai.client import OpenAIClient
from app.infra.parsers.factory import ParserFactory
from app.infra.parsers.pdf import PdfParser
from app.infra.parsers.spreadsheet import SpreadsheetParser
from app.infra.vector.chroma_store import ChromaVectorStore


class AppContainer:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.logger = get_logger(__name__)
        self.engine = build_engine(settings.database_url)
        self.session_factory = build_session_factory(self.engine)
        self.parser_factory = ParserFactory([PdfParser(), SpreadsheetParser()])
        self.chunking_service = ChunkingService(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )
        self.openai_client = OpenAIClient(
            api_key=settings.openai_api_key,
            embedding_model=settings.openai_embedding_model,
            chat_model=settings.openai_chat_model,
        )
        self.vector_store: ChromaVectorStore | None = None

    def initialize(self) -> None:
        self.settings.ensure_directories()
        init_db(self.engine)
        self.vector_store = ChromaVectorStore(
            persist_path=self.settings.chroma_path,
            collection_name=self.settings.chroma_collection_name,
        )
        self.logger.info(
            "container_initialized",
            extra={
                "database_url": self.settings.database_url,
                "chroma_path": str(self.settings.chroma_path),
            },
        )

    def close(self) -> None:
        self.engine.dispose()

    @contextmanager
    def session(self) -> Iterator[Session]:
        session = self.session_factory()
        try:
            yield session
        finally:
            session.close()

    def build_document_service(self, session: Session) -> DocumentService:
        return DocumentService(
            session=session,
            settings=self.settings,
            parser_factory=self.parser_factory,
            chunking_service=self.chunking_service,
            vector_store=self._get_vector_store(),
            openai_client=self.openai_client,
        )

    def build_query_service(self, session: Session) -> QueryService:
        return QueryService(
            session=session,
            settings=self.settings,
            vector_store=self._get_vector_store(),
            openai_client=self.openai_client,
        )

    def build_audit_service(self, session: Session) -> AuditService:
        return AuditService(session=session)

    def healthcheck(self) -> dict[str, object]:
        database_status = "ok"
        vector_status = "ok"

        with self.session() as session:
            session.execute(text("SELECT 1"))

        try:
            vector_count = self._get_vector_store().count()
        except Exception:
            vector_status = "degraded"
            vector_count = None

        return {
            "status": "ok" if database_status == "ok" and vector_status == "ok" else "degraded",
            "app_name": self.settings.app_name,
            "version": self.settings.version,
            "environment": self.settings.app_env,
            "database": database_status,
            "vector_store": vector_status,
            "indexed_chunks": vector_count,
        }

    def _get_vector_store(self) -> ChromaVectorStore:
        if self.vector_store is None:
            raise RuntimeError("Container was not initialized.")
        return self.vector_store
