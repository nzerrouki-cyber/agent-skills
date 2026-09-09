# utils/logger.py
import json
import logging
import sys
from datetime import datetime, timezone


class StructuredJsonFormatter(logging.Formatter):
    """Formats Python log records into GCP Cloud Logging compatible JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "severity": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "logging.googleapis.com/labels": {
                "python_module": record.module,
                "function_name": record.funcName,
            },
        }

        # Attach extra structured fields if passed via extra={"extra_data": ...}
        if hasattr(record, "extra") and isinstance(record.extra, dict):
            log_entry.update(record.extra)

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


def setup_logger(name: str = "enterprise_agentic_workflow", level: int = logging.INFO) -> logging.Logger:
    """Configures and returns a structured logger for GKE stdout/stderr ingestion."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredJsonFormatter())
        logger.addHandler(handler)
        logger.propagate = False

    return logger


# Instantiate global logger for module imports across agents and services
logger = setup_logger()