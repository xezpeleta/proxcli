"""YAML output formatter."""

from __future__ import annotations

from typing import Any

import yaml


def format_yaml(data: Any) -> str:
    """Render data as YAML."""
    return yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True)
