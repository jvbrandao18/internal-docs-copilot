from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(min_length=5, max_length=4000)
    top_k: int = Field(default=4, ge=1, le=10)
    document_ids: list[str] | None = None


class Citation(BaseModel):
    document_id: str
    filename: str
    chunk_id: str
    source_label: str
    excerpt: str
    score: float


class AskResponse(BaseModel):
    query_id: str
    answer: str
    confidence: float
    refused: bool
    refusal_reason: str | None = None
    citations: list[Citation]
