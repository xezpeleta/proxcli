"""Unit tests for VM agent subcommands (osinfo, fsinfo, users, exec)."""

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


class TestVMAgentOsinfoCLI:
    def test_vm_agent_osinfo_dry_run(self, tmp_path, monkeypatch):
        """vm agent osinfo does a GET dry-run."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "vm", "agent", "osinfo", "100",
            "--node", "pve01",
        )
        assert result.returncode == 0
        assert "GET" in result.stdout
        assert "agent/get-osinfo" in result.stdout


class TestVMAgentFsinfoCLI:
    def test_vm_agent_fsinfo_dry_run(self, tmp_path, monkeypatch):
        """vm agent fsinfo does a GET dry-run."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "vm", "agent", "fsinfo", "100",
            "--node", "pve01",
        )
        assert result.returncode == 0
        assert "GET" in result.stdout
        assert "agent/get-fsinfo" in result.stdout


class TestVMAgentUsersCLI:
    def test_vm_agent_users_dry_run(self, tmp_path, monkeypatch):
        """vm agent users does a GET dry-run."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "vm", "agent", "users", "100",
            "--node", "pve01",
        )
        assert result.returncode == 0
        assert "GET" in result.stdout
        assert "agent/get-users" in result.stdout


class TestVMAgentExecCLI:
    def test_vm_agent_exec_dry_run(self, tmp_path, monkeypatch):
        """vm agent exec does a POST dry-run to initiate execution."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "vm", "agent", "exec", "100",
            "--command", "hostname",
            "--node", "pve01",
        )
        assert result.returncode == 0
        assert "POST" in result.stdout
        assert "agent/exec" in result.stdout
