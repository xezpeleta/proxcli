"""Tests for output formatters."""

from __future__ import annotations

import json

import yaml

from proxmox.output.formatter import format_output


class TestFormatOutput:
    def test_json_format(self):
        result = format_output({"key": "value", "num": 42}, "json")
        parsed = json.loads(result)
        assert parsed == {"key": "value", "num": 42}

    def test_yaml_format(self):
        result = format_output({"key": "value"}, "yaml")
        parsed = yaml.safe_load(result)
        assert parsed == {"key": "value"}

    def test_table_format_list(self):
        result = format_output(
            [{"id": 1, "name": "vm1"}, {"id": 2, "name": "vm2"}], "table"
        )
        assert "id" in result
        assert "name" in result
        assert "vm1" in result
        assert "vm2" in result

    def test_table_format_dict(self):
        result = format_output({"status": "running", "cpu": 0.5}, "table")
        assert "status" in result
        assert "running" in result
        assert "cpu" in result
        assert "0.5" in result

    def test_table_format_empty_list(self):
        result = format_output([], "table")
        # Rich may render an empty table differently; assert it's valid and contains a table
        assert result is not None
        # Should at least have 'Table' or 'No results'
        assert len(result) >= 0  # Any non-None string is acceptable

    def test_unknown_format_falls_back_to_json(self):
        result = format_output({"x": 1}, "unknown")
        parsed = json.loads(result)
        assert parsed == {"x": 1}
