"""Authentication manager for Proxmox VE API."""

from __future__ import annotations

from enum import Enum
from typing import Any

import httpx

from proxmox.client.exceptions import AuthError


class AuthMethod(str, Enum):
    PASSWORD = "password"
    API_TOKEN = "api_token"


class AuthManager:
    """Handles Proxmox authentication (password-based ticket or API token).

    For password auth: acquires a ticket and CSRF token via
    POST /api2/json/access/ticket, then injects Cookie + CSRFPreventionToken headers.
    For API token auth: base64-encodes the token and sets an Authorization header.

    Caches credentials in memory for the process lifetime.
    """

    def __init__(self):
        self._method: AuthMethod | None = None
        self._ticket: str | None = None
        self._csrf_token: str | None = None
        self._auth_header: str | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def authenticate_password(
        self, base_url: str, username: str, password: str, *, verify: bool = True
    ) -> None:
        """Acquire a ticket from Proxmox using username + password."""
        url = f"{base_url}/api2/json/access/ticket"
        try:
            resp = httpx.post(
                url,
                data={"username": username, "password": password},
                verify=verify,
                timeout=30,
            )
        except httpx.RequestError as exc:
            raise AuthError(f"Failed to reach Proxmox at {base_url}: {exc}") from exc

        if resp.status_code != 200:
            msg = resp.json().get("message", resp.text)
            raise AuthError(f"Authentication failed: {msg}")

        data = resp.json()["data"]
        self._ticket = data["ticket"]
        self._csrf_token = data["CSRFPreventionToken"]
        self._method = AuthMethod.PASSWORD
        self._auth_header = None

    def set_api_token(self, user: str, token_id: str, secret: str) -> None:
        """Use a Proxmox API token for authentication."""
        self._auth_header = f"PVEAPIToken={user}!{token_id}={secret}"
        self._method = AuthMethod.API_TOKEN
        self._ticket = None
        self._csrf_token = None

    def get_headers(self) -> dict[str, str]:
        """Return the HTTP auth headers needed for the current auth method."""
        if self._method == AuthMethod.API_TOKEN:
            return {"Authorization": self._auth_header or ""}

        if self._method == AuthMethod.PASSWORD:
            headers: dict[str, str] = {}
            if self._ticket:
                headers["Cookie"] = f"PVEAuthCookie={self._ticket}"
            if self._csrf_token:
                headers["CSRFPreventionToken"] = self._csrf_token
            return headers

        return {}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @property
    def is_authenticated(self) -> bool:
        return self._method is not None

    @property
    def method(self) -> AuthMethod | None:
        return self._method

    def clear(self) -> None:
        """Wipe cached credentials."""
        self._method = None
        self._ticket = None
        self._csrf_token = None
        self._auth_header = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize for debugging (never exposes secrets)."""
        return {
            "method": self._method.value if self._method else None,
            "has_ticket": self._ticket is not None,
            "has_csrf": self._csrf_token is not None,
        }
