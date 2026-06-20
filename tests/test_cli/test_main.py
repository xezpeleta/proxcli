"""Integration tests for CLI commands."""

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


class TestCLIAuth:
    def test_auth_clear_and_status(self, tmp_path, monkeypatch):
        """auth clear and auth status work without credentials."""
        # Override config dir
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        # Clear (should succeed even if nothing to clear)
        result = run_proxmox("auth", "clear")
        # Status should show not authenticated
        result = run_proxmox("auth", "status")
        data = json.loads(result.stdout)
        assert data["status"] == "not authenticated"

    def test_auth_login_missing_password(self, tmp_path, monkeypatch):
        """auth login fails without password or token."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "auth", "login",
            "--url", "https://pve:8006",
            "--username", "root@pam",
        )
        assert result.returncode != 0
        assert "password" in result.stderr.lower() or "required" in result.stderr.lower()


class TestCLIVM:
    def test_vm_dry_run(self, tmp_path, monkeypatch):
        """VM create --dry-run prints the request without contacting API."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--password", "test",
            "--dry-run",
            "vm", "create",
            "--node", "pve01",
            "--vmid", "100",
            "--memory", "2048",
        )
        assert result.returncode == 0
        assert "POST" in result.stdout
        assert "pve:8006" in result.stdout
        assert "vmid" in result.stdout

    def test_vm_create_from_file_dry_run(self, tmp_path, monkeypatch):
        """VM create --file --dry-run loads YAML spec and prints the request."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        # Create a minimal YAML spec file
        spec_file = tmp_path / "vm-spec.yaml"
        spec_file.write_text("""
name: test-vm
node: pve01
memory: 2048
cores: 2
net0: "virtio=00:11:22:33:44:55,bridge=vmbr0"
""")

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "vm", "create",
            "--file", str(spec_file),
        )
        assert result.returncode == 0
        assert "POST" in result.stdout
        assert "pve01" in result.stdout
        assert "test-vm" in result.stdout

    def test_vm_create_file_no_node(self, tmp_path, monkeypatch):
        """VM create --file without node: in spec fails gracefully."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        spec_file = tmp_path / "vm-nonode.yaml"
        spec_file.write_text("""
name: test-vm
memory: 2048
cores: 1
""")

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "vm", "create",
            "--file", str(spec_file),
        )
        assert "--node is required" in result.stdout or result.returncode != 0

    def test_vm_create_file_cli_override(self, tmp_path, monkeypatch):
        """CLI flags override --file values."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        spec_file = tmp_path / "vm-spec.yaml"
        spec_file.write_text("""
name: file-name
node: pve01
memory: 2048
cores: 2
""")

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "vm", "create",
            "--file", str(spec_file),
            "--name", "override-name",
            "--memory", "8192",
        )
        assert result.returncode == 0
        assert "override-name" in result.stdout
        assert "8192" in result.stdout

    def test_vm_create_file_bad_yaml(self, tmp_path, monkeypatch):
        """Invalid YAML returns an error."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        spec_file = tmp_path / "bad.yaml"
        spec_file.write_text("this: [ is not: valid")

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "vm", "create",
            "--file", str(spec_file),
        )
        assert "error" in result.stdout.lower()

    def test_vm_create_file_not_found(self, tmp_path, monkeypatch):
        """Missing file returns an error."""
        config_dir = tmp_path / "proxmox-cli"
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", config_dir)

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "vm", "create",
            "--file", "/nonexistent/vm.yaml",
        )
        assert "error" in result.stdout.lower()
