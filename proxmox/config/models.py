"""Pydantic models for configuration and credentials."""

from __future__ import annotations

import os as _os
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field, field_validator, model_validator


class AuthMethod(str, Enum):
    PASSWORD = "password"
    API_TOKEN = "api_token"


class Credentials(BaseModel):
    """Persisted credentials for a single Proxmox endpoint."""

    url: str = Field(..., description="Proxmox API URL, e.g. https://192.168.1.10:8006")
    username: str = Field(..., description="Username, e.g. root@pam")
    auth_method: AuthMethod = Field(..., description="Authentication method")
    password: str | None = Field(None, description="Password (for password auth)")
    api_token_id: str | None = Field(None, description="Token ID (for token auth)")
    api_token_secret: str | None = Field(None, description="Token secret (for token auth)")
    verify_tls: bool = Field(True, description="Whether to verify TLS certificates")

    @field_validator("url")
    @classmethod
    def url_must_have_scheme(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v.rstrip("/")

    @model_validator(mode="after")
    def validate_auth_fields(self):
        if self.auth_method == AuthMethod.PASSWORD and not self.password:
            raise ValueError("Password is required for password authentication")
        if self.auth_method == AuthMethod.API_TOKEN:
            if not self.api_token_id:
                raise ValueError("API token ID is required for token authentication")
            if not self.api_token_secret:
                raise ValueError("API token secret is required for token authentication")
        return self


# ---------------------------------------------------------------------------
# Config file paths (XDG-compliant, overridable via env var)
# ---------------------------------------------------------------------------

_USER_OVERRIDE = _os.environ.get("PROXMOX_CONFIG_DIR")
USER_CONFIG_DIR = Path(_USER_OVERRIDE) if _USER_OVERRIDE else Path.home() / ".config" / "proxmox-cli"
SYSTEM_CONFIG_DIR = Path("/etc/proxmox-cli")
CREDENTIALS_FILE = "credentials.json"
