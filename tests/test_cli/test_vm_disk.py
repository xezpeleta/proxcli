"""Unit tests for VM disk CLI commands."""

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


class TestVMDiskResizeCLI:
    def test_vm_disk_resize_dry_run(self, tmp_path, monkeypatch):
        """vm disk resize does a PUT dry-run."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "vm", "disk", "resize", "100",
            "--disk", "scsi0",
            "--size", "+10G",
            "--node", "pve01",
        )
        assert result.returncode == 0
        assert "PUT" in result.stdout
        assert "/resize" in result.stdout
        assert "scsi0" in result.stdout
        assert "+10G" in result.stdout

    def test_vm_disk_resize_missing_disk(self, tmp_path, monkeypatch):
        """vm disk resize without --disk should fail."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "vm", "disk", "resize", "100",
            "--size", "+10G",
            "--node", "pve01",
        )
        assert result.returncode != 0


class TestVMDiskDetachCLI:
    def test_vm_disk_detach_dry_run(self, tmp_path, monkeypatch):
        """vm disk detach does a PUT dry-run setting disk to none."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "vm", "disk", "detach", "100",
            "--disk", "scsi0",
            "--node", "pve01",
        )
        assert result.returncode == 0
        assert "PUT" in result.stdout
        assert "/config" in result.stdout
        assert "scsi0" in result.stdout
        assert "none" in result.stdout


class TestVMDiskRemoveCLI:
    def test_vm_disk_remove_dry_run(self, tmp_path, monkeypatch):
        """vm disk remove does a PUT dry-run with delete field."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "vm", "disk", "remove", "100",
            "--disk", "scsi0",
            "--force",
            "--node", "pve01",
        )
        assert result.returncode == 0
        assert "PUT" in result.stdout
        assert "/config" in result.stdout
        assert "delete" in result.stdout
        assert "scsi0" in result.stdout

    def test_vm_disk_remove_missing_disk(self, tmp_path, monkeypatch):
        """vm disk remove without --disk should fail."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "vm", "disk", "remove", "100",
            "--node", "pve01",
        )
        assert result.returncode != 0
