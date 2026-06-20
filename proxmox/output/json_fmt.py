"""JSON output formatter."""

from __future__ import annotations

import json
from typing import Any


def format_json(data: Any, indent: int = 2) -> str:
    """Render data as pretty-printed JSON."""
    return json.dumps(data, indent=indent, ensure_ascii=False, default=str)
