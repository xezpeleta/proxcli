"""Tests for ConfigWriter (the sole writer for credentials.json)."""

from __future__ import annotations

import json
import os

import pytest

from proxmox.client.exceptions import ConfigError
from proxmox.config.config import ConfigLoader
from proxmox.config.models import AuthMethod, Credentials
from proxmox.config.writer import ConfigWriter


def _token_creds() -> dict:
    return {
        "url": "https://pve:8006",
        "username": "root@pam",
        "auth_method": "api_token",
        "api_token_id": "proxcli",
        "api_token_secret": "secret-xyz",
        "verify_tls": False,
    }


class TestConfigWriter:
    def test_writes_valid_json_with_0600(self, temp_config_dir):
        """save() writes JSON readable by ConfigLoader with mode 0600."""
        path = ConfigWriter(config_dir=temp_config_dir).save(_token_creds())
        assert path.exists()
        mode = os.stat(path).st_mode & 0o777
        assert mode == 0o600
        data = json.loads(path.read_text())
        assert data["api_token_id"] == "proxcli"
        # Round-trips through the read-only loader.
        loaded = ConfigLoader(user_dir=temp_config_dir).load()
        assert loaded.username == "root@pam"
        assert loaded.auth_method == AuthMethod.API_TOKEN

    def test_accepts_credentials_model(self, temp_config_dir):
        """A Credentials model can be saved directly."""
        creds = Credentials(**_token_creds())
        path = ConfigWriter(config_dir=temp_config_dir).save(creds)
        assert path.exists()

    def test_creates_parent_directory(self, tmp_path):
        """save() creates the config directory if it does not exist."""
        target = tmp_path / "nested" / "dir"
        path = ConfigWriter(config_dir=target).save(_token_creds())
        assert path.exists()

    def test_refuses_overwrite_without_force(self, temp_config_dir):
        """An existing file is not overwritten unless force=True."""
        w = ConfigWriter(config_dir=temp_config_dir)
        w.save(_token_creds())
        with pytest.raises(ConfigError, match="Refusing to overwrite"):
            w.save(_token_creds(), force=False)

    def test_force_overwrites_and_keeps_backup(self, temp_config_dir):
        """force=True overwrites and writes a .json.bak of the old file."""
        w = ConfigWriter(config_dir=temp_config_dir)
        old = w.save(_token_creds())
        old_secret = json.loads(old.read_text())["api_token_secret"]

        new = dict(_token_creds(), api_token_secret="rotated")
        path = w.save(new, force=True)
        assert json.loads(path.read_text())["api_token_secret"] == "rotated"

        bak = path.with_suffix(".json.bak")
        assert bak.exists()
        assert json.loads(bak.read_text())["api_token_secret"] == old_secret

    def test_backup_disabled(self, temp_config_dir):
        """backup=False skips writing the .bak file."""
        w = ConfigWriter(config_dir=temp_config_dir)
        w.save(_token_creds())
        w.save(dict(_token_creds(), api_token_secret="x"), force=True, backup=False)
        assert not (w.path().with_suffix(".json.bak")).exists()

    def test_invalid_dict_rejected(self, temp_config_dir):
        """A dict missing required fields is rejected (validated via model)."""
        bad = {"url": "https://pve:8006"}  # missing username, auth_method, ...
        with pytest.raises(Exception):
            ConfigWriter(config_dir=temp_config_dir).save(bad)

    def test_excludes_none_fields(self, temp_config_dir):
        """None fields (e.g. password for token auth) are omitted from the file."""
        path = ConfigWriter(config_dir=temp_config_dir).save(_token_creds())
        data = json.loads(path.read_text())
        assert "password" not in data  # token auth -> no password key
