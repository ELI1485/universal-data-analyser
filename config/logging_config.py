"""Logging configuration for Universal Data Analyzer.

Configures Python logging with:
- 3 rotating file handlers: app.log (INFO+), error.log (ERROR+), audit.log (INFO+)
- 1 stream handler for console (DEBUG in dev, INFO in prod)
- Max file size: 10 MB, keep 5 backups
- Format: [%(asctime)s] [%(levelname)s] [%(name)s] %(message)s
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


_LOG_FORMAT = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
_BACKUP_COUNT = 5

_audit_logger: logging.Logger | None = None


def setup_logging(log_dir: str = "./logs", log_level: str = "INFO") -> None:
    """Configure the application logging system.

    Args:
        log_dir: Directory path where log files will be stored.
        log_level: The base log level (INFO, DEBUG, WARNING, ERROR).
    """
    global _audit_logger

    # Ensure log directory exists
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # Determine numeric log level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Clear existing handlers to avoid duplicates on re-init
    root_logger.handlers.clear()

    formatter = logging.Formatter(_LOG_FORMAT)

    # --- Console Handler ---
    console_handler = logging.StreamHandler(sys.stdout)
    is_dev = os.getenv("ENV", "development").lower() == "development"
    console_handler.setLevel(logging.DEBUG if is_dev else logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # --- App Log Handler (INFO+) ---
    app_log_path = log_path / "app.log"
    app_handler = RotatingFileHandler(
        filename=str(app_log_path),
        maxBytes=_MAX_BYTES,
        backupCount=_BACKUP_COUNT,
        encoding="utf-8",
    )
    app_handler.setLevel(logging.INFO)
    app_handler.setFormatter(formatter)
    root_logger.addHandler(app_handler)

    # --- Error Log Handler (ERROR+) ---
    error_log_path = log_path / "error.log"
    error_handler = RotatingFileHandler(
        filename=str(error_log_path),
        maxBytes=_MAX_BYTES,
        backupCount=_BACKUP_COUNT,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    root_logger.addHandler(error_handler)

    # --- Audit Log Handler (INFO+ for audit events only) ---
    audit_log_path = log_path / "audit.log"
    audit_handler = RotatingFileHandler(
        filename=str(audit_log_path),
        maxBytes=_MAX_BYTES,
        backupCount=_BACKUP_COUNT,
        encoding="utf-8",
    )
    audit_handler.setLevel(logging.INFO)
    audit_handler.setFormatter(formatter)

    # Create dedicated audit logger
    _audit_logger = logging.getLogger("audit")
    _audit_logger.handlers.clear()
    _audit_logger.addHandler(audit_handler)
    _audit_logger.addHandler(console_handler)
    _audit_logger.setLevel(logging.INFO)
    _audit_logger.propagate = False

    logging.getLogger(__name__).info(
        "Logging configuré — niveau: %s, répertoire: %s", log_level, log_dir
    )


def get_audit_logger() -> logging.Logger:
    """Get the dedicated audit logger instance.

    Returns:
        The audit logger. If setup_logging() hasn't been called yet,
        returns a basic logger with the name 'audit'.
    """
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = logging.getLogger("audit")
    return _audit_logger
