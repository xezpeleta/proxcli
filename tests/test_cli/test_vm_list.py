"""Unit tests for `vm list` — name filtering and the `node` field.

These exercise the handler logic directly with a mocked HTTP layer
(pytest-httpx), which is the cleanest way to test client-side filtering
and response decoration without a live Proxmox API.
"""

from __future__ import annotations

import argparse

from proxmox.cli.vm import _vm_list
from proxmox.client.auth import AuthManager
from proxmox.client.client import ProxmoxClient


def _client() -> ProxmoxClient:
    return ProxmoxClient("https://pve:8006", AuthManager(), timeout=5)


class TestVMList:
    def test_list_injects_bare_node_and_underscore(self, mock_httpx_client):
        """Each VM record carries both `node` and `_node` (the ergonomic key
        agents look for first, plus the historical underscore key)."""
        mock_httpx_client.add_response(
            url="https://pve:8006/api2/json/nodes",
            json={"data": [{"node": "pve01"}]},
        )
        mock_httpx_client.add_response(
            url="https://pve:8006/api2/json/nodes/pve01/qemu",
            json={"data": [{"vmid": 100, "name": "web"}]},
        )

        result = _vm_list(argparse.Namespace(node=None, name=None), _client())
        assert isinstance(result, list)
        assert result[0]["node"] == "pve01"
        assert result[0]["_node"] == "pve01"  # backward compatible

    def test_list_name_filter_case_insensitive_substring(self, mock_httpx_client):
        """--name does a case-insensitive substring match, collapsing the
        'hostname -> vmid + node' lookup to one command."""
        mock_httpx_client.add_response(
            url="https://pve:8006/api2/json/nodes",
            json={"data": [{"node": "pve01"}, {"node": "pve02"}]},
        )
        mock_httpx_client.add_response(
            url="https://pve:8006/api2/json/nodes/pve01/qemu",
            json={"data": [
                {"vmid": 100, "name": "unifi.tknika.net"},
                {"vmid": 101, "name": "webserver"},
            ]},
        )
        mock_httpx_client.add_response(
            url="https://pve:8006/api2/json/nodes/pve02/qemu",
            json={"data": [{"vmid": 200, "name": "UNIFI-backup"}]},
        )

        result = _vm_list(argparse.Namespace(node=None, name="unifi"), _client())
        vmids = {v["vmid"] for v in result}
        assert vmids == {100, 200}  # matches both, case-insensitive
        # node travels with each filtered record
        assert all(v["node"] in {"pve01", "pve02"} for v in result)

    def test_list_name_filter_no_match(self, mock_httpx_client):
        mock_httpx_client.add_response(
            url="https://pve:8006/api2/json/nodes",
            json={"data": [{"node": "pve01"}]},
        )
        mock_httpx_client.add_response(
            url="https://pve:8006/api2/json/nodes/pve01/qemu",
            json={"data": [{"vmid": 100, "name": "web"}]},
        )
        result = _vm_list(argparse.Namespace(node=None, name="nonexistent"), _client())
        assert result == []

    def test_list_single_node_name_filter(self, mock_httpx_client):
        """--name works with --node (filter a single node's VMs)."""
        mock_httpx_client.add_response(
            url="https://pve:8006/api2/json/nodes/pve01/qemu",
            json={"data": [
                {"vmid": 100, "name": "unifi"},
                {"vmid": 101, "name": "other"},
            ]},
        )
        result = _vm_list(argparse.Namespace(node="pve01", name="unifi"), _client())
        assert len(result) == 1
        assert result[0]["vmid"] == 100
        assert result[0]["node"] == "pve01"
