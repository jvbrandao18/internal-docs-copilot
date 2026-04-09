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
    app_debug: bool = False
    sqlite_url: str = "sqlite+pysqlite:///./data/internal_docs_copilot.db"
    openai_api_key: str | None = None
    openai_chat_model: str = "gpt-4.1-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    chroma_persist_dir: Path = Field(default=Path("./data/chroma"))
    upload_dir: Path = Field(default=Path("./data/uploads"))
    log_level: str = "INFO"
    pdf_chunk_size: int = 800
    pdf_chunk_overlap: int = 120
    default_top_k: int = 5
    min_evidence_score: float = 0.25

    def ensure_directories(self) -> None:
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.chroma_persist_dir.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    return Settings()
