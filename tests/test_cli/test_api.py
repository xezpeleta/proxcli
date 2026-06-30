"""Unit tests for api CLI command."""

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


class TestAPICLI:
    def test_api_get_dry_run(self, tmp_path, monkeypatch):
        """api GET does a dry-run."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "api", "GET", "/nodes/pve01/status",
        )
        assert result.returncode == 0
        assert "GET" in result.stdout
        assert "/api2/json/nodes/pve01/status" in result.stdout

    def test_api_put_dry_run(self, tmp_path, monkeypatch):
        """api PUT with --data does a dry-run."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "api", "PUT", "/nodes/pve01/qemu/100/config",
            "--data", '{"memory": 4096}',
        )
        assert result.returncode == 0
        assert "PUT" in result.stdout
        assert "/api2/json/nodes/pve01/qemu/100/config" in result.stdout
        assert "memory" in result.stdout

    def test_api_strips_prefix(self, tmp_path, monkeypatch):
        """api strips /api2/json prefix if present."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "api", "GET", "/api2/json/nodes/pve01/status",
        )
        assert result.returncode == 0
        # Should not double-prefix
        assert "/api2/json/api2/json" not in result.stdout
        assert "/api2/json/nodes/pve01/status" in result.stdout

    def test_api_post_dry_run(self, tmp_path, monkeypatch):
        """api POST with --data."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "api", "POST", "/nodes/pve01/qemu",
            "--data", '{"vmid": 200, "name": "test-vm"}',
        )
        assert result.returncode == 0
        assert "POST" in result.stdout
        assert "vmid" in result.stdout
        assert "test-vm" in result.stdout

    def test_api_delete_dry_run(self, tmp_path, monkeypatch):
        """api DELETE."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "api", "DELETE", "/nodes/pve01/qemu/200",
        )
        assert result.returncode == 0
        assert "DELETE" in result.stdout

    def test_api_invalid_json(self, tmp_path, monkeypatch):
        """api with invalid --data returns error."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "api", "PUT", "/nodes/pve01/qemu/100/config",
            "--data", "not json",
        )
        assert "Invalid JSON" in result.stdout or "error" in result.stdout
