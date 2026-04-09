import hashlib
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


class FakeEmbeddingsClient:
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * 16
        for token in re.findall(r"[a-zA-Z0-9_]+", text.lower()):
            bucket = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16) % len(vector)
            vector[bucket] += 1.0
        return vector


class FakeChatClient:
    def answer_with_evidence(
        self,
        *,
        question: str,
        evidence_blocks: list[str],
    ) -> dict[str, object]:
        if not evidence_blocks:
            return {
                "answer": "",
                "confidence": 0.0,
                "refused": True,
                "refusal_reason": "Insufficient evidence",
            }
        excerpt = evidence_blocks[0].splitlines()[-1].strip()
        return {
            "answer": excerpt[:180],
            "confidence": 0.82,
            "refused": False,
            "refusal_reason": None,
        }


@pytest.fixture
def test_settings(tmp_path: Path) -> Settings:
    return Settings(
        app_name="internal-docs-copilot",
        app_env="test",
        app_debug=False,
        sqlite_url=f"sqlite+pysqlite:///{(tmp_path / 'test.db').as_posix()}",
        openai_api_key="test-key",
        openai_chat_model="fake-chat",
        openai_embedding_model="fake-embedding",
        chroma_persist_dir=tmp_path / "chroma",
        upload_dir=tmp_path / "uploads",
        log_level="INFO",
        pdf_chunk_size=120,
        pdf_chunk_overlap=20,
        default_top_k=5,
        min_evidence_score=0.05,
    )


@pytest.fixture
def client(test_settings: Settings) -> TestClient:
    app = create_app(
        settings=test_settings,
        embeddings_client=FakeEmbeddingsClient(),
        chat_client=FakeChatClient(),
    )
    with TestClient(app) as test_client:
        yield test_client
