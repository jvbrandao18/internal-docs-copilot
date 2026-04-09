from pathlib import Path
from sqlite3 import Connection as SQLiteConnection

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.database import models  # noqa: F401
from app.database.base import Base


def _ensure_sqlite_directory(sqlite_url: str) -> None:
    if not sqlite_url.startswith("sqlite"):
        return
    path_fragment = sqlite_url.split("///", maxsplit=1)[-1]
    if not path_fragment or path_fragment == ":memory:":
        return
    sqlite_path = Path(path_fragment)
    if sqlite_path.parent:
        sqlite_path.parent.mkdir(parents=True, exist_ok=True)


def build_engine(sqlite_url: str) -> Engine:
    _ensure_sqlite_directory(sqlite_url)
    engine = create_engine(
        sqlite_url,
        future=True,
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_connection: SQLiteConnection, _: object) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


def build_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
        class_=Session,
    )


def init_database(engine: Engine) -> None:
    Base.metadata.create_all(bind=engine)
