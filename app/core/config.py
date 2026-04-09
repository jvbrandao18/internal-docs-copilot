from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "internal-docs-copilot"
    app_env: str = "development"
    version: str = "0.1.0"
    debug: bool = False
    api_prefix: str = "/api/v1"

    sqlite_db_path: Path = Field(default=Path("./data/internal_docs_copilot.db"))
    chroma_path: Path = Field(default=Path("./data/chroma"))
    chroma_collection_name: str = "documents"
    uploads_dir: Path = Field(default=Path("./data/uploads"))

    openai_api_key: str | None = None
    openai_embedding_model: str = "text-embedding-3-small"
    openai_chat_model: str = "gpt-4.1-mini"

    chunk_size: int = 350
    chunk_overlap: int = 60
    top_k_results: int = 4
    min_evidence_score: float = 0.35
    max_citation_excerpt_chars: int = 280
    log_level: str = "INFO"

    @property
    def database_url(self) -> str:
        database_path = self.sqlite_db_path.resolve().as_posix()
        return f"sqlite+pysqlite:///{database_path}"

    def ensure_directories(self) -> None:
        self.sqlite_db_path.parent.mkdir(parents=True, exist_ok=True)
        self.chroma_path.mkdir(parents=True, exist_ok=True)
        self.uploads_dir.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    return Settings()
