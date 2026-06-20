"""Tests for ProxmoxClient."""

from __future__ import annotations

import httpx
import pytest

from proxmox.client.auth import AuthManager
from proxmox.client.client import ProxmoxClient
from proxmox.client.exceptions import ProxmoxAPIError
from proxmox.utils.helpers import resolve_vmid


class TestProxmoxClient:
    def test_get_success(self, mock_httpx_client):
        """GET returns unwrapped data on 200."""
        mock_httpx_client.add_response(
            url="https://pve:8006/api2/json/nodes",
            json={"data": [{"node": "pve01"}]},
        )
        client = ProxmoxClient("https://pve:8006", AuthManager())
        result = client.get("/nodes")
        assert result == [{"node": "pve01"}]

    def test_post_success(self, mock_httpx_client):
        """POST returns unwrapped data on 200."""
        mock_httpx_client.add_response(
            method="POST",
            url="https://pve:8006/api2/json/nodes/pve01/qemu",
            json={"data": "UPID:pve01:..."},
        )
        client = ProxmoxClient("https://pve:8006", AuthManager())
        result = client.post("/nodes/pve01/qemu", data={"vmid": 100})
        assert result == "UPID:pve01:..."

    def test_put_success(self, mock_httpx_client):
        """PUT returns unwrapped data."""
        mock_httpx_client.add_response(
            method="PUT",
            url="https://pve:8006/api2/json/nodes/pve01/qemu/100/config",
            json={"data": None},
        )
        client = ProxmoxClient("https://pve:8006", AuthManager())
        result = client.put("/nodes/pve01/qemu/100/config", data={"memory": 4096})
        assert result is None

    def test_delete_success(self, mock_httpx_client):
        """DELETE returns unwrapped data."""
        mock_httpx_client.add_response(
            method="DELETE",
            url="https://pve:8006/api2/json/nodes/pve01/qemu/100",
            json={"data": None},
        )
        client = ProxmoxClient("https://pve:8006", AuthManager())
        result = client.delete("/nodes/pve01/qemu/100")
        assert result is None

    def test_error_401(self, mock_httpx_client):
        """401 raises ProxmoxAPIError with status code."""
        mock_httpx_client.add_response(
            url="https://pve:8006/api2/json/nodes",
            status_code=401,
            json={"message": "permission denied - invalid ticket"},
        )
        client = ProxmoxClient("https://pve:8006", AuthManager())
        with pytest.raises(ProxmoxAPIError) as exc_info:
            client.get("/nodes")
        assert exc_info.value.status_code == 401
        assert "permission denied" in str(exc_info.value)

    def test_error_500_with_retries(self, mock_httpx_client):
        """500 raises ProxmoxAPIError after retries."""
        # Add 4 responses (1 initial + 3 retries), all returning 500
        for _ in range(4):
            mock_httpx_client.add_response(
                url="https://pve:8006/api2/json/nodes",
                status_code=500,
                json={"message": "internal error"},
            )
        client = ProxmoxClient("https://pve:8006", AuthManager(), retries=3)
        with pytest.raises(ProxmoxAPIError) as exc_info:
            client.get("/nodes")
        # 4 attempts: initial + 3 retries
        assert len(mock_httpx_client.get_requests()) == 4
        assert exc_info.value.status_code == 500

    def test_dry_run(self, mock_httpx_client, capsys):
        """--dry-run prints the request without executing it."""
        client = ProxmoxClient("https://pve:8006", AuthManager(), dry_run=True)
        result = client.get("/nodes")
        assert result == {}
        captured = capsys.readouterr()
        assert "GET https://pve:8006/api2/json/nodes" in captured.out
        assert len(mock_httpx_client.get_requests()) == 0

    def test_timeout(self, mock_httpx_client):
        """Timeouts are retried and eventually raised."""
        mock_httpx_client.add_exception(httpx.TimeoutException("timed out"))
        client = ProxmoxClient("https://pve:8006", AuthManager(), timeout=1, retries=0)
        with pytest.raises(ProxmoxAPIError) as exc_info:
            client.get("/nodes")
        assert "timed out" in str(exc_info.value)

    def test_path_normalisation(self, mock_httpx_client):
        """Paths without leading slash are normalised."""
        mock_httpx_client.add_response(
            url="https://pve:8006/api2/json/nodes",
            json={"data": []},
        )
        client = ProxmoxClient("https://pve:8006", AuthManager())
        result = client.get("nodes")  # no leading /
        assert result == []

    def test_url_trailing_slash_stripped(self, mock_httpx_client):
        """Trailing slash on base URL is stripped."""
        mock_httpx_client.add_response(
            url="https://pve:8006/api2/json/nodes",
            json={"data": []},
        )
        client = ProxmoxClient("https://pve:8006/", AuthManager())
        result = client.get("/nodes")
        assert result == []


class TestResolveVmid:
    def test_returns_provided_vmid(self, mock_httpx_client):
        """When a vmid is provided, return it without calling the API."""
        client = ProxmoxClient("https://pve:8006", AuthManager())
        result = resolve_vmid(client, 110)
        assert result == 110
        assert len(mock_httpx_client.get_requests()) == 0

    def test_fetches_nextid_when_vmid_is_none(self, mock_httpx_client):
        """When vmid is None, call /cluster/nextid."""
        mock_httpx_client.add_response(
            url="https://pve:8006/api2/json/cluster/nextid",
            json={"data": "102"},
        )
        client = ProxmoxClient("https://pve:8006", AuthManager())
        result = resolve_vmid(client, None)
        assert result == 102
        assert len(mock_httpx_client.get_requests()) == 1

    def test_fetches_nextid_when_vmid_is_zero(self, mock_httpx_client):
        """When vmid is 0, also fetch nextid (0 is not a valid VMID)."""
        mock_httpx_client.add_response(
            url="https://pve:8006/api2/json/cluster/nextid",
            json={"data": "105"},
        )
        client = ProxmoxClient("https://pve:8006", AuthManager())
        result = resolve_vmid(client, 0)
        assert result == 105

    def test_nextid_returns_integer(self, mock_httpx_client):
        """Some Proxmox versions return nextid as integer."""
        mock_httpx_client.add_response(
            url="https://pve:8006/api2/json/cluster/nextid",
            json={"data": 108},
        )
        client = ProxmoxClient("https://pve:8006", AuthManager())
        result = resolve_vmid(client, None)
        assert result == 108


class TestStorageUpload:
    def test_upload_success(self, mock_httpx_client, tmp_path):
        """Upload sends multipart request and returns data."""
        iso_file = tmp_path / "test.iso"
        iso_file.write_bytes(b"fake iso content")

        mock_httpx_client.add_response(
            method="POST",
            url="https://pve:8006/api2/json/nodes/pve01/storage/local/upload",
            json={"data": "file test.iso uploaded"},
        )
        client = ProxmoxClient("https://pve:8006", AuthManager())
        result = client.upload("pve01", "local", str(iso_file))
        assert result == "file test.iso uploaded"

        # Verify the request was multipart
        requests = mock_httpx_client.get_requests()
        assert len(requests) == 1
        assert "multipart/form-data" in requests[0].headers.get("content-type", "")

    def test_upload_dry_run(self, capsys):
        """Upload in dry-run mode prints request without executing."""
        client = ProxmoxClient("https://pve:8006", AuthManager(), dry_run=True)
        result = client.upload("pve01", "local", "/fake/path.iso")
        assert result == {}
        captured = capsys.readouterr()
        assert "POST https://pve:8006/api2/json/nodes/pve01/storage/local/upload" in captured.out
        assert "/fake/path.iso" in captured.out

    def test_upload_file_not_found(self):
        """Upload raises FileNotFoundError for missing files."""
        client = ProxmoxClient("https://pve:8006", AuthManager())
        with pytest.raises(FileNotFoundError, match="File not found"):
            client.upload("pve01", "local", "/nonexistent/file.iso")

    def test_upload_error_response(self, mock_httpx_client, tmp_path):
        """Upload raises ProxmoxAPIError on non-2xx response."""
        iso_file = tmp_path / "test.iso"
        iso_file.write_bytes(b"data")

        mock_httpx_client.add_response(
            method="POST",
            url="https://pve:8006/api2/json/nodes/pve01/storage/local/upload",
            status_code=403,
            json={"message": "permission denied"},
        )
        client = ProxmoxClient("https://pve:8006", AuthManager())
        with pytest.raises(ProxmoxAPIError) as exc_info:
            client.upload("pve01", "local", str(iso_file))
        assert exc_info.value.status_code == 403
