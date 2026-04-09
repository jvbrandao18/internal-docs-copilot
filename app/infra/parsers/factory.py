from collections.abc import Iterable

from app.core.exceptions import UnsupportedFileTypeError
from app.infra.parsers.base import DocumentParser


class ParserFactory:
    def __init__(self, parsers: Iterable[DocumentParser]) -> None:
        self.parsers = tuple(parsers)

    def get_parser(self, suffix: str) -> DocumentParser:
        normalized_suffix = suffix.lower()
        for parser in self.parsers:
            if normalized_suffix in parser.supported_suffixes:
                return parser
        raise UnsupportedFileTypeError(f"Unsupported file type: {suffix}")
