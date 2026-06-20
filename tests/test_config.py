"""Tests for ConfigLoader (read-only)."""

from __future__ import annotations

import json

import pytest

from proxmox.client.exceptions import ConfigError
from proxmox.config.config import ConfigLoader
from proxmox.config.models import AuthMethod, Credentials


class TestConfigLoader:
    def test_load(self, temp_config_dir):
        """Credentials can be loaded from a config file."""
        config_file = temp_config_dir / "credentials.json"
        temp_config_dir.mkdir(parents=True, exist_ok=True)
        config_file.write_text(
            json.dumps(
                {
                    "url": "https://pve:8006",
                    "username": "root@pam",
                    "auth_method": "password",
                    "password": "secret",
                    "verify_tls": True,
                }
            )
        )

        loader = ConfigLoader(user_dir=temp_config_dir)
        loaded = loader.load()
        assert loaded.url == "https://pve:8006"
        assert loaded.username == "root@pam"
        assert loaded.auth_method == AuthMethod.PASSWORD
        assert loaded.password == "secret"

    def test_load_or_none_when_missing(self, temp_config_dir):
        """load_or_none returns None when no config file exists."""
        loader = ConfigLoader(user_dir=temp_config_dir)
        assert loader.load_or_none() is None
        assert loader.exists() is False

    def test_load_raises_when_missing(self, temp_config_dir):
        """load() raises ConfigError when no config file exists."""
        loader = ConfigLoader(user_dir=temp_config_dir)
        with pytest.raises(ConfigError, match="No credentials found"):
            loader.load()

    def test_exists_when_present(self, temp_config_dir):
        """exists() returns True when the file is present."""
        config_file = temp_config_dir / "credentials.json"
        temp_config_dir.mkdir(parents=True, exist_ok=True)
        config_file.write_text(
            json.dumps(
                {
                    "url": "https://pve:8006",
                    "username": "root@pam",
                    "auth_method": "api_token",
                    "api_token_id": "t",
                    "api_token_secret": "s",
                }
            )
        )

        loader = ConfigLoader(user_dir=temp_config_dir)
        assert loader.exists() is True

    def test_invalid_json(self, temp_config_dir):
        """Malformed JSON raises ConfigError."""
        config_file = temp_config_dir / "credentials.json"
        temp_config_dir.mkdir(parents=True, exist_ok=True)
        config_file.write_text("{ invalid json }")

        loader = ConfigLoader(user_dir=temp_config_dir)
        with pytest.raises(ConfigError, match="Invalid JSON"):
            loader.load()

    def test_invalid_credentials(self, temp_config_dir):
        """Missing required fields raises ConfigError."""
        config_file = temp_config_dir / "credentials.json"
        temp_config_dir.mkdir(parents=True, exist_ok=True)
        config_file.write_text(json.dumps({"url": "https://pve:8006"}))

        loader = ConfigLoader(user_dir=temp_config_dir)
        with pytest.raises(ConfigError, match="Invalid credentials"):
            loader.load()

    def test_api_token_credentials(self, temp_config_dir):
        """API token credentials are loaded correctly."""
        config_file = temp_config_dir / "credentials.json"
        temp_config_dir.mkdir(parents=True, exist_ok=True)
        config_file.write_text(
            json.dumps(
                {
                    "url": "https://pve:8006",
                    "username": "root@pam",
                    "auth_method": "api_token",
                    "api_token_id": "my-token",
                    "api_token_secret": "my-secret",
                }
            )
        )

        loader = ConfigLoader(user_dir=temp_config_dir)
        loaded = loader.load()
        assert loaded.auth_method == AuthMethod.API_TOKEN
        assert loaded.api_token_id == "my-token"
        assert loaded.api_token_secret == "my-secret"
        assert loaded.password is None

    def test_url_validation(self):
        """URL must have http:// or https:// scheme."""
        with pytest.raises(ValueError, match="URL must start with"):
            Credentials(
                url="pve:8006",
                username="root@pam",
                auth_method=AuthMethod.PASSWORD,
                password="secret",
            )

    def test_password_required_for_password_method(self):
        """Password is required when auth_method is PASSWORD."""
        with pytest.raises(ValueError, match="Password is required"):
            Credentials(
                url="https://pve:8006",
                username="root@pam",
                auth_method=AuthMethod.PASSWORD,
            )

    def test_token_id_required_for_token_method(self):
        """API token ID is required when auth_method is API_TOKEN."""
        with pytest.raises(ValueError, match="API token ID is required"):
            Credentials(
                url="https://pve:8006",
                username="root@pam",
                auth_method=AuthMethod.API_TOKEN,
                api_token_secret="secret",
            )
