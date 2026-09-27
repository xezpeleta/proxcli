"""Tests for global-flag handling, --columns, and the first-run cheat sheet.

Covers the agent-discovery pain points: global flags must work after the
subcommand, --columns must not greedily eat the subcommand, and a zero-arg
invocation teaches the syntax instead of dumping the full help.
"""

from __future__ import annotations

import os
import subprocess
import sys

from proxmox.cli.main import _hoist_global_flags, _resolve_columns


def run_proxmox(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    entrypoint = os.path.join(project_root, ".venv", "bin", "proxmox")
    if os.path.exists(entrypoint):
        return subprocess.run([entrypoint, *args], capture_output=True, text=True, timeout=10, env=merged)
    return subprocess.run([sys.executable, "-m", "proxmox.cli.main", *args], capture_output=True, text=True, timeout=10, env=merged)


class TestHoistGlobalFlags:
    def test_moves_dry_run_before_resource(self):
        out = _hoist_global_flags(["vm", "list", "--dry-run"])
        assert out == ["--dry-run", "vm", "list"]

    def test_moves_value_flag_and_value_before_resource(self):
        out = _hoist_global_flags(["vm", "list", "--output", "yaml"])
        assert out == ["--output", "yaml", "vm", "list"]

    def test_handles_equals_form(self):
        out = _hoist_global_flags(["vm", "list", "--output=yaml"])
        assert out == ["--output=yaml", "vm", "list"]

    def test_columns_comma_form_before_resource(self):
        out = _hoist_global_flags(["vm", "list", "--columns", "vmid,name"])
        assert out == ["--columns", "vmid,name", "vm", "list"]

    def test_no_change_when_already_before(self):
        argv = ["--dry-run", "vm", "list"]
        assert _hoist_global_flags(argv) == argv

    def test_no_change_without_resource(self):
        argv = ["--dry-run", "--verbose"]
        assert _hoist_global_flags(argv) == argv

    def test_timeout_not_hoisted(self):
        """--timeout is shadowed by `task wait`/`vm agent exec` with different
        units, so it must NOT be hoisted (the subparser owns it)."""
        out = _hoist_global_flags(["task", "wait", "UPID:pve01:1", "--timeout", "1000"])
        assert out == ["task", "wait", "UPID:pve01:1", "--timeout", "1000"]

    def test_double_dash_preserves_positionals(self):
        """`--` and everything after is left untouched (vm agent exec)."""
        argv = ["vm", "agent", "exec", "100", "--shell", "--", "ls", "-la"]
        assert _hoist_global_flags(argv) == argv

    def test_subcommand_flags_not_hoisted(self):
        """Per-subcommand flags like --node stay where they are."""
        out = _hoist_global_flags(["vm", "list", "--node", "pve01"])
        assert out == ["vm", "list", "--node", "pve01"]


class TestResolveColumns:
    def test_comma_separated(self):
        ns = type("N", (), {"columns": "vmid,name,status"})()
        assert _resolve_columns(ns) == ["vmid", "name", "status"]

    def test_whitespace_separated(self):
        ns = type("N", (), {"columns": "vmid name status"})()
        assert _resolve_columns(ns) == ["vmid", "name", "status"]

    def test_none(self):
        ns = type("N", (), {"columns": None})()
        assert _resolve_columns(ns) is None

    def test_legacy_list_passthrough(self):
        ns = type("N", (), {"columns": ["vmid", "name"]})()
        assert _resolve_columns(ns) == ["vmid", "name"]


class TestCLIGlobalFlags:
    def test_no_args_prints_cheat_sheet(self):
        result = run_proxmox()
        assert result.returncode == 0
        # teaches the most common agent tasks, not the full --help dump
        assert "Common tasks" in result.stdout
        assert "vm list --name" in result.stdout
        assert "--dry-run" in result.stdout
        assert "--output yaml" in result.stdout

    def test_dry_run_after_subcommand_works(self, tmp_path):
        env = {"PROXMOX_CONFIG_DIR": str(tmp_path / "proxmox-cli")}
        result = run_proxmox(
            "--url", "https://pve:8006",
            "--api-token", "root@pam!t=abc",
            "vm", "list", "--dry-run",
            env=env,
        )
        assert result.returncode == 0
        assert "GET" in result.stdout

    def test_columns_after_subcommand_works(self, tmp_path):
        """The original footgun: `vm list --columns vmid name` failed. Now
        comma-separated --columns after the subcommand works."""
        env = {"PROXMOX_CONFIG_DIR": str(tmp_path / "proxmox-cli")}
        result = run_proxmox(
            "--url", "https://pve:8006",
            "--api-token", "root@pam!t=abc",
            "vm", "list", "--columns", "vmid,name", "--dry-run",
            env=env,
        )
        assert result.returncode == 0
        assert "GET" in result.stdout

    def test_proxcli_alias_runs(self):
        """The package name `proxcli` is also an installed binary."""
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        entrypoint = os.path.join(project_root, ".venv", "bin", "proxcli")
        if not os.path.exists(entrypoint):
            return  # alias not installed in this env; skip
        result = subprocess.run([entrypoint, "--version"], capture_output=True, text=True, timeout=10)
        assert result.returncode == 0
        assert "proxcli" in result.stdout

