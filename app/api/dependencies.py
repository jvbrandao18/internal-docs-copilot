from collections.abc import Iterator

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.container import AppContainer
from app.domain.services.audit_service import AuditService
from app.domain.services.document_service import DocumentService
from app.domain.services.query_service import QueryService


def get_container(request: Request) -> AppContainer:
    return request.app.state.container


def get_db_session(container: AppContainer = Depends(get_container)) -> Iterator[Session]:
    with container.session() as session:
        yield session


def get_document_service(
    session: Session = Depends(get_db_session),
    container: AppContainer = Depends(get_container),
) -> DocumentService:
    return container.build_document_service(session)


def get_query_service(
    session: Session = Depends(get_db_session),
    container: AppContainer = Depends(get_container),
) -> QueryService:
    return container.build_query_service(session)


def get_audit_service(
    session: Session = Depends(get_db_session),
    container: AppContainer = Depends(get_container),
) -> AuditService:
    return container.build_audit_service(session)
