"""Unit tests for VM migrate CLI command."""

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


class TestVMMigrateCLI:
    def test_vm_migrate_dry_run_basic(self, tmp_path, monkeypatch):
        """vm migrate --target with minimal args does a POST dry-run."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "vm", "migrate", "100",
            "--target", "pve02",
            "--node", "pve01",
        )
        assert result.returncode == 0
        assert "POST" in result.stdout
        assert "/migrate" in result.stdout
        assert "target" in result.stdout
        assert "pve02" in result.stdout

    def test_vm_migrate_dry_run_full(self, tmp_path, monkeypatch):
        """vm migrate with all optional flags."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "vm", "migrate", "100",
            "--target", "pve02",
            "--node", "pve01",
            "--online",
            "--with-local-disks",
            "--target-storage", "rbd_ssd",
        )
        assert result.returncode == 0
        assert "POST" in result.stdout
        assert "/migrate" in result.stdout
        assert "online" in result.stdout
        assert "with-local-disks" in result.stdout
        assert "rbd_ssd" in result.stdout
        assert "targetstorage" in result.stdout

    def test_vm_migrate_missing_target(self, tmp_path, monkeypatch):
        """vm migrate without --target should fail (required arg)."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "vm", "migrate", "100",
            "--node", "pve01",
        )
        assert result.returncode != 0

    def test_vm_migrate_online(self, tmp_path, monkeypatch):
        """vm migrate --online for live migration."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "vm", "migrate", "100",
            "--target", "pve02",
            "--node", "pve01",
            "--online",
        )
        assert result.returncode == 0
        assert "POST" in result.stdout
        assert "/migrate" in result.stdout
        assert "online" in result.stdout
