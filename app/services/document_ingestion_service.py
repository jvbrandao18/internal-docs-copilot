import hashlib
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.exceptions import (
    NotFoundError,
    UnsupportedFileTypeError,
    ValidationError,
)
from app.core.logging import get_logger, log_event
from app.database.models import Chunk, Document, utcnow
from app.infra.vectorstore.chroma_store import ChromaStore
from app.repositories.chunk_repository import ChunkRepository
from app.repositories.document_repository import DocumentRepository
from app.services.audit_service import AuditService
from app.services.chunking_service import ChunkingService, ChunkPayload
from app.services.embedding_service import EmbeddingService
from app.services.parsing_service import ParsingService


class DocumentIngestionService:
    allowed_extensions = {".pdf": "pdf", ".xlsx": "xlsx", ".csv": "csv"}

    def __init__(
        self,
        *,
        session: Session,
        settings: Settings,
        document_repository: DocumentRepository,
        chunk_repository: ChunkRepository,
        parsing_service: ParsingService,
        chunking_service: ChunkingService,
        embedding_service: EmbeddingService,
        chroma_store: ChromaStore,
        audit_service: AuditService,
    ) -> None:
        self.session = session
        self.settings = settings
        self.document_repository = document_repository
        self.chunk_repository = chunk_repository
        self.parsing_service = parsing_service
        self.chunking_service = chunking_service
        self.embedding_service = embedding_service
        self.chroma_store = chroma_store
        self.audit_service = audit_service
        self.logger = get_logger(__name__)

    def ingest(self, upload_file: UploadFile) -> Document:
        filename = upload_file.filename or ""
        extension = Path(filename).suffix.lower()
        file_type = self.allowed_extensions.get(extension)
        if file_type is None:
            raise UnsupportedFileTypeError("Only PDF, XLSX and CSV files are supported.")
        if not filename.strip():
            raise ValidationError("Uploaded file must have a valid filename.")

        document_id = str(uuid4())
        stored_path = self.settings.upload_dir / f"{document_id}{extension}"
        sha256_hash = self._save_upload(upload_file, stored_path)

        document = Document(
            id=document_id,
            filename=filename,
            file_type=file_type,
            status="processing",
            path=str(stored_path),
            sha256_hash=sha256_hash,
        )
        self.document_repository.add(document)
        self.audit_service.record_event(
            event_type="document_uploaded",
            document_id=document_id,
            payload_json={"filename": filename, "file_type": file_type},
        )
        self.session.commit()

        try:
            parsed_document = self.parsing_service.parse(stored_path, file_type)
            chunk_payloads = self.chunking_service.build_chunks(parsed_document)
            if not chunk_payloads:
                raise ValidationError("The uploaded document does not contain extractable content.")

            chunks = self._build_chunk_models(
                document_id=document_id,
                chunk_payloads=chunk_payloads,
            )
            self.chunk_repository.add_many(chunks)

            embeddings = self.embedding_service.embed_texts([chunk.content for chunk in chunks])
            self.chroma_store.upsert_chunks(chunks, embeddings, filename)

            document.status = "indexed"
            document.processed_at = utcnow()
            document.page_count = parsed_document.page_count
            document.sheet_count = parsed_document.sheet_count
            document.error_message = None
            self.audit_service.record_event(
                event_type="document_indexed",
                document_id=document_id,
                payload_json={"chunk_count": len(chunks)},
            )
            self.session.commit()
            log_event(
                self.logger,
                "document_indexed",
                document_id=document_id,
                filename=filename,
                file_type=file_type,
                status="success",
                details={"chunk_count": len(chunks)},
            )
            return document
        except Exception as exc:
            self.session.rollback()
            self.chroma_store.delete_document(document_id)
            failed_document = self.document_repository.get(document_id)
            if failed_document is not None:
                failed_document.status = "failed"
                failed_document.error_message = str(exc)
                self.audit_service.record_event(
                    event_type="document_failed",
                    document_id=document_id,
                    payload_json={"error": str(exc)},
                )
                self.session.commit()
            log_event(
                self.logger,
                "document_failed",
                document_id=document_id,
                filename=filename,
                file_type=file_type,
                status="failed",
                error_type=type(exc).__name__,
                details=str(exc),
            )
            raise

    def list_documents(self) -> list[Document]:
        return list(self.document_repository.list())

    def get_document(self, document_id: str) -> Document:
        document = self.document_repository.get(document_id)
        if document is None:
            raise NotFoundError(f"Document '{document_id}' was not found.")
        return document

    def delete_document(self, document_id: str) -> None:
        document = self.get_document(document_id)
        deleted_chunks = self.chunk_repository.delete_by_document(document_id)
        deleted_vectors = self.chroma_store.delete_document(document_id)
        file_path = Path(document.path)
        if file_path.exists():
            file_path.unlink()
        self.document_repository.delete(document)
        self.audit_service.record_event(
            event_type="document_deleted",
            document_id=document_id,
            payload_json={"deleted_chunks": deleted_chunks, "deleted_vectors": deleted_vectors},
        )
        self.session.commit()
        log_event(
            self.logger,
            "document_deleted",
            document_id=document_id,
            filename=document.filename,
            file_type=document.file_type,
            status="success",
            details={"deleted_chunks": deleted_chunks, "deleted_vectors": deleted_vectors},
        )

    def _save_upload(self, upload_file: UploadFile, destination: Path) -> str:
        sha256 = hashlib.sha256()
        total_bytes = 0
        upload_file.file.seek(0)
        with destination.open("wb") as buffer:
            while True:
                chunk = upload_file.file.read(1024 * 1024)
                if not chunk:
                    break
                total_bytes += len(chunk)
                buffer.write(chunk)
                sha256.update(chunk)
        upload_file.file.seek(0)
        if total_bytes == 0:
            destination.unlink(missing_ok=True)
            raise ValidationError("Uploaded file is empty.")
        return sha256.hexdigest()

    def _build_chunk_models(
        self,
        *,
        document_id: str,
        chunk_payloads: list[ChunkPayload],
    ) -> list[Chunk]:
        chunks: list[Chunk] = []
        for index, chunk_payload in enumerate(chunk_payloads, start=1):
            chunks.append(
                Chunk(
                    id=f"{document_id}:{index}",
                    document_id=document_id,
                    chunk_index=index,
                    content=chunk_payload.content,
                    source_type=chunk_payload.source_type,
                    page_number=chunk_payload.page_number,
                    sheet_name=chunk_payload.sheet_name,
                    row_start=chunk_payload.row_start,
                    row_end=chunk_payload.row_end,
                    metadata_json=chunk_payload.metadata_json,
                )
            )
        return chunks
