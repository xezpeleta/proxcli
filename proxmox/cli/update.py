"""proxmox update — self-upgrade proxcli from PyPI."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import urllib.request
from importlib.metadata import version

from proxmox.utils.logging import log_error


def register_update_parser(subparsers: argparse._SubParsersAction) -> None:
    update_parser = subparsers.add_parser("update", help="Check for and install proxcli updates")
    update_parser.add_argument(
        "--check",
        action="store_true",
        help="Only check if an update is available (do not install)",
    )
    update_parser.add_argument(
        "--pre",
        action="store_true",
        help="Include pre-release versions when checking",
    )
    update_parser.set_defaults(func=_update, output_format="table")


def _get_latest_version(include_pre: bool = False) -> str:
    """Fetch the latest version tag from PyPI."""
    url = "https://pypi.org/pypi/proxcli/json"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read().decode())
    except Exception as exc:
        raise RuntimeError(f"Failed to query PyPI: {exc}") from exc

    versions = list(data.get("releases", {}).keys())

    if not versions:
        raise RuntimeError("No releases found on PyPI")

    if not include_pre:
        versions = [v for v in versions if _is_stable(v)]
        if not versions:
            raise RuntimeError("No stable releases found on PyPI")

    return max(versions, key=_version_key)


def _is_stable(ver: str) -> bool:
    """Return True if version looks like a stable release (no dev/pre markers)."""
    # Strip epoch if present
    v = ver
    # Simple check: no a/b/rc/dev/post markers
    for marker in ("a", "b", "rc", "dev", "post"):
        if marker in v:
            return False
    return True


def _version_key(ver: str) -> tuple:
    """Parse a version string into a comparable tuple."""
    parts = ver.split(".")
    result = []
    for p in parts:
        # Try int first
        try:
            result.append(int(p))
        except ValueError:
            result.append(p)
    return tuple(result)


def _update(args: argparse.Namespace, client: object | None = None) -> dict | str:
    """Check for updates and optionally install them.

    Returns a dict for the output formatter.
    """
    current = version("proxcli")

    try:
        latest = _get_latest_version(include_pre=args.pre)
    except RuntimeError as exc:
        return {"error": str(exc)}

    up_to_date = _version_key(current) >= _version_key(latest)

    if args.check:
        if up_to_date:
            return {
                "current": current,
                "latest": latest,
                "status": "up-to-date",
                "message": f"proxcli {current} is the latest version.",
            }
        else:
            return {
                "current": current,
                "latest": latest,
                "status": "update-available",
                "message": f"proxcli {latest} is available (you have {current}). Run 'proxmox update' to upgrade.",
            }

    if up_to_date:
        return {
            "current": current,
            "latest": latest,
            "status": "up-to-date",
            "message": f"proxcli {current} is already the latest version.",
        }

    # Run uv tool install
    log_error(f"Upgrading proxcli from {current} to {latest}...", file=sys.stderr)
    try:
        result = subprocess.run(
            ["uv", "tool", "install", "proxcli", "--reinstall"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            error_msg = result.stderr.strip() or result.stdout.strip() or f"exit code {result.returncode}"
            log_error(error_msg)
            return {
                "current": current,
                "latest": latest,
                "status": "error",
                "message": f"Upgrade failed: {error_msg}",
            }
    except FileNotFoundError:
        return {
            "current": current,
            "latest": latest,
            "status": "error",
            "message": "uv not found in PATH. Install uv (https://docs.astral.sh/uv/) or upgrade manually with 'uv tool install proxcli --reinstall'.",
        }
    except subprocess.TimeoutExpired:
        return {
            "current": current,
            "latest": latest,
            "status": "error",
            "message": "Upgrade timed out. Try again or upgrade manually.",
        }

    new_version = version("proxcli")
    return {
        "current": new_version,
        "previous": current,
        "latest": latest,
        "status": "upgraded",
        "message": f"proxcli upgraded from {current} to {new_version}.",
    }
