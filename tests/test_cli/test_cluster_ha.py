"""Unit tests for ``cluster ha`` — read-only High Availability inspection."""

from __future__ import annotations

import argparse

from proxmox.cli.cluster import (
    _cl_ha_config,
    _cl_ha_group_show,
    _cl_ha_groups,
    _cl_ha_resource_show,
    _cl_ha_resources,
    _cl_ha_status,
)
from proxmox.client.auth import AuthManager
from proxmox.client.client import ProxmoxClient


def _client() -> ProxmoxClient:
    return ProxmoxClient("https://pve:8006", AuthManager(), timeout=5)


_BASE = "https://pve:8006/api2/json/cluster/ha"


class TestHAStatus:
    def test_status(self, mock_httpx_client):
        data = [{"type": "service", "id": "vm:100", "state": "started"}]
        mock_httpx_client.add_response(url=f"{_BASE}/status/current", json={"data": data})
        result = _cl_ha_status(argparse.Namespace(), _client())
        assert result == data

    def test_config(self, mock_httpx_client):
        data = {"quorum": 3, "manager": "pve01"}
        mock_httpx_client.add_response(url=f"{_BASE}/config", json={"data": data})
        result = _cl_ha_config(argparse.Namespace(), _client())
        assert result == data


class TestHAResources:
    def test_list(self, mock_httpx_client):
        data = [
            {"sid": "vm:100", "state": "started", "group": "grp1"},
            {"sid": "ct:200", "state": "stopped", "group": "grp2"},
        ]
        mock_httpx_client.add_response(url=f"{_BASE}/resources", json={"data": data})
        result = _cl_ha_resources(argparse.Namespace(), _client())
        assert result == data

    def test_show(self, mock_httpx_client):
        data = {"sid": "vm:100", "state": "started", "group": "grp1"}
        mock_httpx_client.add_response(url=f"{_BASE}/resources/vm:100", json={"data": data})
        result = _cl_ha_resource_show(argparse.Namespace(sid="vm:100"), _client())
        assert result == data

    def test_show_container_sid(self, mock_httpx_client):
        data = {"sid": "ct:200", "state": "stopped"}
        mock_httpx_client.add_response(url=f"{_BASE}/resources/ct:200", json={"data": data})
        result = _cl_ha_resource_show(argparse.Namespace(sid="ct:200"), _client())
        assert result == data


class TestHAGroups:
    def test_list(self, mock_httpx_client):
        data = [{"group": "grp1", "nodes": "pve01 pve02"}]
        mock_httpx_client.add_response(url=f"{_BASE}/groups", json={"data": data})
        result = _cl_ha_groups(argparse.Namespace(), _client())
        assert result == data

    def test_show(self, mock_httpx_client):
        data = {"group": "grp1", "nodes": "pve01 pve02", "restricted": 0}
        mock_httpx_client.add_response(url=f"{_BASE}/groups/grp1", json={"data": data})
        result = _cl_ha_group_show(argparse.Namespace(group="grp1"), _client())
        assert result == data
