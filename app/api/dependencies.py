from collections.abc import Iterator

from fastapi import Depends, Request
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings
from app.infra.llm.chat_client import ChatClient
from app.infra.llm.embeddings_client import EmbeddingsClient
from app.infra.vectorstore.chroma_store import ChromaStore
from app.repositories.audit_repository import AuditRepository
from app.repositories.chunk_repository import ChunkRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.query_repository import QueryRepository
from app.services.answer_service import AnswerService
from app.services.audit_service import AuditService
from app.services.chunking_service import ChunkingService
from app.services.document_ingestion_service import DocumentIngestionService
from app.services.embedding_service import EmbeddingService
from app.services.parsing_service import ParsingService
from app.services.query_service import QueryService
from app.services.retrieval_service import RetrievalService


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_session_factory(request: Request) -> sessionmaker[Session]:
    return request.app.state.session_factory


def get_db_session(
    session_factory: sessionmaker[Session] = Depends(get_session_factory),
) -> Iterator[Session]:
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


def get_embeddings_client(request: Request) -> EmbeddingsClient:
    return request.app.state.embeddings_client


def get_chat_client(request: Request) -> ChatClient:
    return request.app.state.chat_client


def get_chroma_store(request: Request) -> ChromaStore:
    return request.app.state.chroma_store


def get_document_service(
    session: Session = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
    embeddings_client: EmbeddingsClient = Depends(get_embeddings_client),
    chroma_store: ChromaStore = Depends(get_chroma_store),
) -> DocumentIngestionService:
    return DocumentIngestionService(
        session=session,
        settings=settings,
        document_repository=DocumentRepository(session),
        chunk_repository=ChunkRepository(session),
        parsing_service=ParsingService(),
        chunking_service=ChunkingService(
            pdf_chunk_size=settings.pdf_chunk_size,
            pdf_chunk_overlap=settings.pdf_chunk_overlap,
        ),
        embedding_service=EmbeddingService(embeddings_client),
        chroma_store=chroma_store,
        audit_service=AuditService(
            session=session,
            audit_repository=AuditRepository(session),
            query_repository=QueryRepository(session),
        ),
    )


def get_query_service(
    session: Session = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
    embeddings_client: EmbeddingsClient = Depends(get_embeddings_client),
    chat_client: ChatClient = Depends(get_chat_client),
    chroma_store: ChromaStore = Depends(get_chroma_store),
) -> QueryService:
    retrieval_service = RetrievalService(
        document_repository=DocumentRepository(session),
        embedding_service=EmbeddingService(embeddings_client),
        chroma_store=chroma_store,
        default_top_k=settings.default_top_k,
    )
    answer_service = AnswerService(
        chat_client=chat_client,
        min_evidence_score=settings.min_evidence_score,
    )
    audit_service = AuditService(
        session=session,
        audit_repository=AuditRepository(session),
        query_repository=QueryRepository(session),
    )
    return QueryService(
        session=session,
        retrieval_service=retrieval_service,
        answer_service=answer_service,
        audit_service=audit_service,
    )


def get_audit_service(session: Session = Depends(get_db_session)) -> AuditService:
    return AuditService(
        session=session,
        audit_repository=AuditRepository(session),
        query_repository=QueryRepository(session),
    )
