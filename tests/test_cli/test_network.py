"""Unit tests for network CLI commands."""

from __future__ import annotations

import subprocess
import sys


def run_proxmox(*args: str) -> subprocess.CompletedProcess:
    """Run the proxmox CLI and return the completed process."""
    return subprocess.run(
        [sys.executable, "-m", "proxmox.cli.main", *args],
        capture_output=True,
        text=True,
        timeout=10,
    )


class TestNetworkCLI:
    def test_network_list_dry_run(self, tmp_path, monkeypatch):
        """network list --dry-run prints the GET request."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "network", "list",
            "--node", "pve01",
        )
        assert result.returncode == 0
        assert "GET" in result.stdout
        assert "nodes/pve01/network" in result.stdout

    def test_network_list_type_filter(self, tmp_path, monkeypatch):
        """network list --type bridge adds type param."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "network", "list",
            "--node", "pve01",
            "--type", "bridge",
        )
        assert result.returncode == 0
        assert "nodes/pve01/network" in result.stdout

    def test_network_list_default_node(self, tmp_path, monkeypatch):
        """network list defaults to localhost when --node not given."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "network", "list",
        )
        assert result.returncode == 0
        assert "nodes/localhost/network" in result.stdout

    def test_network_show_dry_run(self, tmp_path, monkeypatch):
        """network show --dry-run prints the GET request."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "network", "show", "vmbr0",
            "--node", "pve01",
        )
        assert result.returncode == 0
        assert "GET" in result.stdout
        assert "nodes/pve01/network/vmbr0" in result.stdout

    def test_network_show_default_node(self, tmp_path, monkeypatch):
        """network show defaults to localhost when --node not given."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "network", "show", "bond0",
        )
        assert result.returncode == 0
        assert "nodes/localhost/network/bond0" in result.stdout

    def test_network_show_missing_iface(self, tmp_path, monkeypatch):
        """network show without iface argument fails."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "network", "show",
            "--node", "pve01",
        )
        assert result.returncode != 0
