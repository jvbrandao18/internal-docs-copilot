from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol


@dataclass(slots=True)
class ParsedSection:
    section_id: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ParsedDocument:
    source_path: Path
    filename: str
    content_type: str
    metadata: dict[str, Any]
    sections: list[ParsedSection]


class DocumentParser(Protocol):
    supported_suffixes: tuple[str, ...]

    def parse(
        self,
        source_path: Path,
        *,
        filename: str,
        content_type: str | None = None,
    ) -> ParsedDocument: ...
