"""Utilities for configuring service logging."""

from __future__ import annotations

import logging
import sys
from typing import Optional


def configure_logging(level: int = logging.INFO, *, log_format: Optional[str] = None) -> None:
    """Configure global logging defaults for the ETL service."""

    logging.basicConfig(
        level=level,
        format=log_format
        or "%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )
