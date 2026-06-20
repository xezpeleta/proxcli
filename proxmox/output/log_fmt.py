"""Log-line output formatter — timestamped log entries."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def format_log(data: Any) -> str:
    """Format log entries as plain text lines with timestamps.

    Detects lists of dicts with 'time' and 'msg' fields and formats them
    as human-readable log lines.  Falls back to JSON for non-log data.
    """
    if not isinstance(data, list):
        return _fallback(data)

    lines: list[str] = []
    for entry in data:
        if not isinstance(entry, dict):
            return _fallback(data)
        line = _format_log_line(entry)
        lines.append(line)

    return "\n".join(lines)


def _format_log_line(entry: dict) -> str:
    """Format a single log entry as a line."""
    # Timestamp
    ts = entry.get("time", "")
    ts_str = _format_ts(ts)

    # Source (node, service tag)
    parts = [ts_str]

    node = entry.get("node", "")
    tag = entry.get("tag", "")
    if tag:
        parts.append(f"[{tag}]")
    if node:
        parts.append(f"[{node}]")

    # Message
    msg = entry.get("msg", "")
    parts.append(msg)

    return " ".join(parts)


def _format_ts(value: Any) -> str:
    """Format a timestamp value as human-readable."""
    if isinstance(value, (int, float)):
        try:
            dt = datetime.fromtimestamp(value, tz=timezone.utc)
            return dt.strftime("%Y-%m-%dT%H:%M:%S")
        except (OSError, ValueError):
            return str(value)
    if isinstance(value, str):
        # Already an ISO string or similar
        return value
    return str(value)


def _fallback(data: Any) -> str:
    """Fallback to JSON for non-log data."""
    import json

    return json.dumps(data, indent=2, default=str)
