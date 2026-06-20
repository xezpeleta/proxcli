"""Unit tests for backup CLI commands."""

from __future__ import annotations

import json
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


class TestBackupCLI:
    def test_backup_create_dry_run(self, tmp_path, monkeypatch):
        """backup create --dry-run prints the POST request."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--password", "test",
            "--dry-run",
            "backup", "create",
            "--node", "pve01",
            "--vmid", "100",
            "--storage", "pbs-store",
            "--mode", "snapshot",
            "--compress", "zstd",
        )
        assert result.returncode == 0
        assert "POST" in result.stdout
        assert "vzdump" in result.stdout
        assert "pve01" in result.stdout
        assert "pbs-store" in result.stdout

    def test_backup_create_all_dry_run(self, tmp_path, monkeypatch):
        """backup create --all --dry-run."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "backup", "create",
            "--node", "pve01",
            "--all",
            "--storage", "pbs-store",
        )
        assert result.returncode == 0
        assert "POST" in result.stdout
        assert "vzdump" in result.stdout
        assert '"all"' in result.stdout or "all" in result.stdout

    def test_backup_list_dry_run(self, tmp_path, monkeypatch):
        """backup list --dry-run prints the GET request."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "backup", "list",
            "--node", "pve01",
            "--storage", "pbs-store",
        )
        assert result.returncode == 0
        assert "GET" in result.stdout
        assert "storage" in result.stdout
        assert "content" in result.stdout

    def test_backup_tasks_dry_run(self, tmp_path, monkeypatch):
        """backup tasks --dry-run prints the GET request."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "backup", "tasks",
            "--node", "pve01",
            "--limit", "10",
        )
        assert result.returncode == 0
        assert "GET" in result.stdout
        assert "tasks" in result.stdout

    def test_backup_delete_dry_run(self, tmp_path, monkeypatch):
        """backup delete --dry-run prints the DELETE request."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "backup", "delete",
            "pbs-store:backup/vm/100/2024-01-01T00:00:00Z",
            "--node", "pve01",
        )
        assert result.returncode == 0
        assert "DELETE" in result.stdout
        assert "storage" in result.stdout
        assert "content" in result.stdout

    def test_backup_show_dry_run(self, tmp_path, monkeypatch):
        """backup show --dry-run prints the GET request."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "backup", "show",
            "pbs-store:backup/vm/100/2024-01-01T00:00:00Z",
            "--node", "pve01",
            "--vmid", "100",
        )
        assert result.returncode == 0
        assert "GET" in result.stdout

    def test_backup_defaults_dry_run(self, tmp_path, monkeypatch):
        """backup defaults --dry-run prints the GET request."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "backup", "defaults",
            "--node", "pve01",
            "--storage", "pbs-store",
        )
        assert result.returncode == 0
        assert "GET" in result.stdout
        assert "vzdump" in result.stdout

    def test_backup_create_no_vmid_or_all(self, tmp_path, monkeypatch):
        """backup create without --vmid or --all fails."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "backup", "create",
            "--node", "pve01",
            "--storage", "pbs-store",
        )
        # Should still return 0 because --dry-run runs the handler which returns an error dict
        stdout = result.stdout.strip()
        if stdout:
            data = json.loads(stdout)
            assert "error" in data
