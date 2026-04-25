import json
import logging
import sys
import time
from typing import Any

class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        for key, value in record.__dict__.items():
            if key not in {
                "args", "created", "exc_info", "exc_text", "filename",
                "funcName", "levelname", "levelno", "lineno", "message",
                "module", "msecs", "msg", "name", "pathname", "process",
                "processName", "relativeCreated", "stack_info", "taskName",
                "thread", "threadName",
            }:
                payload[key] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)

def _build_handler() -> logging.StreamHandler:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_JsonFormatter())
    return handler

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.addHandler(_build_handler())
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger

def log_request(
    logger: logging.Logger,
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    client_ip: str,
    extra: dict[str, Any] | None = None,
) -> None:
    fields: dict[str, Any] = {
        "event": "http_request",
        "method": method,
        "path": path,
        "status_code": status_code,
        "duration_ms": round(duration_ms, 2),
        "client_ip": client_ip,
    }
    if extra:
        fields.update(extra)
    logger.info("HTTP request", extra=fields)

def log_tool_call(
    logger: logging.Logger,
    tool_name: str,
    tool_input: dict[str, Any],
    success: bool,
    duration_ms: float,
) -> None:
    logger.info(
        "Tool call",
        extra={
            "event": "tool_call",
            "tool_name": tool_name,
            "tool_input": tool_input,
            "success": success,
            "duration_ms": round(duration_ms, 2),
        },
    )
