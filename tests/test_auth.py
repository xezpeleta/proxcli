"""Tests for AuthManager."""

from __future__ import annotations

import pytest

from proxmox.client.auth import AuthMethod
from proxmox.client.exceptions import AuthError


class TestAuthManager:
    def test_initial_state(self, auth_manager):
        """New AuthManager is not authenticated."""
        assert auth_manager.is_authenticated is False
        assert auth_manager.method is None
        assert auth_manager.get_headers() == {}

    def test_password_auth(self, mock_httpx_client, auth_manager):
        """Password auth acquires ticket and CSRF token."""
        mock_httpx_client.add_response(
            method="POST",
            url="https://pve:8006/api2/json/access/ticket",
            json={
                "data": {
                    "ticket": "PVE:test-ticket",
                    "CSRFPreventionToken": "csrf-abc123",
                    "username": "root@pam",
                }
            },
        )
        auth_manager.authenticate_password(
            "https://pve:8006", "root@pam", "secret", verify=True
        )
        assert auth_manager.is_authenticated is True
        assert auth_manager.method == AuthMethod.PASSWORD

        headers = auth_manager.get_headers()
        assert headers["Cookie"] == "PVEAuthCookie=PVE:test-ticket"
        assert headers["CSRFPreventionToken"] == "csrf-abc123"

    def test_password_auth_failure(self, mock_httpx_client, auth_manager):
        """Password auth failure raises AuthError."""
        mock_httpx_client.add_response(
            method="POST",
            url="https://pve:8006/api2/json/access/ticket",
            status_code=401,
            json={"message": "authentication failure"},
        )
        with pytest.raises(AuthError, match="authentication failure"):
            auth_manager.authenticate_password(
                "https://pve:8006", "root@pam", "wrong", verify=True
            )

    def test_api_token_auth(self, auth_manager):
        """API token sets Authorization header."""
        auth_manager.set_api_token("root@pam", "my-token", "my-secret")
        assert auth_manager.is_authenticated is True
        assert auth_manager.method == AuthMethod.API_TOKEN

        headers = auth_manager.get_headers()
        assert headers["Authorization"] == "PVEAPIToken=root@pam!my-token=my-secret"
        assert "Cookie" not in headers
        assert "CSRFPreventionToken" not in headers

    def test_clear(self, auth_manager):
        """clear() wipes cached credentials."""
        auth_manager.set_api_token("root@pam", "t", "s")
        assert auth_manager.is_authenticated is True

        auth_manager.clear()
        assert auth_manager.is_authenticated is False
        assert auth_manager.get_headers() == {}

    def test_to_dict_no_secrets(self, auth_manager):
        """to_dict() never exposes secrets."""
        auth_manager.set_api_token("root@pam", "t", "s")
        info = auth_manager.to_dict()
        assert info["method"] == "api_token"
        assert "PVEAPIToken" not in str(info)
        assert "secret" not in str(info)
