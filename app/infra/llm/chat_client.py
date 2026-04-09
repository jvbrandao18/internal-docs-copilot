import json
from typing import Any

from openai import OpenAI

from app.core.exceptions import ConfigurationError, ExternalServiceError


class ChatClient:
    def __init__(self, *, api_key: str | None, model: str) -> None:
        self.api_key = api_key
        self.model = model
        self._client: OpenAI | None = None

    def answer_with_evidence(
        self,
        *,
        question: str,
        evidence_blocks: list[str],
    ) -> dict[str, Any]:
        client = self._get_client()
        try:
            response = client.chat.completions.create(
                model=self.model,
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Answer only from the supplied evidence. "
                            "If the evidence is insufficient or irrelevant, refuse safely. "
                            "Return JSON with keys: answer, confidence, refused, refusal_reason."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Question:\n{question}\n\n"
                            f"Evidence:\n{chr(10).join(evidence_blocks)}"
                        ),
                    },
                ],
            )
        except ConfigurationError:
            raise
        except Exception as exc:
            raise ExternalServiceError(
                "Failed to generate an answer from the retrieved evidence."
            ) from exc

        content = response.choices[0].message.content or "{}"
        try:
            payload = json.loads(content)
        except json.JSONDecodeError:
            payload = {
                "answer": "",
                "confidence": 0.0,
                "refused": True,
                "refusal_reason": "Model response was not valid JSON.",
            }
        return payload

    def _get_client(self) -> OpenAI:
        if not self.api_key:
            raise ConfigurationError("OPENAI_API_KEY is not configured.")
        if self._client is None:
            self._client = OpenAI(api_key=self.api_key)
        return self._client
