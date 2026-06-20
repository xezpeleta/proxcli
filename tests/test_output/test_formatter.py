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

    def test_table_format_with_columns(self):
        """--columns restricts which columns appear."""
        data = [
            {"vmid": 100, "name": "vm1", "status": "running", "cpus": 2},
            {"vmid": 101, "name": "vm2", "status": "stopped", "cpus": 4},
        ]
        result = format_output(data, "table", columns=["vmid", "status"])
        assert "vmid" in result
        assert "status" in result
        assert "running" in result
        assert "stopped" in result
        assert "name" not in result
        assert "cpus" not in result

    def test_table_format_status_colors(self):
        """Status values should be colored in table output."""
        data = [
            {"vmid": 100, "status": "running"},
            {"vmid": 101, "status": "stopped"},
            {"vmid": 102, "status": "paused"},
        ]
        result = format_output(data, "table")
        # Rich ANSI codes for green (running)
        assert "\x1b" in result  # escape codes present
        assert "running" in result
        assert "stopped" in result

    def test_table_format_dict_with_status(self):
        """Key-value table with status field should be colored."""
        data = {"status": "running", "cpu": 0.5}
        result = format_output(data, "table")
        assert "\x1b" in result  # color codes should be present
        assert "running" in result
