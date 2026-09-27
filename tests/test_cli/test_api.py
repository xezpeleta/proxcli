"""Unit tests for api CLI command."""

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


class TestAPICLI:
    def test_api_get_dry_run(self, tmp_path, monkeypatch):
        """api GET does a dry-run."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "api", "GET", "/nodes/pve01/status",
        )
        assert result.returncode == 0
        assert "GET" in result.stdout
        assert "/api2/json/nodes/pve01/status" in result.stdout

    def test_api_put_dry_run(self, tmp_path, monkeypatch):
        """api PUT with --data does a dry-run."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "api", "PUT", "/nodes/pve01/qemu/100/config",
            "--data", '{"memory": 4096}',
        )
        assert result.returncode == 0
        assert "PUT" in result.stdout
        assert "/api2/json/nodes/pve01/qemu/100/config" in result.stdout
        assert "memory" in result.stdout

    def test_api_strips_prefix(self, tmp_path, monkeypatch):
        """api strips /api2/json prefix if present."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "api", "GET", "/api2/json/nodes/pve01/status",
        )
        assert result.returncode == 0
        # Should not double-prefix
        assert "/api2/json/api2/json" not in result.stdout
        assert "/api2/json/nodes/pve01/status" in result.stdout

    def test_api_post_dry_run(self, tmp_path, monkeypatch):
        """api POST with --data."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "api", "POST", "/nodes/pve01/qemu",
            "--data", '{"vmid": 200, "name": "test-vm"}',
        )
        assert result.returncode == 0
        assert "POST" in result.stdout
        assert "vmid" in result.stdout
        assert "test-vm" in result.stdout

    def test_api_delete_dry_run(self, tmp_path, monkeypatch):
        """api DELETE."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "api", "DELETE", "/nodes/pve01/qemu/200",
        )
        assert result.returncode == 0
        assert "DELETE" in result.stdout

    def test_api_invalid_json(self, tmp_path, monkeypatch):
        """api with invalid --data returns error."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "api", "PUT", "/nodes/pve01/qemu/100/config",
            "--data", "not json",
        )
        assert "Invalid JSON" in result.stdout or "error" in result.stdout

    def test_api_list_endpoints_no_creds(self):
        """api --list-endpoints needs no credentials (pure documentation)."""
        result = run_proxmox("api", "--list-endpoints", "--output", "json")
        assert result.returncode == 0, result.stderr
        import json as _json
        data = _json.loads(result.stdout)
        assert isinstance(data, list)
        assert len(data) > 20
        # each record has the documented shape
        first = data[0]
        assert {"category", "method", "path", "description"} <= set(first)

    def test_api_list_endpoints_table(self):
        """api --list-endpoints --output table renders a grouped table."""
        result = run_proxmox("api", "--list-endpoints", "--output", "table")
        assert result.returncode == 0
        assert "category" in result.stdout
        assert "/cluster/status" in result.stdout

    def test_api_no_method_without_list_endpoints_errors(self, tmp_path, monkeypatch):
        """api with no method/path and no --list-endpoints returns an error."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "api",
        )
        assert result.returncode == 0  # handler returns an error dict, not a crash
        assert "method is required" in result.stdout

    def test_api_help_epilog_documents_path_conventions(self):
        """api --help surfaces the node-vs-cluster path convention."""
        result = run_proxmox("api", "--help")
        assert result.returncode == 0
        assert "Cluster-wide:" in result.stdout
        assert "Per-node:" in result.stdout
        assert "--list-endpoints" in result.stdout
