"""Unit tests for `vm snapshot create` — --wait, --if-not-exists, UPID hint."""

from __future__ import annotations

import argparse

from proxmox.cli.vm import _vm_snapshot_create
from proxmox.client.auth import AuthManager
from proxmox.client.client import ProxmoxClient


def _client() -> ProxmoxClient:
    return ProxmoxClient("https://pve:8006", AuthManager(), timeout=5)


class TestVMSnapshotCreate:
    def test_returns_upid_hint_when_async(self, mock_httpx_client):
        """Without --wait, the UPID is returned with a hint telling the agent
        how to block until the task completes."""
        upid = "UPID:pve01:00000001:00000001:00000001:qmsnapshot::root@pam:"
        mock_httpx_client.add_response(
            method="POST",
            url="https://pve:8006/api2/json/nodes/pve01/qemu/100/snapshot",
            json={"data": upid},
        )
        args = argparse.Namespace(
            vmid=100, snapname="pre-update", node="pve01",
            description=None, vmstate=0,
            if_not_exists=False, wait=False, timeout=300,
        )
        result = _vm_snapshot_create(args, _client())
        assert result["data"] == upid
        assert result["async"] is True
        assert "task wait" in result["hint"]
        assert upid in result["hint"]
        assert result["node"] == "pve01"

    def test_if_not_exists_is_noop_when_present(self, mock_httpx_client):
        """--if-not-exists succeeds without POSTing when the snapshot exists."""
        mock_httpx_client.add_response(
            url="https://pve:8006/api2/json/nodes/pve01/qemu/100/snapshot",
            json={"data": [{"name": "pre-update"}]},
        )
        args = argparse.Namespace(
            vmid=100, snapname="pre-update", node="pve01",
            description=None, vmstate=0,
            if_not_exists=True, wait=False, timeout=300,
        )
        result = _vm_snapshot_create(args, _client())
        assert result["result"] == "already_exists"
        assert "no action taken" in result["hint"]
        # No POST mock was registered, so if one were made pytest-httpx would
        # fail the test with an unmatched request error.

    def test_if_not_exists_creates_when_absent(self, mock_httpx_client):
        """--if-not-exists still creates when the snapshot is missing."""
        mock_httpx_client.add_response(
            url="https://pve:8006/api2/json/nodes/pve01/qemu/100/snapshot",
            json={"data": [{"name": "other-snap"}]},
        )
        upid = "UPID:pve01:00000002:00000002:00000002:qmsnapshot::root@pam:"
        mock_httpx_client.add_response(
            method="POST",
            url="https://pve:8006/api2/json/nodes/pve01/qemu/100/snapshot",
            json={"data": upid},
        )
        args = argparse.Namespace(
            vmid=100, snapname="pre-update", node="pve01",
            description=None, vmstate=0,
            if_not_exists=True, wait=False, timeout=300,
        )
        result = _vm_snapshot_create(args, _client())
        assert result["data"] == upid
        assert result["async"] is True

    def test_wait_blocks_until_task_ok(self, mock_httpx_client):
        """--wait polls the task status endpoint and returns result=ok."""
        upid = "UPID:pve01:00000003:00000003:00000003:qmsnapshot::root@pam:"
        mock_httpx_client.add_response(
            method="POST",
            url="https://pve:8006/api2/json/nodes/pve01/qemu/100/snapshot",
            json={"data": upid},
        )
        mock_httpx_client.add_response(
            url=f"https://pve:8006/api2/json/nodes/pve01/tasks/{upid}/status",
            json={"data": {"status": "stopped", "exitstatus": "OK"}},
        )
        args = argparse.Namespace(
            vmid=100, snapname="pre-update", node="pve01",
            description=None, vmstate=0,
            if_not_exists=False, wait=True, timeout=10,
        )
        result = _vm_snapshot_create(args, _client())
        assert result["result"] == "ok"
        assert result["upid"] == upid
        assert result["snapname"] == "pre-update"
        assert result["node"] == "pve01"

    def test_wait_reports_task_error(self, mock_httpx_client):
        """--wait surfaces a failed task as result=error with the exit status."""
        upid = "UPID:pve01:00000004:00000004:00000004:qmsnapshot::root@pam:"
        mock_httpx_client.add_response(
            method="POST",
            url="https://pve:8006/api2/json/nodes/pve01/qemu/100/snapshot",
            json={"data": upid},
        )
        mock_httpx_client.add_response(
            url=f"https://pve:8006/api2/json/nodes/pve01/tasks/{upid}/status",
            json={"data": {"status": "stopped", "exitstatus": "snapshot disk already exists"}},
        )
        args = argparse.Namespace(
            vmid=100, snapname="pre-update", node="pve01",
            description=None, vmstate=0,
            if_not_exists=False, wait=True, timeout=10,
        )
        result = _vm_snapshot_create(args, _client())
        assert result["result"] == "error"
        assert "snapshot disk already exists" in result["exitstatus"]
