"""Unit tests for VM tags — ``vm set --tag``/``--clear-tags`` and ``vm create --tag``."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys

from proxmox.cli.vm import _vm_set
from proxmox.client.auth import AuthManager
from proxmox.client.client import ProxmoxClient


def _client() -> ProxmoxClient:
    return ProxmoxClient("https://pve:8006", AuthManager(), timeout=5)


def _set_namespace(**overrides) -> argparse.Namespace:
    """Build a Namespace for ``_vm_set`` with sensible defaults."""
    defaults: dict = dict(
        vmid=100,
        node="pve01",
        ipconfig0=None,
        ipconfig1=None,
        ipconfig2=None,
        ipconfig3=None,
        ciuser=None,
        cipassword=None,
        sshkeys=None,
        nameserver=None,
        searchdomain=None,
        cicustom=None,
        options=None,
        add_tags=None,
        clear_tags=False,
    )
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


_CONFIG_URL = "https://pve:8006/api2/json/nodes/pve01/qemu/100/config"


class TestVMSetTags:
    def test_add_tag_merges_with_existing(self, mock_httpx_client):
        """``--tag`` reads current config and merges without clobbering."""
        mock_httpx_client.add_response(
            url=_CONFIG_URL,
            json={"data": {"tags": "existing", "name": "web-01"}},
        )
        mock_httpx_client.add_response(
            method="PUT",
            url=_CONFIG_URL,
            json={"data": None},
        )
        args = _set_namespace(add_tags=["web", "prod"])
        _vm_set(args, _client())

        requests = mock_httpx_client.get_requests()
        assert len(requests) == 2
        assert requests[0].method == "GET"
        assert requests[1].method == "PUT"
        body = requests[1].content.decode()
        assert "tags=" in body
        assert "existing" in body  # preserved
        assert "web" in body  # added
        assert "prod" in body  # added

    def test_add_tag_deduplicates(self, mock_httpx_client):
        """``--tag`` does not duplicate a tag already present."""
        mock_httpx_client.add_response(
            url=_CONFIG_URL,
            json={"data": {"tags": "web"}},
        )
        mock_httpx_client.add_response(
            method="PUT",
            url=_CONFIG_URL,
            json={"data": None},
        )
        args = _set_namespace(add_tags=["web", "prod"])
        _vm_set(args, _client())

        body = mock_httpx_client.get_requests()[-1].content.decode()
        # "web" appears exactly once (deduped)
        assert body.count("web") == 1
        assert "prod" in body

    def test_add_tag_to_untagged_vm(self, mock_httpx_client):
        """``--tag`` on a VM with no existing tags sets them fresh."""
        mock_httpx_client.add_response(
            url=_CONFIG_URL,
            json={"data": {"name": "web-01"}},  # no "tags" key
        )
        mock_httpx_client.add_response(
            method="PUT",
            url=_CONFIG_URL,
            json={"data": None},
        )
        args = _set_namespace(add_tags=["new"])
        _vm_set(args, _client())

        body = mock_httpx_client.get_requests()[-1].content.decode()
        assert "tags=new" in body

    def test_clear_tags_sends_delete(self, mock_httpx_client):
        """``--clear-tags`` sends ``delete=tags`` without reading current config."""
        mock_httpx_client.add_response(
            method="PUT",
            url=_CONFIG_URL,
            json={"data": None},
        )
        args = _set_namespace(clear_tags=True)
        _vm_set(args, _client())

        requests = mock_httpx_client.get_requests()
        # No GET — clearing doesn't need to read current tags
        assert len(requests) == 1
        assert requests[0].method == "PUT"
        body = requests[0].content.decode()
        assert "delete=tags" in body


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


class TestVMCreateTagsDryRun:
    def test_create_with_tags_dry_run(self, tmp_path, monkeypatch):
        """``vm create --tag`` includes tags in the dry-run POST body."""
        monkeypatch.setattr("proxmox.config.models.USER_CONFIG_DIR", tmp_path / "proxmox-cli")

        result = _run_proxmox(
            "--url", "https://pve:8006",
            "--username", "root@pam",
            "--api-token", "root@pam!test=abc123",
            "--dry-run",
            "vm", "create",
            "--node", "pve01",
            "--vmid", "100",
            "--memory", "1024",
            "--name", "web-01",
            "--tag", "web",
            "--tag", "prod",
        )
        assert result.returncode == 0
        assert "POST" in result.stdout
        assert "/nodes/pve01/qemu" in result.stdout
        assert "tags=" in result.stdout
        assert "web" in result.stdout
        assert "prod" in result.stdout
