"""Tests for ConfigLoader."""

from __future__ import annotations

import json
import stat

import pytest

from proxmox.client.exceptions import ConfigError
from proxmox.config.config import ConfigLoader
from proxmox.config.models import AuthMethod, Credentials


class TestConfigLoader:
    def test_save_and_load(self, temp_config_dir, sample_credentials_dict):
        """Credentials can be saved and loaded back."""
        loader = ConfigLoader(user_dir=temp_config_dir)
        creds = Credentials(**sample_credentials_dict)
        path = loader.save(creds)

        assert path.exists()
        loaded = loader.load()
        assert loaded.url == "https://pve:8006"
        assert loaded.username == "root@pam"
        assert loaded.auth_method == AuthMethod.PASSWORD
        assert loaded.password == "secret"

    def test_load_none_when_missing(self, temp_config_dir):
        """load_or_none returns None when no config file exists."""
        loader = ConfigLoader(user_dir=temp_config_dir)
        assert loader.load_or_none() is None
        assert loader.exists() is False

    def test_load_raises_when_missing(self, temp_config_dir):
        """load() raises ConfigError when no config file exists."""
        loader = ConfigLoader(user_dir=temp_config_dir)
        with pytest.raises(ConfigError, match="No credentials found"):
            loader.load()

    def test_clear(self, temp_config_dir, sample_credentials_dict):
        """clear() removes the credentials file."""
        loader = ConfigLoader(user_dir=temp_config_dir)
        creds = Credentials(**sample_credentials_dict)
        loader.save(creds)
        assert loader.exists()

        loader.clear()
        assert loader.exists() is False

    def test_file_permissions(self, temp_config_dir, sample_credentials_dict):
        """Saved credentials file has 0o600 permissions."""
        loader = ConfigLoader(user_dir=temp_config_dir)
        creds = Credentials(**sample_credentials_dict)
        path = loader.save(creds)

        file_mode = path.stat().st_mode
        expected_mode = stat.S_IRUSR | stat.S_IWUSR
        assert stat.S_IMODE(file_mode) == expected_mode

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
        """API token credentials are saved and loaded."""
        loader = ConfigLoader(user_dir=temp_config_dir)
        creds = Credentials(
            url="https://pve:8006",
            username="root@pam",
            auth_method=AuthMethod.API_TOKEN,
            api_token_id="my-token",
            api_token_secret="my-secret",
        )
        loader.save(creds)
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
