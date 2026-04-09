import re
from dataclasses import dataclass

from app.infra.llm.chat_client import ChatClient
from app.infra.vectorstore.chroma_store import RetrievedChunk


@dataclass(slots=True)
class AnswerResult:
    answer: str
    confidence: float
    refused: bool
    refusal_reason: str | None


class AnswerService:
    def __init__(
        self,
        *,
        chat_client: ChatClient,
        min_evidence_score: float,
    ) -> None:
        self.chat_client = chat_client
        self.min_evidence_score = min_evidence_score

    def answer(self, *, question: str, retrieved_chunks: list[RetrievedChunk]) -> AnswerResult:
        relevant_chunks = self._select_relevant_chunks(question, retrieved_chunks)
        evidence_score = self._calculate_evidence_score(relevant_chunks)
        if not relevant_chunks or evidence_score < self.min_evidence_score:
            return AnswerResult(
                answer="I do not have enough evidence in the indexed documents to answer safely.",
                confidence=round(evidence_score, 2),
                refused=True,
                refusal_reason="Insufficient evidence",
            )

        evidence_blocks = [
            (
                f"[{index}] document={chunk.metadata.get('document_name')} "
                f"page={chunk.metadata.get('page_number')} "
                f"sheet={chunk.metadata.get('sheet_name')}\n"
                f"{chunk.content}"
            )
            for index, chunk in enumerate(relevant_chunks, start=1)
        ]
        payload = self.chat_client.answer_with_evidence(
            question=question,
            evidence_blocks=evidence_blocks,
        )

        model_confidence = self._clamp_confidence(payload.get("confidence"))
        final_confidence = (
            evidence_score if model_confidence == 0 else min(evidence_score, model_confidence)
        )
        refused = bool(payload.get("refused", False))
        answer = str(payload.get("answer", "")).strip()
        refusal_reason = payload.get("refusal_reason")

        if refused and not answer:
            answer = "I do not have enough evidence in the indexed documents to answer safely."
        if not refused and not answer:
            answer = "No grounded answer was generated."

        return AnswerResult(
            answer=answer,
            confidence=round(final_confidence, 2),
            refused=refused,
            refusal_reason=refusal_reason,
        )

    def _select_relevant_chunks(
        self,
        question: str,
        retrieved_chunks: list[RetrievedChunk],
    ) -> list[RetrievedChunk]:
        filtered_by_score = [chunk for chunk in retrieved_chunks if chunk.score >= 0.15]
        if not filtered_by_score:
            return []

        keywords = {
            token
            for token in re.findall(r"[a-zA-Z0-9_]{4,}", question.lower())
            if token not in {"what", "with", "from", "that", "this", "have"}
        }
        if not keywords:
            return filtered_by_score

        keyword_matches = [
            chunk
            for chunk in filtered_by_score
            if any(keyword in chunk.content.lower() for keyword in keywords)
        ]
        return keyword_matches

    @staticmethod
    def _calculate_evidence_score(retrieved_chunks: list[RetrievedChunk]) -> float:
        if not retrieved_chunks:
            return 0.0
        return round(sum(chunk.score for chunk in retrieved_chunks) / len(retrieved_chunks), 4)

    @staticmethod
    def _clamp_confidence(value: object) -> float:
        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            return 0.0
        return max(0.0, min(1.0, numeric_value))
