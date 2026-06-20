"""Unit tests for role and ACL CLI commands."""

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


class TestRoleCLI:
    def test_role_list_dry_run(self, tmp_path, monkeypatch):
        """role list --dry-run prints the GET request."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "role", "list",
        )
        assert result.returncode == 0
        assert "GET" in result.stdout
        assert "access/roles" in result.stdout

    def test_role_show_dry_run(self, tmp_path, monkeypatch):
        """role show --dry-run prints the GET request."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "role", "show", "PVEVMAdmin",
        )
        assert result.returncode == 0
        assert "GET" in result.stdout
        assert "access/roles/PVEVMAdmin" in result.stdout

    def test_role_create_dry_run(self, tmp_path, monkeypatch):
        """role create --dry-run prints the POST request."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "role", "create", "CustomRole",
            "--privs", "VM.Audit,VM.PowerMgmt,Datastore.Audit",
        )
        assert result.returncode == 0
        assert "POST" in result.stdout
        assert "access/roles" in result.stdout
        assert "CustomRole" in result.stdout

    def test_role_update_dry_run(self, tmp_path, monkeypatch):
        """role update --dry-run prints the PUT request."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "role", "update", "CustomRole",
            "--privs", "VM.Audit,Sys.Audit",
        )
        assert result.returncode == 0
        assert "PUT" in result.stdout
        assert "access/roles/CustomRole" in result.stdout

    def test_role_delete_dry_run(self, tmp_path, monkeypatch):
        """role delete --dry-run prints the DELETE request."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "role", "delete", "CustomRole",
        )
        assert result.returncode == 0
        assert "DELETE" in result.stdout
        assert "access/roles/CustomRole" in result.stdout


class TestACLCLI:
    def test_acl_list_dry_run(self, tmp_path, monkeypatch):
        """acl list --dry-run prints the GET request."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "acl", "list",
        )
        assert result.returncode == 0
        assert "GET" in result.stdout
        assert "access/acl" in result.stdout

    def test_acl_show_dry_run(self, tmp_path, monkeypatch):
        """acl show --dry-run prints the GET request with path param."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "acl", "show", "/vms/100",
        )
        assert result.returncode == 0
        assert "GET" in result.stdout
        assert "access/acl" in result.stdout

    def test_acl_add_dry_run(self, tmp_path, monkeypatch):
        """acl add --dry-run prints the PUT request."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "acl", "add", "/vms",
            "--roles", "PVEVMUser",
            "--users", "testuser@pve",
        )
        assert result.returncode == 0
        assert "PUT" in result.stdout
        assert "access/acl" in result.stdout
        assert "PVEVMUser" in result.stdout

    def test_acl_add_with_groups(self, tmp_path, monkeypatch):
        """acl add with --groups."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "acl", "add", "/pool/mypool",
            "--roles", "PVEPoolAdmin",
            "--groups", "Admin",
        )
        assert result.returncode == 0
        assert "PUT" in result.stdout

    def test_acl_add_no_propagate(self, tmp_path, monkeypatch):
        """acl add with --no-propagate sends propagate=0."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "acl", "add", "/vms",
            "--roles", "PVEAuditor",
            "--users", "auditor@pve",
            "--no-propagate",
        )
        assert result.returncode == 0
        assert "'propagate': 0" in result.stdout

    def test_acl_add_with_tokens(self, tmp_path, monkeypatch):
        """acl add with --tokens."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "acl", "add", "/",
            "--roles", "PVEAdmin",
            "--tokens", "xezpeleta@pve!proxcli",
        )
        assert result.returncode == 0
        assert "PUT" in result.stdout

    def test_acl_delete_dry_run(self, tmp_path, monkeypatch):
        """acl delete --dry-run sends delete=1 in the body."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "acl", "delete", "/vms",
            "--roles", "PVEVMUser",
            "--users", "testuser@pve",
        )
        assert result.returncode == 0
        assert "PUT" in result.stdout
        assert "'delete': 1" in result.stdout
