"""Table output formatter using rich."""

from __future__ import annotations

from typing import Any

from rich.console import Console
from rich.table import Table


def format_table(data: Any, columns: list[str] | None = None) -> str:
    """Render data as a rich-powered ASCII table.

    - list[dict]  → columnar table
    - dict        → key-value table
    - other       → plain string
    """
    console = Console(force_terminal=True, color_system=None, width=120)
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

    # Auto-detect columns from first item keys if not specified
    cols = columns or list(items[0].keys())
    table = Table(show_header=True, header_style="bold")
    for col in cols:
        table.add_column(col, overflow="fold")
    for item in items:
        table.add_row(*[str(item.get(col, "")) for col in cols])
    return table


def _kv_table(data: dict) -> Table:
    table = Table(show_header=True, header_style="bold")
    table.add_column("Key", style="dim")
    table.add_column("Value")
    for key, value in data.items():
        if isinstance(value, (dict, list)):
            import json

            value = json.dumps(value, default=str)
        table.add_row(str(key), str(value))
    return table


def _plain_table(data: Any) -> Table:
    table = Table()
    table.add_column("Result")
    table.add_row(str(data))
    return table
