"""Integration tests for CLI commands."""

from __future__ import annotations

import json
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


class TestCLIAuth:
    def test_auth_status_no_config(self, tmp_path):
        """auth status shows 'not authenticated' when no config exists."""
        config_dir = tmp_path / "proxmox-cli"
        env = {"PROXMOX_CONFIG_DIR": str(config_dir)}

        result = run_proxmox("auth", "status", env=env)
        data = json.loads(result.stdout)
        assert data["status"] == "not authenticated"

    def test_auth_status_with_config(self, tmp_path):
        """auth status shows config details when credentials exist."""
        config_dir = tmp_path / "proxmox-cli"
        config_dir.mkdir(parents=True, exist_ok=True)
        creds_file = config_dir / "credentials.json"
        creds_file.write_text(
            json.dumps(
                {
                    "url": "https://pve:8006",
                    "username": "root@pam",
                    "auth_method": "api_token",
                    "api_token_id": "my-token",
                    "api_token_secret": "my-secret",
                }
            )
        )
        env = {"PROXMOX_CONFIG_DIR": str(config_dir)}

        result = run_proxmox("auth", "status", env=env)
        data = json.loads(result.stdout)
        assert data["status"] == "authenticated"
        assert data["url"] == "https://pve:8006"
        assert data["username"] == "root@pam"
        assert data["auth_method"] == "api_token"


class TestCLIVM:
    def test_vm_dry_run(self, tmp_path):
        """VM create --dry-run prints the request without contacting API."""
        config_dir = tmp_path / "proxmox-cli"
        env = {"PROXMOX_CONFIG_DIR": str(config_dir)}

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--password", "test",
            "--dry-run",
            "vm", "create",
            "--node", "pve01",
            "--vmid", "100",
            "--memory", "2048",
            env=env,
        )
        assert result.returncode == 0
        assert "POST" in result.stdout
        assert "pve:8006" in result.stdout
        assert "vmid" in result.stdout

    def test_vm_create_from_file_dry_run(self, tmp_path):
        """VM create --file --dry-run loads YAML spec and prints the request."""
        config_dir = tmp_path / "proxmox-cli"
        env = {"PROXMOX_CONFIG_DIR": str(config_dir)}

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
            env=env,
        )
        assert result.returncode == 0
        assert "POST" in result.stdout
        assert "pve01" in result.stdout
        assert "test-vm" in result.stdout

    def test_vm_create_file_no_node(self, tmp_path):
        """VM create --file without node: in spec fails gracefully."""
        config_dir = tmp_path / "proxmox-cli"
        env = {"PROXMOX_CONFIG_DIR": str(config_dir)}

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
            env=env,
        )
        assert "--node is required" in result.stdout or result.returncode != 0

    def test_vm_create_file_cli_override(self, tmp_path):
        """CLI flags override --file values."""
        config_dir = tmp_path / "proxmox-cli"
        env = {"PROXMOX_CONFIG_DIR": str(config_dir)}

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
            env=env,
        )
        assert result.returncode == 0
        assert "override-name" in result.stdout
        assert "8192" in result.stdout

    def test_vm_create_file_bad_yaml(self, tmp_path):
        """Invalid YAML returns an error."""
        config_dir = tmp_path / "proxmox-cli"
        env = {"PROXMOX_CONFIG_DIR": str(config_dir)}

        spec_file = tmp_path / "bad.yaml"
        spec_file.write_text("this: [ is not: valid")

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "vm", "create",
            "--file", str(spec_file),
            env=env,
        )
        assert "error" in result.stdout.lower()

    def test_vm_create_file_not_found(self, tmp_path):
        """Missing file returns an error."""
        config_dir = tmp_path / "proxmox-cli"
        env = {"PROXMOX_CONFIG_DIR": str(config_dir)}

        result = run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "vm", "create",
            "--file", "/nonexistent/vm.yaml",
            env=env,
        )
        assert "error" in result.stdout.lower()
