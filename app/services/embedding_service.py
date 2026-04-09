from app.infra.llm.embeddings_client import EmbeddingsClient


class EmbeddingService:
    def __init__(self, embeddings_client: EmbeddingsClient) -> None:
        self.embeddings_client = embeddings_client

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return self.embeddings_client.embed_texts(texts)
