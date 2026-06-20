"""Config file loader — read-only access to credentials.json.

proxcli never creates, modifies, or deletes this file.
Users must create it manually (e.g. via a text editor).
"""

from __future__ import annotations

import json
from pathlib import Path

from proxmox.client.exceptions import ConfigError
from proxmox.config.models import (
    CREDENTIALS_FILE,
    SYSTEM_CONFIG_DIR,
    USER_CONFIG_DIR,
    Credentials,
)


class ConfigLoader:
    """Read-only loader for credentials from a JSON config file.

    Priority:
    1. ~/.config/proxmox-cli/credentials.json  (user)
    2. /etc/proxmox-cli/credentials.json        (system)
    """

    def __init__(self, user_dir: Path | None = None, system_dir: Path | None = None):
        self._user_dir = user_dir or USER_CONFIG_DIR
        self._system_dir = system_dir or SYSTEM_CONFIG_DIR

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load(self) -> Credentials:
        """Load credentials from disk. Raises ConfigError if not found."""
        path = self.find_file()
        if path is None:
            user_path = self._user_dir / CREDENTIALS_FILE
            sys_path = self._system_dir / CREDENTIALS_FILE
            raise ConfigError(
                f"No credentials found. Create {user_path} or {sys_path} "
                "with your Proxmox credentials."
            )
        return self._read(path)

    def load_or_none(self) -> Credentials | None:
        """Load credentials, returning None if not found."""
        try:
            return self.load()
        except ConfigError:
            return None

    def find_file(self) -> Path | None:
        """Return the path to the credentials file, or None."""
        for base in (self._user_dir, self._system_dir):
            p = base / CREDENTIALS_FILE
            if p.exists():
                return p
        return None

    def exists(self) -> bool:
        """Return True if a credentials file can be found."""
        return self.find_file() is not None

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _read(self, path: Path) -> Credentials:
        try:
            raw = json.loads(path.read_text())
        except json.JSONDecodeError as exc:
            raise ConfigError(f"Invalid JSON in {path}: {exc}") from exc

        try:
            return Credentials(**raw)
        except Exception as exc:
            raise ConfigError(f"Invalid credentials in {path}: {exc}") from exc
