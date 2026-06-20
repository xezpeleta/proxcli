"""HTTP client for the Proxmox VE REST API."""

from __future__ import annotations

import os
import time
from typing import Any

import httpx

from proxmox.client.auth import AuthManager
from proxmox.client.exceptions import AuthError, ProxmoxAPIError


class ProxmoxClient:
    """Wraps httpx to talk to the Proxmox VE JSON API.

    Handles:
    - Base URL construction (prefixes /api2/json)
    - Auth header injection
    - Timeout control
    - TLS verification toggle
    - Retry on 5xx with exponential backoff
    - Dry-run mode
    - CSRF ticket auto-refresh on 401
    """

    def __init__(
        self,
        base_url: str,
        auth_manager: AuthManager,
        *,
        timeout: int = 30,
        verify_tls: bool = True,
        dry_run: bool = False,
        retries: int = 3,
        verbose: bool = False,
    ):
        # Normalise trailing slash
        self._base_url = base_url.rstrip("/")
        self._auth = auth_manager
        self._timeout = timeout
        self._verify_tls = verify_tls
        self._dry_run = dry_run
        self._max_retries = retries
        self._verbose = verbose
        self._username: str | None = None
        self._password: str | None = None

    # ------------------------------------------------------------------
    # Public HTTP methods
    # ------------------------------------------------------------------

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[Any]:
        """Send an HTTP request and unwrap the Proxmox JSON envelope.

        Returns ``response.json()["data"]`` on success.
        """
        path = self._normalise_path(path)
        full_url = f"{self._base_url}/api2/json{path}"

        self._debug(f"{method} {full_url}")
        if data:
            self._debug(f"  body: {data}")

        if self._dry_run:
            self._print_dry_run(method, full_url, data)
            return {}

        return self._send_with_retry(method, full_url, params, data)

    def get(self, path: str, *, params: dict[str, Any] | None = None) -> dict[str, Any] | list[Any]:
        return self.request("GET", path, params=params)

    def post(
        self, path: str, *, data: dict[str, Any] | None = None
    ) -> dict[str, Any] | list[Any]:
        return self.request("POST", path, data=data)

    def put(
        self, path: str, *, data: dict[str, Any] | None = None
    ) -> dict[str, Any] | list[Any]:
        return self.request("PUT", path, data=data)

    def delete(
        self, path: str, *, params: dict[str, Any] | None = None
    ) -> dict[str, Any] | list[Any]:
        return self.request("DELETE", path, params=params)

    def upload(
        self,
        node: str,
        storage: str,
        file_path: str,
        *,
        content_type: str = "iso",
    ) -> dict[str, Any]:
        """Upload a file to a storage via multipart/form-data.

        Args:
            node: Target node name.
            storage: Storage ID (e.g. 'local').
            file_path: Path to the local file to upload.
            content_type: Proxmox content type ('iso', 'vztmpl', 'import').
        """
        path = f"/nodes/{node}/storage/{storage}/upload"
        full_url = f"{self._base_url}/api2/json{path}"

        if self._dry_run:
            print(f"POST {full_url}")
            print(f"Headers: {self._auth.get_headers()}")
            print(f"File: {file_path} (content={content_type})")
            return {}

        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        filename = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)

        self._debug(f"POST {full_url}")
        self._debug(f"  file: {file_path} ({file_size} bytes)")

        headers = self._auth.get_headers()

        with open(file_path, "rb") as f:
            try:
                resp = httpx.post(
                    full_url,
                    files={"filename": (filename, f, "application/octet-stream")},
                    data={"content": content_type},
                    headers=headers,
                    timeout=self._timeout,
                    verify=self._verify_tls,
                )
            except httpx.RequestError as exc:
                msg = str(exc)
                if "SSL" in msg or "certificate" in msg.lower():
                    msg += "\nHint: use --insecure to skip TLS verification"
                raise ProxmoxAPIError(0, {"message": msg}, full_url) from exc

        self._debug(f"  ← {resp.status_code}")

        if not (200 <= resp.status_code < 300):
            try:
                body = resp.json()
            except Exception:
                body = {"message": resp.text}
            raise ProxmoxAPIError(resp.status_code, body, full_url)

        envelope = resp.json()
        return envelope.get("data", envelope)

    def set_credentials(self, username: str, password: str) -> None:
        """Store credentials for lazy / auto-refresh authentication."""
        self._username = username
        self._password = password

    def authenticate(self) -> None:
        """Explicitly authenticate the client (password method)."""
        if self._username and self._password:
            self._auth.authenticate_password(
                self._base_url, self._username, self._password, verify=self._verify_tls
            )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    def _normalise_path(path: str) -> str:
        if not path.startswith("/"):
            path = "/" + path
        return path

    def _send_with_retry(
        self,
        method: str,
        url: str,
        params: dict[str, Any] | None,
        data: dict[str, Any] | None,
    ) -> dict[str, Any] | list[Any]:
        last_exc: Exception | None = None

        for attempt in range(self._max_retries + 1):
            try:
                return self._send_one(method, url, params, data)
            except AuthError:
                raise  # don't retry auth errors
            except ProxmoxAPIError as exc:
                if exc.status_code < 500:
                    raise
                last_exc = exc
                if attempt < self._max_retries:
                    delay = 2**attempt
                    self._debug(f"  ⏳ retry {attempt + 1}/{self._max_retries} in {delay}s ...")
                    time.sleep(delay)
            except httpx.TimeoutException as exc:
                last_exc = exc
                if attempt < self._max_retries:
                    delay = 2**attempt
                    self._debug(f"  ⏳ timeout, retry {attempt + 1}/{self._max_retries} in {delay}s ...")
                    time.sleep(delay)

        if isinstance(last_exc, ProxmoxAPIError):
            raise last_exc
        raise ProxmoxAPIError(0, {"message": str(last_exc)}, url)

    def _send_one(
        self,
        method: str,
        url: str,
        params: dict[str, Any] | None,
        data: dict[str, Any] | None,
    ) -> dict[str, Any] | list[Any]:
        headers = self._auth.get_headers()

        try:
            resp = httpx.request(
                method=method,
                url=url,
                params=params,
                data=data,
                headers=headers,
                timeout=self._timeout,
                verify=self._verify_tls,
            )
        except httpx.TimeoutException:
            raise
        except httpx.RequestError as exc:
            # Wrap connection / TLS errors
            msg = str(exc)
            if "SSL" in msg or "certificate" in msg.lower():
                msg += "\nHint: use --insecure to skip TLS verification"
            raise ProxmoxAPIError(0, {"message": msg}, url) from exc

        self._debug(f"  ← {resp.status_code}")

        if resp.status_code == 401 and self._username and self._password:
            # Auto-refresh ticket once
            self._debug("  🔄 re-authenticating ...")
            self.authenticate()
            headers = self._auth.get_headers()
            resp = httpx.request(
                method=method,
                url=url,
                params=params,
                data=data,
                headers=headers,
                timeout=self._timeout,
                verify=self._verify_tls,
            )

        if not (200 <= resp.status_code < 300):
            try:
                body = resp.json()
            except Exception:
                body = {"message": resp.text}
            raise ProxmoxAPIError(resp.status_code, body, url)

        # Unwrap Proxmox JSON envelope
        envelope = resp.json()
        return envelope.get("data", envelope)

    def _print_dry_run(self, method: str, url: str, data: dict[str, Any] | None) -> None:
        print(f"{method} {url}")
        print(f"Headers: {self._auth.get_headers()}")
        if data:
            print(f"Body: {data}")

    def _debug(self, message: str) -> None:
        if self._verbose:
            import sys

            print(f"[proxmox] {message}", file=sys.stderr)
