from __future__ import annotations

import logging
from typing import Any

from rich.console import Console
from rich.logging import RichHandler

CONSOLE = Console(stderr=True)


def setup_logging():
    root = logging.getLogger()
    root.setLevel(logging.WARNING)
    for h in list(root.handlers):
        root.removeHandler(h)

    rich_logger = logging.getLogger('rich')
    rich_logger.setLevel(logging.DEBUG)
    rich_logger.propagate = False
    rich_logger.handlers.clear()

    formatter = logging.Formatter('%(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    handler = RichHandler(rich_tracebacks=True, console=CONSOLE)
    handler.setFormatter(formatter)
    rich_logger.addHandler(handler)
    return rich_logger


def is_nan(value: Any) -> bool:
    return value != value  # NaN is the only value that is not equal to itself
