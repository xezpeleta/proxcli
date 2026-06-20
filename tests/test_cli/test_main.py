"""Integration tests for CLI commands."""

from __future__ import annotations

import json
import subprocess
import sys


def run_proxmox(*args: str) -> subprocess.CompletedProcess:
    """Run the proxmox CLI and return the completed process."""
    return subprocess.run(
        [sys.executable, "-m", "proxmox.cli.main", *args],
        capture_output=True,
        text=True,
        timeout=10,
    )


class TestCLIAuth:
    def test_auth_clear_and_status(self, tmp_path, monkeypatch):
        """auth clear and auth status work without credentials."""
        # Override config dir
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        # Clear (should succeed even if nothing to clear)
        result = run_proxmox("auth", "clear")
        # Status should show not authenticated
        result = run_proxmox("auth", "status")
        data = json.loads(result.stdout)
        assert data["status"] == "not authenticated"

    def test_auth_login_missing_password(self, tmp_path, monkeypatch):
        """auth login fails without password or token."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "auth", "login",
            "--url", "https://pve:8006",
            "--username", "root@pam",
        )
        assert result.returncode != 0
        assert "password" in result.stderr.lower() or "required" in result.stderr.lower()


class TestCLIVM:
    def test_vm_dry_run(self, tmp_path, monkeypatch):
        """VM create --dry-run prints the request without contacting API."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--password", "test",
            "--dry-run",
            "vm", "create",
            "--node", "pve01",
            "--vmid", "100",
            "--memory", "2048",
        )
        assert result.returncode == 0
        assert "POST" in result.stdout
        assert "pve:8006" in result.stdout
        assert "vmid" in result.stdout
