"""Structured JSON logging configuration for observability."""
import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict
from backend.app.core.config import settings


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_payload: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno,
        }
        if hasattr(record, "agent"):
            log_payload["agent"] = record.agent
        if hasattr(record, "symbol"):
            log_payload["symbol"] = record.symbol
        if hasattr(record, "event"):
            log_payload["event"] = record.event
        if hasattr(record, "extra_data"):
            log_payload["extra_data"] = record.extra_data
        if record.exc_info:
            log_payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_payload)


def setup_logger(name: str = "algo_system") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        logger.propagate = False
    return logger


logger = setup_logger()
