"""Structured stderr logging."""

from __future__ import annotations

import sys


def log_error(message: str) -> None:
    """Print an error message to stderr."""
    print(f"Error: {message}", file=sys.stderr)


def log_info(message: str) -> None:
    """Print an info message to stderr."""
    print(message, file=sys.stderr)
