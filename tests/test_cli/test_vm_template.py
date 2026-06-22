"""Unit tests for VM template CLI command."""

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


class TestVMTemplateCLI:
    def test_vm_template_dry_run(self, tmp_path, monkeypatch):
        """vm template does a POST dry-run."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "vm", "template", "100",
            "--node", "pve01",
        )
        assert result.returncode == 0
        assert "POST" in result.stdout
        assert "/template" in result.stdout

    def test_vm_template_no_node(self, tmp_path, monkeypatch):
        """vm template with --password auto-entangles (resolves node)."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "vm", "template", "100",
            "--node", "pve01",
        )
        assert result.returncode == 0
        assert "POST" in result.stdout
