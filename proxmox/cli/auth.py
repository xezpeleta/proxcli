"""`proxmox auth` subcommand — show authentication status."""

from __future__ import annotations

import argparse

from proxmox.client.client import ProxmoxClient
from proxmox.config.config import ConfigLoader


def register_auth_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the `proxmox auth` subcommand tree."""
    auth_parser = subparsers.add_parser("auth", help="Show authentication status")
    auth_sub = auth_parser.add_subparsers(dest="action", title="actions", required=True)

    # --- auth status ---
    status = auth_sub.add_parser("status", help="Show current authentication status")
    status.set_defaults(func=_auth_status)


def _auth_status(args: argparse.Namespace, client: ProxmoxClient | None = None) -> dict:
    """Display current authentication status."""
    loader = ConfigLoader()
    creds = loader.load_or_none()
    if creds is None:
        return {"status": "not authenticated"}

    found_path = loader.find_file()
    return {
        "status": "authenticated",
        "url": creds.url,
        "username": creds.username,
        "auth_method": creds.auth_method.value,
        "verify_tls": creds.verify_tls,
        "config_file": str(found_path) if found_path else "unknown",
    }
