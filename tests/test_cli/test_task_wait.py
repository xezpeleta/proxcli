"""Unit tests for task wait CLI command."""

from __future__ import annotations

import os
import subprocess
import sys


def run_proxmox(*args: str) -> subprocess.CompletedProcess:
    """Run the proxmox CLI and return the completed process."""
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    entrypoint = os.path.join(project_root, ".venv", "bin", "proxmox")
    if os.path.exists(entrypoint):
        return subprocess.run(
            [entrypoint, *args],
            capture_output=True,
            text=True,
            timeout=10,
        )
    return subprocess.run(
        [sys.executable, "-m", "proxmox.cli.main", *args],
        capture_output=True,
        text=True,
        timeout=10,
    )


class TestTaskWaitCLI:
    def test_task_wait_dry_run(self, tmp_path, monkeypatch):
        """task wait does a GET dry-run to task status."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        upid = "UPID:pve01:00000001:00000001:00000001:vzdump::root@pam:"
        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "task", "wait", upid,
            "--timeout", "1000",
            "--poll", "100",
        )
        assert result.returncode == 0
        assert "GET" in result.stdout
        assert "/status" in result.stdout
        assert "pve01" in result.stdout
