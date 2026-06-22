"""Unit tests for backup restore CLI command."""

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


class TestBackupRestoreCLI:
    def test_backup_restore_dry_run_basic(self, tmp_path, monkeypatch):
        """backup restore with minimal args does a POST dry-run."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "backup", "restore",
            "pbs:backup/vm/100/2025/01/01/vzdump-qemu-100-2025_01_01-00_00_00.vma.zst",
            "--vmid", "200",
            "--node", "pve01",
        )
        assert result.returncode == 0
        assert "POST" in result.stdout
        assert "/qemu" in result.stdout
        assert "archive" in result.stdout
        assert "200" in result.stdout

    def test_backup_restore_dry_run_full(self, tmp_path, monkeypatch):
        """backup restore with all optional flags."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "backup", "restore",
            "pbs:backup/vm/100/2025/01/01/vzdump-qemu-100-2025_01_01-00_00_00.vma.zst",
            "--vmid", "200",
            "--node", "pve01",
            "--storage", "rbd_ssd",
            "--unique",
            "--pool", "dev-pool",
            "--start",
        )
        assert result.returncode == 0
        assert "POST" in result.stdout
        assert "/qemu" in result.stdout
        assert "archive" in result.stdout
        assert "rbd_ssd" in result.stdout
        assert "unique" in result.stdout
        assert "dev-pool" in result.stdout
        assert "start" in result.stdout

    def test_backup_restore_missing_vmid(self, tmp_path, monkeypatch):
        """backup restore without --vmid should fail."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "backup", "restore",
            "pbs:backup/vm/100/vzdump-qemu-100.vma.zst",
            "--node", "pve01",
        )
        assert result.returncode != 0

    def test_backup_restore_container(self, tmp_path, monkeypatch):
        """backup restore should detect LXC backups and use /lxc endpoint."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "backup", "restore",
            "pbs:backup/lxc/100/vzdump-lxc-100-2025_01_01-00_00_00.tar.zst",
            "--vmid", "200",
            "--node", "pve01",
        )
        assert result.returncode == 0
        assert "POST" in result.stdout
        # Should use /lxc endpoint, not /qemu
        assert "/lxc" in result.stdout
        assert "archive" in result.stdout
        assert "200" in result.stdout
