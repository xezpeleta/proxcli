"""Unit tests for VM ISO attach/detach CLI commands."""

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


class TestVMISOAttachCLI:
    def test_vm_iso_attach_dry_run(self, tmp_path, monkeypatch):
        """vm iso attach does a PUT dry-run setting ide2."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "vm", "iso", "attach", "100",
            "--iso-volume", "local:iso/ubuntu-24.04.iso",
            "--node", "pve01",
        )
        assert result.returncode == 0
        assert "PUT" in result.stdout
        assert "/config" in result.stdout
        assert "ide2" in result.stdout
        assert "local:iso/ubuntu-24.04.iso" in result.stdout

    def test_vm_iso_attach_missing_volume(self, tmp_path, monkeypatch):
        """vm iso attach without --iso-volume needs to resolve."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "vm", "iso", "attach", "100",
            "--node", "pve01",
        )
        # Without --iso-volume, the handler sets ide2 to "none"
        assert result.returncode == 0
        assert "PUT" in result.stdout


class TestVMISODetachCLI:
    def test_vm_iso_detach_dry_run(self, tmp_path, monkeypatch):
        """vm iso detach does a PUT dry-run setting ide2 to none."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "vm", "iso", "detach", "100",
            "--node", "pve01",
        )
        assert result.returncode == 0
        assert "PUT" in result.stdout
        assert "/config" in result.stdout
        assert "ide2" in result.stdout
        assert "none" in result.stdout
