"""Output formatter dispatcher."""

from __future__ import annotations

from typing import Any

from proxmox.output.json_fmt import format_json
from proxmox.output.table_fmt import format_table
from proxmox.output.yaml_fmt import format_yaml


def format_output(data: Any, fmt: str, *, columns: list[str] | None = None) -> str:
    """Dispatch to the appropriate formatter.

    Args:
        data: The data to format (dict, list, etc.)
        fmt: One of 'json', 'table', 'yaml'
        columns: Optional column name override for table mode.
    """
    if fmt == "json":
        return format_json(data)
    if fmt == "table":
        return format_table(data, columns)
    if fmt == "yaml":
        return format_yaml(data)
    return format_json(data)
