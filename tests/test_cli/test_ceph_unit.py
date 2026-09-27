"""Unit tests for `proxmox ceph osd` and `proxmox ceph pool`.

Exercises the handler logic directly with a mocked HTTP layer
(pytest-httpx), covering:
  - the CRUSH-tree → disk-inventory join that surfaces OSD utilization
  - graceful degradation when the CRUSH tree is unavailable
  - pool ``percent_used`` normalization (0–1 ratio → 0–100 number)
  - surfacing of ``max_avail`` / ``target_size_ratio`` (nearfull signals)
"""

from __future__ import annotations

import argparse

from proxmox.cli.ceph import _ceph_osd, _ceph_pool, _flatten_crush_tree
from proxmox.client.auth import AuthManager
from proxmox.client.client import ProxmoxClient


def _client() -> ProxmoxClient:
    return ProxmoxClient("https://pve:8006", AuthManager(), timeout=5)


# A minimal CRUSH tree: root -> host (pve01) -> one OSD (osd.0).
_CRUSH_TREE = {
    "root": {
        "id": -1,
        "name": "default",
        "type": "root",
        "children": [
            {
                "id": -3,
                "name": "pve01",
                "type": "host",
                "children": [
                    {
                        "id": 0,
                        "name": "osd.0",
                        "type": "osd",
                        "status": "up",
                        "in": 1,
                        "reweight": 1,
                        "percent_used": 65.76,
                        "bytes_used": 631457251328,
                        "total_space": 960193626112,
                    },
                ],
            },
        ],
    }
}


class TestFlattenCrushTree:
    def test_flatten_indexes_osds_by_id(self):
        osds = _flatten_crush_tree(_CRUSH_TREE["root"])
        assert "0" in osds
        assert osds["0"]["percent_used"] == 65.76

    def test_flatten_ignores_non_osd_nodes(self):
        osds = _flatten_crush_tree(_CRUSH_TREE["root"])
        # only the osd leaf is captured, not the host/root
        assert set(osds) == {"0"}

    def test_flatten_handles_nested_tree(self):
        tree = {
            "id": -1, "name": "default", "type": "root",
            "children": [
                {"id": -3, "name": "h1", "type": "host", "children": [
                    {"id": 1, "name": "osd.1", "type": "osd", "status": "up"},
                ]},
                {"id": -4, "name": "h2", "type": "host", "children": [
                    {"id": 2, "name": "osd.2", "type": "osd", "status": "down"},
                ]},
            ],
        }
        osds = _flatten_crush_tree(tree)
        assert set(osds) == {"1", "2"}
        assert osds["2"]["status"] == "down"


class TestCephOSD:
    def test_osd_merges_utilization_from_crush_tree(self, mock_httpx_client):
        """`ceph osd --node` joins disk health with CRUSH-tree utilization."""
        mock_httpx_client.add_response(
            url="https://pve:8006/api2/json/nodes/pve01/ceph/osd",
            json={"data": _CRUSH_TREE},
        )
        mock_httpx_client.add_response(
            url="https://pve:8006/api2/json/nodes/pve01/disks/list",
            json={"data": [
                {"osdid": 0, "devpath": "/dev/sda", "model": "Samsung",
                 "size": 960193626112, "type": "ssd", "health": "PASSED", "wearout": 99},
                {"osdid": -1, "devpath": "/dev/sdb", "model": "Spare",
                 "size": 1000000000, "type": "ssd", "health": "PASSED"},  # non-OSD disk
            ]},
        )

        result = _ceph_osd(argparse.Namespace(node="pve01"), _client())
        assert len(result) == 1  # the osdid=-1 disk is filtered out
        osd = result[0]
        assert osd["osd"] == 0
        assert osd["node"] == "pve01"
        assert osd["device"] == "/dev/sda"
        # utilization fields come from the CRUSH tree
        assert osd["used_pct"] == 65.8          # 65.76 -> round(,1)
        assert osd["used_gb"] == 588.1          # 631457251328 / 1024^3
        assert osd["reweight"] == 1
        assert osd["status"] == "up"
        assert osd["in_cluster"] is True
        # disk-health fields are preserved
        assert osd["health"] == "PASSED"
        assert osd["wearout"] == "99%"

    def test_osd_without_crush_tree_still_reports_disk_health(self, mock_httpx_client):
        """When Ceph/the CRUSH tree is unavailable, utilization is None but
        disk health is still reported (graceful degradation)."""
        # CRUSH tree endpoint returns empty / no root
        mock_httpx_client.add_response(
            url="https://pve:8006/api2/json/nodes/pve01/ceph/osd",
            json={"data": {}},
        )
        mock_httpx_client.add_response(
            url="https://pve:8006/api2/json/nodes/pve01/disks/list",
            json={"data": [
                {"osdid": 0, "devpath": "/dev/sda", "model": "Samsung",
                 "size": 960193626112, "type": "ssd", "health": "PASSED", "wearout": 99},
            ]},
        )

        result = _ceph_osd(argparse.Namespace(node="pve01"), _client())
        assert len(result) == 1
        osd = result[0]
        assert osd["health"] == "PASSED"
        # utilization fields are absent (None)
        assert osd["used_pct"] is None
        assert osd["used_gb"] is None
        assert osd["reweight"] is None
        assert osd["status"] is None

    def test_osd_across_all_nodes_uses_one_crush_tree(self, mock_httpx_client):
        """Without --node, the CRUSH tree (cluster-wide) is fetched once and
        disk health is scanned per-node; both nodes' OSDs get utilization."""
        mock_httpx_client.add_response(
            url="https://pve:8006/api2/json/nodes",
            json={"data": [{"node": "pve01"}, {"node": "pve02"}]},
        )
        mock_httpx_client.add_response(
            url="https://pve:8006/api2/json/nodes/pve01/ceph/osd",
            json={"data": _CRUSH_TREE},
        )
        mock_httpx_client.add_response(
            url="https://pve:8006/api2/json/nodes/pve01/disks/list",
            json={"data": [
                {"osdid": 0, "devpath": "/dev/sda", "model": "X",
                 "size": 960193626112, "type": "ssd", "health": "PASSED"},
            ]},
        )
        mock_httpx_client.add_response(
            url="https://pve:8006/api2/json/nodes/pve02/disks/list",
            json={"data": []},
        )

        result = _ceph_osd(argparse.Namespace(node=None), _client())
        assert len(result) == 1
        assert result[0]["used_pct"] == 65.8


class TestCephPool:
    _POOL_RBD = {
        "pool": 4,
        "pool_name": "rbd_ssd",
        "type": "replicated",
        "size": 3,
        "pg_num": 256,
        "bytes_used": 9709343979465,
        "percent_used": 0.728606104850769,   # 0-1 RATIO (unlike OSD tree!)
        "max_avail": None,
        "target_size_ratio": 100,
        "crush_rule_name": "replicated_ruleset_ssd",
        "application_metadata": {"rbd": {}},
    }
    _POOL_MGR = {
        "pool": 3,
        "pool_name": ".mgr",
        "type": "replicated",
        "size": 3,
        "pg_num": 1,
        "bytes_used": 542584698,
        "percent_used": 0.000150004838360474,
        "max_avail": None,
        "target_size_ratio": None,
        "crush_rule_name": "replicated_ruleset_ssd",
        "application_metadata": {"mgr": {}, "mgr_devicehealth": {}},
    }

    def test_pool_normalizes_percent_used_ratio_to_percent(self, mock_httpx_client):
        """Pool `percent_used` arrives as a 0-1 ratio; output is 0-100."""
        mock_httpx_client.add_response(
            url="https://pve:8006/api2/json/nodes/pve01/ceph/pool",
            json={"data": [self._POOL_RBD]},
        )
        result = _ceph_pool(argparse.Namespace(node="pve01"), _client())
        assert isinstance(result, list)
        pool = result[0]
        assert pool["name"] == "rbd_ssd"
        assert pool["percent_used"] == 72.9          # 0.7286 * 100 -> round(,1)
        assert pool["bytes_used"] == 9709343979465
        assert pool["used_gb"] == 9042.5

    def test_pool_surfaces_nearfull_signals(self, mock_httpx_client):
        """`max_avail` (None when full-ish) and `target_size_ratio` (the
        misconfiguration that distorts capacity) are surfaced verbatim."""
        mock_httpx_client.add_response(
            url="https://pve:8006/api2/json/nodes/pve01/ceph/pool",
            json={"data": [self._POOL_RBD, self._POOL_MGR]},
        )
        result = _ceph_pool(argparse.Namespace(node="pve01"), _client())
        by_name = {p["name"]: p for p in result}
        assert by_name["rbd_ssd"]["max_avail"] is None
        assert by_name["rbd_ssd"]["target_size_ratio"] == 100
        assert by_name[".mgr"]["target_size_ratio"] is None
        # applications are joined + sorted
        assert by_name[".mgr"]["applications"] == "mgr, mgr_devicehealth"

    def test_pool_no_ceph_returns_error(self, mock_httpx_client):
        """When no node has Ceph running, a helpful error is returned."""
        mock_httpx_client.add_response(
            url="https://pve:8006/api2/json/nodes",
            json={"data": [{"node": "pve01"}]},
        )
        mock_httpx_client.add_response(
            url="https://pve:8006/api2/json/nodes/pve01/ceph/pool",
            json={"data": {}},  # not a list -> skipped
        )
        result = _ceph_pool(argparse.Namespace(node=None), _client())
        assert isinstance(result, dict)
        assert "error" in result
