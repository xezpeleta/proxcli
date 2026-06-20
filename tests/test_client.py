"""Tests for ProxmoxClient."""

from __future__ import annotations

import httpx
import pytest

from proxmox.client.auth import AuthManager
from proxmox.client.client import ProxmoxClient
from proxmox.client.exceptions import ProxmoxAPIError


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
