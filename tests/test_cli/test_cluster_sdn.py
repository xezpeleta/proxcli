"""Unit tests for ``cluster sdn`` — read-only Software-Defined Networking inspection."""

from __future__ import annotations

import argparse

from proxmox.cli.cluster import (
    _cl_sdn_controller_show,
    _cl_sdn_controllers,
    _cl_sdn_dns,
    _cl_sdn_ipams,
    _cl_sdn_overview,
    _cl_sdn_pending,
    _cl_sdn_subnet_show,
    _cl_sdn_subnets,
    _cl_sdn_vnet_show,
    _cl_sdn_vnets,
    _cl_sdn_zone_show,
    _cl_sdn_zones,
)
from proxmox.client.auth import AuthManager
from proxmox.client.client import ProxmoxClient


def _client() -> ProxmoxClient:
    return ProxmoxClient("https://pve:8006", AuthManager(), timeout=5)


_BASE = "https://pve:8006/api2/json/cluster/sdn"


class TestSDNOverview:
    def test_overview(self, mock_httpx_client):
        data = [{"id": "sdn", "sdn": "ok"}]
        mock_httpx_client.add_response(url=f"{_BASE}", json={"data": data})
        result = _cl_sdn_overview(argparse.Namespace(), _client())
        assert result == data

    def test_pending(self, mock_httpx_client):
        data = [{"type": "zone", "name": "myzone", "change": "create"}]
        mock_httpx_client.add_response(url=f"{_BASE}/pending", json={"data": data})
        result = _cl_sdn_pending(argparse.Namespace(), _client())
        assert result == data


class TestSDNZones:
    def test_list(self, mock_httpx_client):
        data = [{"zone": "myzone", "type": "simple"}]
        mock_httpx_client.add_response(url=f"{_BASE}/zones", json={"data": data})
        result = _cl_sdn_zones(argparse.Namespace(), _client())
        assert result == data

    def test_show(self, mock_httpx_client):
        data = {"zone": "myzone", "type": "simple", "bridge": "vnet0"}
        mock_httpx_client.add_response(url=f"{_BASE}/zones/myzone", json={"data": data})
        result = _cl_sdn_zone_show(argparse.Namespace(zone="myzone"), _client())
        assert result == data


class TestSDNVnets:
    def test_list(self, mock_httpx_client):
        data = [{"vnet": "vnet0", "zone": "myzone"}]
        mock_httpx_client.add_response(url=f"{_BASE}/vnets", json={"data": data})
        result = _cl_sdn_vnets(argparse.Namespace(), _client())
        assert result == data

    def test_show(self, mock_httpx_client):
        data = {"vnet": "vnet0", "zone": "myzone", "tag": 100}
        mock_httpx_client.add_response(url=f"{_BASE}/vnets/vnet0", json={"data": data})
        result = _cl_sdn_vnet_show(argparse.Namespace(vnet="vnet0"), _client())
        assert result == data


class TestSDNControllers:
    def test_list(self, mock_httpx_client):
        data = [{"controller": "evpn", "type": "evpn"}]
        mock_httpx_client.add_response(url=f"{_BASE}/controllers", json={"data": data})
        result = _cl_sdn_controllers(argparse.Namespace(), _client())
        assert result == data

    def test_show(self, mock_httpx_client):
        data = {"controller": "evpn", "type": "evpn", "peers": "10.0.0.1"}
        mock_httpx_client.add_response(url=f"{_BASE}/controllers/evpn", json={"data": data})
        result = _cl_sdn_controller_show(argparse.Namespace(controller="evpn"), _client())
        assert result == data


class TestSDNSubnets:
    def test_list(self, mock_httpx_client):
        data = [{"subnet": "vnet0-10.0.0.0-24", "cidr": "10.0.0.0/24"}]
        mock_httpx_client.add_response(url=f"{_BASE}/subnets", json={"data": data})
        result = _cl_sdn_subnets(argparse.Namespace(), _client())
        assert result == data

    def test_show(self, mock_httpx_client):
        data = {"subnet": "vnet0-10.0.0.0-24", "cidr": "10.0.0.0/24", "gateway": "10.0.0.1"}
        mock_httpx_client.add_response(
            url=f"{_BASE}/subnets/vnet0-10.0.0.0-24", json={"data": data}
        )
        result = _cl_sdn_subnet_show(
            argparse.Namespace(subnet="vnet0-10.0.0.0-24"), _client()
        )
        assert result == data


class TestSDNPlugins:
    def test_ipams(self, mock_httpx_client):
        data = [{"ipam": "pve", "type": "pve"}]
        mock_httpx_client.add_response(url=f"{_BASE}/ipams", json={"data": data})
        result = _cl_sdn_ipams(argparse.Namespace(), _client())
        assert result == data

    def test_dns(self, mock_httpx_client):
        data = [{"dns": "ad", "type": "ad"}]
        mock_httpx_client.add_response(url=f"{_BASE}/dns", json={"data": data})
        result = _cl_sdn_dns(argparse.Namespace(), _client())
        assert result == data
