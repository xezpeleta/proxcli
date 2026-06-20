"""Integration tests for `proxmox node` system commands (subscription, dns, time, services, pci, netstat, config)."""

from __future__ import annotations

import os
import subprocess
import sys


def run_proxmox(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
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
    return {"PROXMOX_CONFIG_DIR": str(tmp_path / "proxmox-cli")}


class TestNodeSystemCLI:
    def test_subscription_dry_run(self, tmp_path):
        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "node", "subscription", "pve01",
            env=_fake_env(tmp_path),
        )
        assert result.returncode == 0
        assert "GET" in result.stdout
        assert "nodes/pve01/subscription" in result.stdout

    def test_dns_dry_run(self, tmp_path):
        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "node", "dns", "pve01",
            env=_fake_env(tmp_path),
        )
        assert result.returncode == 0
        assert "GET" in result.stdout
        assert "nodes/pve01/dns" in result.stdout

    def test_time_dry_run(self, tmp_path):
        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "node", "time", "pve01",
            env=_fake_env(tmp_path),
        )
        assert result.returncode == 0
        assert "GET" in result.stdout
        assert "nodes/pve01/time" in result.stdout

    def test_services_dry_run(self, tmp_path):
        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "node", "services", "pve01",
            env=_fake_env(tmp_path),
        )
        assert result.returncode == 0
        assert "GET" in result.stdout
        assert "nodes/pve01/services" in result.stdout

    def test_pci_dry_run(self, tmp_path):
        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "node", "pci", "pve01",
            env=_fake_env(tmp_path),
        )
        assert result.returncode == 0
        assert "GET" in result.stdout
        assert "hardware/pci" in result.stdout

    def test_netstat_dry_run(self, tmp_path):
        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "node", "netstat", "pve01",
            env=_fake_env(tmp_path),
        )
        assert result.returncode == 0
        assert "GET" in result.stdout
        assert "nodes/pve01/netstat" in result.stdout

    def test_config_dry_run(self, tmp_path):
        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "node", "config", "pve01",
            env=_fake_env(tmp_path),
        )
        assert result.returncode == 0
        assert "GET" in result.stdout
        assert "nodes/pve01/config" in result.stdout


class TestClusterSystemCLI:
    def test_log_dry_run(self, tmp_path):
        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "cluster", "log", "--limit", "20",
            env=_fake_env(tmp_path),
        )
        assert result.returncode == 0
        assert "GET" in result.stdout
        assert "cluster/log" in result.stdout

    def test_options_dry_run(self, tmp_path):
        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "cluster", "options",
            env=_fake_env(tmp_path),
        )
        assert result.returncode == 0
        assert "GET" in result.stdout
        assert "cluster/options" in result.stdout


class TestStorageStatusCLI:
    def test_status_dry_run(self, tmp_path):
        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "storage", "status", "local", "--node", "pve01",
            env=_fake_env(tmp_path),
        )
        assert result.returncode == 0
        assert "GET" in result.stdout
        assert "nodes/pve01/storage/local/status" in result.stdout
