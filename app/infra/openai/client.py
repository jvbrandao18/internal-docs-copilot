import json
from typing import Any

from openai import OpenAI

from app.core.exceptions import ConfigurationError, ExternalServiceError
from app.infra.vector.chroma_store import RetrievedChunk


class OpenAIClient:
    def __init__(self, *, api_key: str | None, embedding_model: str, chat_model: str) -> None:
        self.api_key = api_key
        self.embedding_model = embedding_model
        self.chat_model = chat_model
        self._client: OpenAI | None = None

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        try:
            response = self._get_client().embeddings.create(
                model=self.embedding_model,
                input=texts,
            )
        except Exception as exc:
            raise ExternalServiceError("Embedding generation failed.") from exc

        return [list(item.embedding) for item in response.data]

    def answer_question(self, *, question: str, evidence: list[RetrievedChunk]) -> dict[str, Any]:
        evidence_blocks = []
        for index, chunk in enumerate(evidence, start=1):
            source_label = chunk.metadata.get("source_label", "unknown source")
            filename = chunk.metadata.get("filename", "unknown file")
            evidence_blocks.append(
                f"[{index}] {filename} | {source_label}\n{chunk.text[:1400].strip()}"
            )

        prompt = f"""
Return only valid JSON using this schema:
{{
  "answer": "string",
  "refused": false,
  "refusal_reason": null,
  "confidence": 0.0
}}

Rules:
- Answer only from the evidence provided below.
- If the evidence is missing, weak or contradictory, set "refused" to true.
- Never invent facts, citations or policy details.
- Keep the answer concise and grounded.

Question:
{question}

Evidence:
{chr(10).join(evidence_blocks)}
""".strip()

        try:
            response = self._get_client().responses.create(
                model=self.chat_model,
                input=prompt,
            )
        except Exception as exc:
            raise ExternalServiceError("Answer generation failed.") from exc

        raw_text = self._extract_output_text(response)
        return self._normalize_answer(raw_text)

    def _get_client(self) -> OpenAI:
        if not self.api_key:
            raise ConfigurationError("OPENAI_API_KEY is not configured.")
        if self._client is None:
            self._client = OpenAI(api_key=self.api_key)
        return self._client

    def _extract_output_text(self, response: Any) -> str:
        output_text = getattr(response, "output_text", None)
        if output_text:
            return str(output_text).strip()

        chunks: list[str] = []
        for output_item in getattr(response, "output", []) or []:
            content_items = getattr(output_item, "content", None)
            if content_items is None and isinstance(output_item, dict):
                content_items = output_item.get("content", [])
            for content_item in content_items or []:
                text = getattr(content_item, "text", None)
                if text is None and isinstance(content_item, dict):
                    text = content_item.get("text")
                if text:
                    chunks.append(str(text))
        return "\n".join(chunks).strip()

    def _normalize_answer(self, raw_text: str) -> dict[str, Any]:
        if not raw_text:
            return {
                "answer": "",
                "refused": True,
                "refusal_reason": "The language model did not return a grounded answer.",
                "confidence": 0.0,
            }

        try:
            payload = json.loads(raw_text)
        except json.JSONDecodeError:
            return {
                "answer": raw_text,
                "refused": False,
                "refusal_reason": None,
                "confidence": 0.5,
            }

        return {
            "answer": str(payload.get("answer", "")).strip(),
            "refused": bool(payload.get("refused", False)),
            "refusal_reason": payload.get("refusal_reason"),
            "confidence": self._clamp_confidence(payload.get("confidence")),
        }

    @staticmethod
    def _clamp_confidence(value: Any) -> float:
        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            return 0.0
        return max(0.0, min(1.0, numeric_value))
