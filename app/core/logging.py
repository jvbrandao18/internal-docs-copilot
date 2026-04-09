import json
import logging
from datetime import UTC, datetime
from typing import Any

_STANDARD_LOG_RECORD_FIELDS = {
    "args",
    "asctime",
    "created",
    "exc_info",
    "exc_text",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "module",
    "msecs",
    "message",
    "msg",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "thread",
    "threadName",
}


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "event": getattr(record, "event", record.getMessage()),
            "document_id": getattr(record, "document_id", None),
            "query_id": getattr(record, "query_id", None),
            "filename": getattr(record, "log_filename", None),
            "file_type": getattr(record, "file_type", None),
            "status": getattr(record, "status", None),
            "latency_ms": getattr(record, "latency_ms", None),
            "details": getattr(record, "details", None),
        }
        extras = {
            key: value
            for key, value in record.__dict__.items()
            if key not in _STANDARD_LOG_RECORD_FIELDS and not key.startswith("_")
        }
        payload.update(extras)
        if record.exc_info:
            payload["details"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=True, default=str)


def configure_logging(log_level: str) -> None:
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(log_level.upper())

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root_logger.addHandler(handler)

    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()
        logger.propagate = True


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def log_event(logger: logging.Logger, event: str, **fields: Any) -> None:
    safe_fields = dict(fields)
    if "filename" in safe_fields:
        safe_fields["log_filename"] = safe_fields.pop("filename")
    logger.info(event, extra={"event": event, **safe_fields})
