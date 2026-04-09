from openai import OpenAI

from app.core.exceptions import ConfigurationError, ExternalServiceError


class EmbeddingsClient:
    def __init__(self, *, api_key: str | None, model: str) -> None:
        self.api_key = api_key
        self.model = model
        self._client: OpenAI | None = None

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        client = self._get_client()
        try:
            response = client.embeddings.create(
                model=self.model,
                input=texts,
            )
        except ConfigurationError:
            raise
        except Exception as exc:
            raise ExternalServiceError(
                "Failed to generate embeddings for the document content."
            ) from exc
        return [list(item.embedding) for item in response.data]

    def _get_client(self) -> OpenAI:
        if not self.api_key:
            raise ConfigurationError("OPENAI_API_KEY is not configured.")
        if self._client is None:
            self._client = OpenAI(api_key=self.api_key)
        return self._client
