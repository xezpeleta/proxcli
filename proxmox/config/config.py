"""Config file loader — reads / writes credentials.json."""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path

from proxmox.client.exceptions import ConfigError
from proxmox.config.models import (
    CREDENTIALS_FILE,
    SYSTEM_CONFIG_DIR,
    USER_CONFIG_DIR,
    Credentials,
)


class ConfigLoader:
    """Loads and persists credentials to a JSON config file.

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
        path = self._find_file()
        if path is None:
            raise ConfigError(
                "No credentials found. Run 'proxmox auth login' first, "
                f"or place a {CREDENTIALS_FILE} in {self._user_dir} or {self._system_dir}."
            )
        return self._read(path)

    def load_or_none(self) -> Credentials | None:
        """Load credentials, returning None if not found."""
        try:
            return self.load()
        except ConfigError:
            return None

    def save(self, credentials: Credentials) -> Path:
        """Persist credentials to the user config directory.

        Creates parent directories and sets restrictive permissions (0o600).
        """
        self._user_dir.mkdir(parents=True, exist_ok=True)
        path = self._user_dir / CREDENTIALS_FILE

        data = credentials.model_dump(mode="json", exclude_none=True)
        payload = json.dumps(data, indent=2)
        path.write_text(payload)

        # Restrict permissions: owner-read/write only
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
        return path

    def clear(self) -> None:
        """Delete the user-level credentials file."""
        path = self._user_dir / CREDENTIALS_FILE
        if path.exists():
            path.unlink()

    def exists(self) -> bool:
        """Return True if a credentials file can be found."""
        return self._find_file() is not None

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _find_file(self) -> Path | None:
        for base in (self._user_dir, self._system_dir):
            p = base / CREDENTIALS_FILE
            if p.exists():
                return p
        return None

    def _read(self, path: Path) -> Credentials:
        try:
            raw = json.loads(path.read_text())
        except json.JSONDecodeError as exc:
            raise ConfigError(f"Invalid JSON in {path}: {exc}") from exc

        try:
            return Credentials(**raw)
        except Exception as exc:
            raise ConfigError(f"Invalid credentials in {path}: {exc}") from exc
