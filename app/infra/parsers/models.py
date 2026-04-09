from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ParsedRecord:
    content: str
    source_type: str
    page_number: int | None = None
    sheet_name: str | None = None
    row_start: int | None = None
    row_end: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ParsedDocumentResult:
    file_type: str
    records: list[ParsedRecord]
    page_count: int | None = None
    sheet_count: int | None = None
