from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=4000)
    document_ids: list[str] = Field(default_factory=list)
    top_k: int = Field(default=5, ge=1, le=10)


class QuerySourceResponse(BaseModel):
    document_name: str
    page_number: int | None = None
    sheet_name: str | None = None
    excerpt: str


class AskResponse(BaseModel):
    answer: str
    confidence: float
    sources: list[QuerySourceResponse]
    retrieved_chunks: int
    latency_ms: int
