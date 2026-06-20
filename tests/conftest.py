"""Shared test fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

from proxmox.client.auth import AuthManager
from proxmox.client.client import ProxmoxClient


@pytest.fixture
def auth_manager():
    """Return a fresh AuthManager."""
    return AuthManager()


@pytest.fixture
def client(auth_manager):
    """Return a ProxmoxClient pointing at a fake local URL."""
    return ProxmoxClient(
        base_url="https://pve:8006",
        auth_manager=auth_manager,
        timeout=5,
    )


@pytest.fixture
def mock_httpx_client(httpx_mock):
    """Return httpx_mock for stubbing HTTP."""
    return httpx_mock


@pytest.fixture
def sample_credentials_dict():
    """Sample credentials as a plain dict."""
    return {
        "url": "https://pve:8006",
        "username": "root@pam",
        "auth_method": "password",
        "password": "secret",
        "verify_tls": True,
    }


@pytest.fixture
def temp_config_dir(tmp_path) -> Path:
    """Temporary config directory."""
    return tmp_path / "config"
