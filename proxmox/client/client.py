"""HTTP client for the Proxmox VE REST API."""

from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from typing import Any

import httpx

from proxmox.client.auth import AuthManager
from proxmox.client.exceptions import AuthError, ProxmoxAPIError


def _log_line(entry: dict) -> str:
    """Format a log entry dict as a single text line."""
    ts = entry.get("time", "")
    if isinstance(ts, (int, float)):
        try:
            ts = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        except (OSError, ValueError):
            ts = str(ts)
    elif not isinstance(ts, str):
        ts = str(ts)

    parts = [ts]
    tag = entry.get("tag", "")
    node = entry.get("node", "")
    if tag:
        parts.append(f"[{tag}]")
    if node:
        parts.append(f"[{node}]")
    msg = entry.get("msg", "")
    parts.append(msg)
    return " ".join(parts)


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
        content: str | None = None,
    ) -> dict[str, Any] | list[Any]:
        """Send an HTTP request and unwrap the Proxmox JSON envelope.

        Returns ``response.json()["data"]`` on success.

        Set ``content`` to send a raw string body (e.g. pre-encoded form data)
        instead of ``data`` which gets form-encoded by httpx.
        """
        path = self._normalise_path(path)
        full_url = f"{self._base_url}/api2/json{path}"

        self._debug(f"{method} {full_url}")
        if content:
            self._debug(f"  content: {content[:200]}")
        elif data:
            self._debug(f"  body: {data}")

        if self._dry_run:
            self._print_dry_run(method, full_url, data or {"content": content})
            return {}

        return self._send_with_retry(method, full_url, params, data, content)

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
        content: str | None = None,
    ) -> dict[str, Any] | list[Any]:
        last_exc: Exception | None = None

        for attempt in range(self._max_retries + 1):
            try:
                return self._send_one(method, url, params, data, content)
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
        content: str | None = None,
    ) -> dict[str, Any] | list[Any]:
        headers = self._auth.get_headers()

        # Build the httpx kwargs
        httpx_kwargs: dict[str, Any] = dict(
            method=method,
            url=url,
            params=params,
            headers=headers,
            timeout=self._timeout,
            verify=self._verify_tls,
        )
        if content is not None:
            httpx_kwargs["content"] = content
            httpx_kwargs["headers"] = {**headers, "Content-Type": "application/x-www-form-urlencoded"}
        else:
            httpx_kwargs["data"] = data

        try:
            resp = httpx.request(**httpx_kwargs)
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
            retry_headers = self._auth.get_headers()
            retry_kwargs = dict(httpx_kwargs)
            retry_kwargs["headers"] = retry_headers
            resp = httpx.request(**retry_kwargs)

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

    # ------------------------------------------------------------------
    # Task log streaming
    # ------------------------------------------------------------------

    def stream_task_log(self, upid: str, *, follow: bool = False) -> None:
        """Stream task log lines to stdout.

        Args:
            upid: Task UPID string (e.g. UPID:pve01:00000010:...).
            follow: If True, keep polling until task exits.
        """
        import sys

        node = self._extract_node_from_upid(upid)
        if not node:
            print(f"Error: could not extract node from UPID: {upid}", file=sys.stderr)
            return

        if self._dry_run:
            self._print_dry_run("GET", f"{self._base_url}/api2/json/nodes/{node}/tasks/{upid}/log", None)
            if follow:
                print("[dry-run] --follow would poll /tasks/{upid}/status until stopped")
            return

        start = 0
        seen_lines: set[int] = set()

        while True:
            try:
                log_data = self.request("GET", f"/nodes/{node}/tasks/{upid}/log", params={"start": start})
            except ProxmoxAPIError:
                if not follow:
                    break
                time.sleep(1)
                continue

            if isinstance(log_data, dict):
                log_data = log_data.get("data", []) if "data" in log_data else []

            if isinstance(log_data, list):
                for entry in log_data:
                    if not isinstance(entry, dict):
                        continue
                    n = entry.get("n", 0)
                    if n in seen_lines:
                        continue
                    seen_lines.add(n)
                    line = entry.get("t", "")
                    print(line)

            # Check if task is done
            if follow:
                try:
                    status_data = self.request("GET", f"/nodes/{node}/tasks/{upid}/status")
                    if isinstance(status_data, dict):
                        status = status_data.get("status")
                        if status == "stopped":
                            exit_code = status_data.get("exitstatus")
                            if exit_code is not None:
                                print(f"\nTask completed with exit code: {exit_code}")
                            break
                except ProxmoxAPIError:
                    pass

            if not follow:
                break

            start = len(seen_lines)
            time.sleep(1)

    @staticmethod
    def _extract_node_from_upid(upid: str) -> str | None:
        """Parse node name from a Proxmox UPID string: UPID:{node}:..."""
        parts = upid.split(":")
        if len(parts) >= 2:
            return parts[1]
        return None

    def stream_log(
        self,
        path: str,
        *,
        follow: bool = False,
        params: dict | None = None,
    ) -> None:
        """Stream log entries from a polling endpoint (cluster/log, node/ceph/log).

        Args:
            path: API path to poll (e.g., '/cluster/log').
            follow: If True, keep polling for new entries (Ctrl+C to stop).
            params: Optional query params (e.g., {'max': 100}).
        """
        base_params = dict(params) if params else {}

        if self._dry_run:
            self._print_dry_run("GET", f"{self._base_url}/api2/json{path}", base_params)
            if follow:
                print("[dry-run] --follow would poll until Ctrl+C")
            return

        seen: set[str] = set()

        try:
            while True:
                try:
                    data = self.request("GET", path, params=base_params)
                except ProxmoxAPIError:
                    if not follow:
                        break
                    time.sleep(1)
                    continue

                if not isinstance(data, list):
                    break

                new_entries = []
                for entry in data:
                    eid = entry.get("id", "")
                    ekey = f"{entry.get('time', '')}:{eid}"
                    if ekey not in seen:
                        seen.add(ekey)
                        new_entries.append(entry)

                # Print new entries oldest-first
                try:
                    for entry in reversed(new_entries):
                        line = _log_line(entry)
                        print(line, flush=True)
                except BrokenPipeError:
                    return

                if not follow:
                    break

                time.sleep(1)
        except (KeyboardInterrupt, Exception):
            pass
