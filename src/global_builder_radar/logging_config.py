"""Structured logging configuration.

Configuration:
- GBR_LOG_LEVEL controls the minimum log level.
- Logs are emitted as stable key=value records for local and background execution.
"""

from __future__ import annotations

import logging
import os


def configure_logging() -> None:
    level = os.getenv("GBR_LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format=(
            "timestamp=%(asctime)s level=%(levelname)s logger=%(name)s "
            "message=%(message)s"
        ),
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )
