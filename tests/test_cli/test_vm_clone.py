"""Unit tests for VM clone CLI command."""

from __future__ import annotations

import subprocess
import sys


def run_proxmox(*args: str) -> subprocess.CompletedProcess:
    """Run the proxmox CLI and return the completed process."""
    import os
    # Resolve the venv entrypoint relative to the project root
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    entrypoint = os.path.join(project_root, ".venv", "bin", "proxmox")
    if os.path.exists(entrypoint):
        return subprocess.run(
            [entrypoint, *args],
            capture_output=True,
            text=True,
            timeout=10,
        )
    # Fallback: try sys.executable with -m
    return subprocess.run(
        [sys.executable, "-m", "proxmox.cli.main", *args],
        capture_output=True,
        text=True,
        timeout=10,
    )


class TestVMCloneCLI:
    def test_vm_clone_dry_run_basic(self, tmp_path, monkeypatch):
        """vm clone --newid with minimal args does a POST dry-run."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "vm", "clone", "100",
            "--newid", "200",
            "--node", "pve01",
        )
        assert result.returncode == 0
        assert "POST" in result.stdout
        assert "/clone" in result.stdout
        assert "200" in result.stdout
        assert "newid" in result.stdout

    def test_vm_clone_dry_run_full(self, tmp_path, monkeypatch):
        """vm clone with all optional flags."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "vm", "clone", "100",
            "--newid", "300",
            "--node", "pve01",
            "--name", "cloned-vm",
            "--target-node", "pve02",
            "--target-storage", "rbd_ssd",
            "--full", "0",
            "--description", "Test clone from CLI",
            "--pool", "dev-pool",
        )
        assert result.returncode == 0
        assert "POST" in result.stdout
        assert "/clone" in result.stdout
        assert "newid" in result.stdout
        assert "300" in result.stdout
        assert "cloned-vm" in result.stdout
        assert "pve02" in result.stdout
        assert "rbd_ssd" in result.stdout
        assert "Test clone from CLI" in result.stdout
        assert "dev-pool" in result.stdout

    def test_vm_clone_missing_newid(self, tmp_path, monkeypatch):
        """vm clone without --newid should fail (required arg)."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--password", "test",
            "--dry-run",
            "vm", "clone", "100",
        )
        assert result.returncode != 0

    def test_vm_clone_linked(self, tmp_path, monkeypatch):
        """vm clone with --full 0 (linked clone)."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "vm", "clone", "100",
            "--newid", "400",
            "--full", "0",
            "--node", "pve01",
        )
        assert result.returncode == 0
        assert "POST" in result.stdout
        assert "full" in result.stdout
        assert "0" in result.stdout
