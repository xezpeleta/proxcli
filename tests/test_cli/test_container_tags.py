"""Unit + dry-run tests for container tags — ``container create --tag``."""

from __future__ import annotations

import os
import subprocess
import sys


def _run_proxmox(*args: str) -> subprocess.CompletedProcess:
    """Run the proxmox CLI binary and return the completed process."""
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    entrypoint = os.path.join(project_root, ".venv", "bin", "proxmox")
    if os.path.exists(entrypoint):
        return subprocess.run([entrypoint, *args], capture_output=True, text=True, timeout=10)
    return subprocess.run(
        [sys.executable, "-m", "proxmox.cli.main", *args],
        capture_output=True,
        text=True,
        timeout=10,
    )


class TestContainerCreateTagsDryRun:
    def test_create_with_tags_dry_run(self, tmp_path, monkeypatch):
        """``container create --tag`` includes tags in the dry-run POST body."""
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", tmp_path / "proxmox-cli")

        result = _run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "container", "create",
            "--node", "pve01",
            "--vmid", "200",
            "--ostemplate", "local:vztmpl/debian-12.tar.zst",
            "--memory", "512",
            "--tag", "web",
            "--tag", "prod",
        )
        assert result.returncode == 0
        assert "POST" in result.stdout
        assert "/nodes/pve01/lxc" in result.stdout
        # container create sends a dict body; tags appear as 'tags': 'web;prod'
        assert "'tags'" in result.stdout
        assert "web;prod" in result.stdout

    def test_create_without_tags_omits_tags_key(self, tmp_path, monkeypatch):
        """Without ``--tag``, the POST body has no tags key."""
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", tmp_path / "proxmox-cli")

        result = _run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "container", "create",
            "--node", "pve01",
            "--vmid", "201",
            "--ostemplate", "local:vztmpl/debian-12.tar.zst",
            "--memory", "512",
        )
        assert result.returncode == 0
        assert "'tags'" not in result.stdout
