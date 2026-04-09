import mimetypes
import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.exceptions import AppError, NotFoundError, UnsupportedFileTypeError
from app.core.logging import get_logger
from app.db.models import AuditEvent, Document, utcnow
from app.db.repositories.documents import AuditRepository, DocumentRepository
from app.domain.services.chunking import ChunkingService
from app.infra.openai.client import OpenAIClient
from app.infra.parsers.factory import ParserFactory
from app.infra.vector.chroma_store import ChromaVectorStore


class DocumentService:
    allowed_extensions = {".pdf", ".xlsx", ".csv"}

    def __init__(
        self,
        *,
        session: Session,
        settings: Settings,
        parser_factory: ParserFactory,
        chunking_service: ChunkingService,
        vector_store: ChromaVectorStore,
        openai_client: OpenAIClient,
    ) -> None:
        self.session = session
        self.settings = settings
        self.parser_factory = parser_factory
        self.chunking_service = chunking_service
        self.vector_store = vector_store
        self.openai_client = openai_client
        self.document_repository = DocumentRepository(session)
        self.audit_repository = AuditRepository(session)
        self.logger = get_logger(__name__)

    def ingest_upload(self, upload_file: UploadFile) -> tuple[Document, AuditEvent]:
        filename = upload_file.filename or "upload"
        extension = Path(filename).suffix.lower()
        if extension not in self.allowed_extensions:
            raise UnsupportedFileTypeError(f"Unsupported file type: {extension or 'unknown'}")

        document_id = str(uuid4())
        storage_path = self.settings.uploads_dir / f"{document_id}{extension}"
        content_type = (
            upload_file.content_type
            or mimetypes.guess_type(filename)[0]
            or "application/octet-stream"
        )

        document = Document(
            id=document_id,
            filename=filename,
            content_type=content_type,
            file_extension=extension,
            storage_path=str(storage_path),
            status="processing",
            document_metadata={},
        )
        self.document_repository.add(document)
        self.session.commit()

        try:
            upload_file.file.seek(0)
            with storage_path.open("wb") as target_file:
                shutil.copyfileobj(upload_file.file, target_file)

            parser = self.parser_factory.get_parser(extension)
            parsed_document = parser.parse(
                storage_path,
                filename=filename,
                content_type=content_type,
            )
            chunks = self.chunking_service.chunk_document(
                document_id=document_id,
                parsed_document=parsed_document,
            )
            if not chunks:
                raise AppError(
                    "The document does not contain extractable text.",
                    status_code=422,
                    code="empty_document",
                )

            embeddings = self.openai_client.embed_texts([chunk.text for chunk in chunks])
            self.vector_store.upsert_chunks(chunks, embeddings)

            document.status = "indexed"
            document.chunk_count = len(chunks)
            document.document_metadata = parsed_document.metadata
            document.error_message = None

            audit_event = self._build_audit_event(
                event_type="document_indexed",
                status="success",
                document_id=document_id,
                payload={
                    "filename": filename,
                    "chunk_count": len(chunks),
                    "metadata": parsed_document.metadata,
                },
            )
            self.audit_repository.add(audit_event)
            self.session.commit()

            self.logger.info(
                "document_indexed",
                extra={
                    "document_id": document_id,
                    "filename": filename,
                    "chunk_count": len(chunks),
                },
            )
            return document, audit_event

        except Exception as exc:
            self.session.rollback()
            self._cleanup_vectors(document_id)

            failed_document = self.document_repository.get(document_id)
            if failed_document is not None:
                failed_document.status = "failed"
                failed_document.error_message = str(exc)

            audit_event = self._build_audit_event(
                event_type="document_indexed",
                status="failed",
                document_id=document_id,
                payload={"filename": filename, "error": str(exc)},
            )
            self.audit_repository.add(audit_event)
            self.session.commit()

            self.logger.exception(
                "document_indexing_failed",
                extra={"document_id": document_id, "filename": filename},
            )
            if isinstance(exc, AppError):
                raise
            raise AppError(
                "Document ingestion failed during parsing or indexing.",
                status_code=500,
                code="document_ingestion_failed",
            ) from exc

    def list_documents(self, *, include_deleted: bool = False) -> list[Document]:
        return list(self.document_repository.list(include_deleted=include_deleted))

    def delete_document(self, document_id: str) -> tuple[Document, AuditEvent]:
        document = self.document_repository.get(document_id)
        if document is None or document.deleted_at is not None:
            raise NotFoundError(f"Document '{document_id}' was not found.")

        deleted_vectors = self.vector_store.delete_document(document_id)
        storage_path = Path(document.storage_path)
        if storage_path.exists():
            storage_path.unlink()

        document.status = "deleted"
        document.deleted_at = utcnow()
        audit_event = self._build_audit_event(
            event_type="document_deleted",
            status="success",
            document_id=document_id,
            payload={"filename": document.filename, "deleted_vectors": deleted_vectors},
        )
        self.audit_repository.add(audit_event)
        self.session.commit()

        self.logger.info(
            "document_deleted",
            extra={"document_id": document_id, "filename": document.filename},
        )
        return document, audit_event

    def _cleanup_vectors(self, document_id: str) -> None:
        try:
            self.vector_store.delete_document(document_id)
        except Exception:
            self.logger.warning(
                "vector_cleanup_failed",
                extra={"document_id": document_id},
            )

    def _build_audit_event(
        self,
        *,
        event_type: str,
        status: str,
        document_id: str | None,
        payload: dict[str, object],
    ) -> AuditEvent:
        return AuditEvent(
            id=str(uuid4()),
            event_type=event_type,
            status=status,
            actor="system",
            document_id=document_id,
            payload=payload,
        )
