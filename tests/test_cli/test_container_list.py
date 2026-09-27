"""Unit tests for `container list` — name filtering and the `node` field."""

from __future__ import annotations

import argparse

from proxmox.cli.container import _ct_list
from proxmox.client.auth import AuthManager
from proxmox.client.client import ProxmoxClient


def _client() -> ProxmoxClient:
    return ProxmoxClient("https://pve:8006", AuthManager(), timeout=5)


class TestContainerList:
    def test_injects_bare_node_field(self, mock_httpx_client):
        mock_httpx_client.add_response(
            url="https://pve:8006/api2/json/nodes",
            json={"data": [{"node": "pve01"}]},
        )
        mock_httpx_client.add_response(
            url="https://pve:8006/api2/json/nodes/pve01/lxc",
            json={"data": [{"vmid": 200, "name": "dns"}]},
        )
        result = _ct_list(argparse.Namespace(node=None, name=None), _client())
        assert result[0]["node"] == "pve01"
        assert result[0]["_node"] == "pve01"

    def test_name_filter_case_insensitive(self, mock_httpx_client):
        mock_httpx_client.add_response(
            url="https://pve:8006/api2/json/nodes/pve01/lxc",
            json={"data": [
                {"vmid": 200, "name": "dns-resolver"},
                {"vmid": 201, "name": "mail"},
            ]},
        )
        result = _ct_list(argparse.Namespace(node="pve01", name="DNS"), _client())
        assert len(result) == 1
        assert result[0]["vmid"] == 200
