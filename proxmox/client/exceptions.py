"""Proxmox CLI exceptions."""


class ProxmoxError(Exception):
    """Base exception for proxmox CLI errors."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class ProxmoxAPIError(ProxmoxError):
    """Raised when the Proxmox API returns a non-2xx response."""

    def __init__(self, status_code: int, body: dict | None = None, url: str = ""):
        self.status_code = status_code
        self.body = body or {}
        self.url = url

        # Try to extract a meaningful error message from Proxmox response
        msg = body.get("message", "") if body else ""
        if not msg and isinstance(body, dict) and "errors" in body:
            msg = str(body["errors"])

        message = f"HTTP {status_code}"
        if url:
            message += f" on {url}"
        if msg:
            message += f": {msg}"

        super().__init__(message)


class AuthError(ProxmoxError):
    """Raised when authentication fails."""


class ConfigError(ProxmoxError):
    """Raised when configuration is missing or invalid."""


class NotFoundError(ProxmoxAPIError):
    """Raised when a resource is not found (404)."""
