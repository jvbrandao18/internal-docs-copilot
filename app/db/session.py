from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db import models  # noqa: F401
from app.db.base import Base


def build_engine(database_url: str) -> Engine:
    return create_engine(
        database_url,
        future=True,
        connect_args={"check_same_thread": False},
    )


def build_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
        class_=Session,
    )


def init_db(engine: Engine) -> None:
    Base.metadata.create_all(bind=engine)
