"""Table output formatter using rich."""

from __future__ import annotations

from typing import Any

from rich.console import Console
from rich.style import Style
from rich.table import Table
from rich.text import Text

# Status values that get colored when they appear in any column
_STATUS_COLORS: dict[str, str] = {
    "running": "bold green",
    "stopped": "dim red",
    "paused": "yellow",
    "suspended": "yellow",
    "active": "bold green",
    "inactive": "dim red",
    "ok": "green",
    "error": "bold red",
    "failed": "bold red",
    "warning": "yellow",
    "online": "bold green",
    "offline": "dim red",
    "available": "green",
    "unavailable": "red",
    "enabled": "green",
    "disabled": "dim red",
    "quorate": "green",
    "yes": "green",
    "no": "dim red",
    "true": "green",
    "false": "dim red",
    "healthy": "green",
    "START": "green",
    "STOP": "red",
    "TASK OK": "bold green",
}


def format_table(data: Any, columns: list[str] | None = None) -> str:
    """Render data as a rich-powered ASCII table.

    - list[dict]  → columnar table
    - dict        → key-value table
    - other       → plain string
    """
    console = Console(force_terminal=True, width=120)
    table = _build_table(data, columns)
    with console.capture() as capture:
        console.print(table)
    return capture.get().rstrip()


def _build_table(data: Any, columns: list[str] | None) -> Table:
    if isinstance(data, list):
        return _list_table(data, columns)
    if isinstance(data, dict):
        return _kv_table(data)
    return _plain_table(data)


def _list_table(items: list[dict], columns: list[str] | None) -> Table:
    if not items:
        return Table(title="No results")

    # Determine which columns are status-like (case-insensitive check)
    status_cols = _find_status_columns(items[0])

    # Auto-detect columns from first item keys if not specified
    cols = columns or list(items[0].keys())
    table = Table(show_header=True, header_style="bold")
    for col in cols:
        table.add_column(col, overflow="fold")

    for item in items:
        row_values: list[Text | str] = []
        for col in cols:
            raw = str(item.get(col, ""))
            if col in status_cols:
                row_values.append(_colorize_status(raw))
            else:
                row_values.append(raw)
        table.add_row(*row_values)
    return table


def _find_status_columns(first_item: dict) -> set[str]:
    """Detect columns likely to contain status/state values."""
    status_names = {"status", "state", "running", "active", "health",
                    "exitstatus", "lock", "template", "quorate"}
    return {k for k in first_item if k.lower() in status_names}


def _kv_table(data: dict) -> Table:
    table = Table(show_header=True, header_style="bold")
    table.add_column("Key", style="dim")
    table.add_column("Value")
    for key, value in data.items():
        if isinstance(value, (dict, list)):
            import json

            value = json.dumps(value, default=str)
        rendered_value: Text | str
        if key in {"status", "state", "exitstatus", "running", "lock"}:
            rendered_value = _colorize_status(str(value))
        else:
            rendered_value = str(value)
        table.add_row(str(key), rendered_value)
    return table


def _colorize_status(value: str) -> Text:
    """Apply color to a status/state value."""
    lower = value.lower().strip()
    for pattern, style_str in _STATUS_COLORS.items():
        if lower == pattern:
            return Text(value, style=Style.parse(style_str))
    return Text(value)


def _plain_table(data: Any) -> Table:
    table = Table()
    table.add_column("Result")
    table.add_row(str(data))
    return table
