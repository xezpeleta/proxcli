"""Unit tests for user CLI commands."""

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


class TestUserCLI:
    def test_user_list_dry_run(self, tmp_path, monkeypatch):
        """user list --dry-run prints the GET request."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "user", "list",
        )
        assert result.returncode == 0
        assert "GET" in result.stdout
        assert "access/users" in result.stdout

    def test_user_show_dry_run(self, tmp_path, monkeypatch):
        """user show --dry-run prints the GET request."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "user", "show", "testuser@pve",
        )
        assert result.returncode == 0
        assert "GET" in result.stdout
        assert "access/users/testuser@pve" in result.stdout

    def test_user_create_dry_run(self, tmp_path, monkeypatch):
        """user create --dry-run prints the POST request."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "user", "create", "newuser@pve",
            "--password", "Test123!",
            "--email", "test@example.com",
            "--firstname", "Test",
            "--lastname", "User",
        )
        assert result.returncode == 0
        assert "POST" in result.stdout
        assert "access/users" in result.stdout
        assert "newuser@pve" in result.stdout

    def test_user_create_with_groups(self, tmp_path, monkeypatch):
        """user create with --group combines into comma-separated string."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "user", "create", "newuser@pve",
            "--group", "Admin",
            "--group", "Users",
        )
        assert result.returncode == 0
        assert "Admin,Users" in result.stdout

    def test_user_create_disabled(self, tmp_path, monkeypatch):
        """user create --disable sends enable=0."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "user", "create", "disabled@pve",
            "--disable",
        )
        assert result.returncode == 0
        assert "'enable': 0" in result.stdout

    def test_user_update_dry_run(self, tmp_path, monkeypatch):
        """user update --dry-run prints the PUT request."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "user", "update", "testuser@pve",
            "--email", "new@example.com",
        )
        assert result.returncode == 0
        assert "PUT" in result.stdout
        assert "access/users/testuser@pve" in result.stdout

    def test_user_delete_dry_run(self, tmp_path, monkeypatch):
        """user delete --dry-run prints the DELETE request."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "user", "delete", "testuser@pve",
        )
        assert result.returncode == 0
        assert "DELETE" in result.stdout
        assert "access/users/testuser@pve" in result.stdout
