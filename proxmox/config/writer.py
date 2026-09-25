"""Writer for credentials.json.

This is the **only** module in proxcli that creates or overwrites
``credentials.json``. :class:`~proxmox.config.config.ConfigLoader` remains
strictly read-only for every other code path; the write capability is scoped
exclusively to `proxmox auth setup`, which the user invokes explicitly to
bootstrap their credentials.

The file is written with mode ``0600`` (owner read/write only) and an optional
``.json.bak`` backup of any pre-existing file.
"""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

from proxmox.client.exceptions import ConfigError
from proxmox.config.models import CREDENTIALS_FILE, USER_CONFIG_DIR, Credentials


class ConfigWriter:
    """Write Proxmox credentials to ``credentials.json``."""

    def __init__(self, config_dir: Path | None = None):
        self._dir = config_dir or USER_CONFIG_DIR

    def path(self) -> Path:
        """Return the absolute path that will be written."""
        return self._dir / CREDENTIALS_FILE

    def save(
        self,
        creds: Credentials | dict,
        force: bool = False,
        backup: bool = True,
    ) -> Path:
        """Persist credentials to disk.

        Args:
            creds: A :class:`Credentials` model or a dict with the same keys.
            force: If False and the file already exists, refuse to overwrite
                (raise :class:`ConfigError`). If True, overwrite (after backup).
            backup: If True and overwriting an existing file, copy it to
                ``credentials.json.bak`` first.

        Returns:
            The path written.
        """
        data = self._normalize(creds)
        target = self.path()

        if target.exists():
            if not force:
                raise ConfigError(
                    f"Refusing to overwrite existing {target}. "
                    "Pass force=True (or --force) to replace it."
                )
            if backup:
                bak = target.with_suffix(".json.bak")
                shutil.copy2(target, bak)

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(data, indent=2) + "\n")
        # Restrict to owner only — the file contains a token secret.
        os.chmod(target, 0o600)
        return target

    # ------------------------------------------------------------------

    @staticmethod
    def _normalize(creds: Credentials | dict) -> dict:
        if isinstance(creds, Credentials):
            # exclude_none keeps the file clean (e.g. no "password": null for
            # token auth); the model validators on reload still accept it.
            data = creds.model_dump(exclude_none=True, mode="json")
        elif isinstance(creds, dict):
            # Validate a plain dict by round-tripping through the model so we
            # never write something ConfigLoader cannot read back.
            data = Credentials(**creds).model_dump(exclude_none=True, mode="json")
        else:
            raise ConfigError(f"Unsupported credentials type: {type(creds).__name__}")
        return data
