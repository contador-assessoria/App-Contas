"""Simple logging helpers for the UI layer."""

from __future__ import annotations

import logging
from pathlib import Path

from .helpers import ensure_app_dir


def get_logger(name: str = "app") -> logging.Logger:
    """Return a configured :class:`logging.Logger` instance.

    The first time this function is called a log file is created inside the
    application data directory.  Subsequent calls return the same configured
    logger.
    """

    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    log_dir = Path(ensure_app_dir())
    log_file = log_dir / "app.log"

    handler = logging.FileHandler(log_file, encoding="utf-8")
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    return logger


__all__ = ["get_logger"]
