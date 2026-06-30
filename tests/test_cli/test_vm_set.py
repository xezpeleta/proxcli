"""Unit tests for VM set CLI command."""

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


class TestVMSetCLI:
    def test_vm_set_ipconfig_dry_run(self, tmp_path, monkeypatch):
        """vm set --ipconfig0 does a PUT dry-run."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "vm", "set", "201",
            "--node", "pve01",
            "--ipconfig0", "ip=10.0.0.51/24,gw=10.0.0.1",
        )
        assert result.returncode == 0
        assert "PUT" in result.stdout
        assert "/config" in result.stdout
        assert "ipconfig0" in result.stdout
        assert "10.0.0.51" in result.stdout

    def test_vm_set_ciuser_dry_run(self, tmp_path, monkeypatch):
        """vm set --ciuser with --cipassword."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "vm", "set", "201",
            "--node", "pve01",
            "--ciuser", "debian",
            "--cipassword", "ChangeMe123!",
        )
        assert result.returncode == 0
        assert "PUT" in result.stdout
        assert "ciuser" in result.stdout
        assert "debian" in result.stdout
        assert "cipassword" in result.stdout

    def test_vm_set_options_dry_run(self, tmp_path, monkeypatch):
        """vm set --option key=value (repeatable)."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "vm", "set", "201",
            "--node", "pve01",
            "--option", "memory=8192",
            "--option", "cores=4",
        )
        assert result.returncode == 0
        assert "PUT" in result.stdout
        assert "memory" in result.stdout
        assert "8192" in result.stdout
        assert "cores" in result.stdout
        assert "4" in result.stdout

    def test_vm_set_no_args_errors(self, tmp_path, monkeypatch):
        """vm set with no config keys should return an error dict."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "vm", "set", "201",
            "--node", "pve01",
        )
        assert '"error"' in result.stdout
        assert "No configuration keys provided" in result.stdout

    def test_vm_set_combined(self, tmp_path, monkeypatch):
        """vm set with ipconfig + cloud-init flags + options."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "vm", "set", "201",
            "--node", "pve01",
            "--ipconfig0", "ip=dhcp",
            "--nameserver", "8.8.8.8",
            "--option", "description=web server",
        )
        assert result.returncode == 0
        assert "PUT" in result.stdout
        assert "ipconfig0" in result.stdout
        assert "dhcp" in result.stdout
        assert "nameserver" in result.stdout
        assert "8.8.8.8" in result.stdout
        assert "description" in result.stdout
