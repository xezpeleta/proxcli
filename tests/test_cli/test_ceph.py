"""Integration tests for `proxmox ceph` commands."""

from __future__ import annotations

import os
import subprocess
import sys


def run_proxmox(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    """Run the proxmox CLI and return the completed process."""
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    return subprocess.run(
        [sys.executable, "-m", "proxmox.cli.main", *args],
        capture_output=True,
        text=True,
        timeout=10,
        env=merged_env,
    )


def _fake_env(tmp_path) -> dict[str, str]:
    """Return env vars targeting a temp config dir."""
    return {"PROXMOX_CONFIG_DIR": str(tmp_path / "proxmox-cli")}


class TestCephCLI:
    def test_ceph_status_dry_run(self, tmp_path):
        """ceph status --dry-run shows the request."""
        env = _fake_env(tmp_path)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "ceph", "status",
            env=env,
        )
        assert result.returncode == 0
        assert "GET" in result.stdout
        assert "cluster/ceph/status" in result.stdout

    def test_ceph_log_dry_run(self, tmp_path):
        """ceph log --dry-run shows the request."""
        env = _fake_env(tmp_path)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "ceph", "log",
            "--node", "pve01",
            "--limit", "10",
            env=env,
        )
        assert result.returncode == 0
        assert "GET" in result.stdout
        assert "nodes/pve01/ceph/log" in result.stdout

    def test_ceph_osd_dry_run(self, tmp_path):
        """ceph osd --dry-run shows the request."""
        env = _fake_env(tmp_path)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "ceph", "osd",
            "--node", "pve01",
            env=env,
        )
        assert result.returncode == 0
        assert "GET" in result.stdout
        assert "disks/list" in result.stdout

    def test_ceph_disks_dry_run(self, tmp_path):
        """ceph disks --dry-run shows the request."""
        env = _fake_env(tmp_path)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "ceph", "disks",
            env=env,
        )
        assert result.returncode == 0
        assert "GET" in result.stdout
        assert "nodes" in result.stdout
