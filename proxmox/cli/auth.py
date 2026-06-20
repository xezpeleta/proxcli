"""`proxmox auth` subcommand — manage credentials."""

from __future__ import annotations

import argparse
import sys

from proxmox.client.auth import AuthManager
from proxmox.client.client import ProxmoxClient
from proxmox.config.config import ConfigLoader
from proxmox.config.models import AuthMethod, Credentials
from proxmox.utils.logging import log_error, log_info


def register_auth_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the `proxmox auth` subcommand tree."""
    auth_parser = subparsers.add_parser("auth", help="Manage Proxmox credentials")
    auth_sub = auth_parser.add_subparsers(dest="action", title="actions", required=True)

    # --- auth login ---
    login = auth_sub.add_parser("login", help="Authenticate and save credentials")
    login.add_argument("--url", required=True, help="Proxmox API URL")
    login.add_argument("--username", required=True, help="Username (e.g. root@pam)")
    login.add_argument("--password", help="Password")
    login.add_argument("--password-stdin", action="store_true", help="Read password from stdin")
    login.add_argument("--api-token", help="API token (user!tokenid=secret)")
    login.add_argument(
        "--insecure", action="store_true", help="Skip TLS verification (save preference)"
    )
    login.set_defaults(func=_auth_login)

    # --- auth status ---
    status = auth_sub.add_parser("status", help="Show current authentication status")
    status.set_defaults(func=_auth_status)

    # --- auth clear ---
    clear = auth_sub.add_parser("clear", help="Remove saved credentials")
    clear.set_defaults(func=_auth_clear)


def _auth_login(args: argparse.Namespace, client: ProxmoxClient | None = None) -> dict | None:
    """Authenticate and persist credentials."""
    loader = ConfigLoader()
    url = args.url.rstrip("/")

    # Determine password
    password = args.password
    if args.password_stdin:
        password = sys.stdin.readline().rstrip("\n")

    verify_tls = not args.insecure

    # Validate credentials
    if args.api_token:
        parts = args.api_token.split("=", 1)
        if len(parts) != 2:
            log_error("Invalid --api-token format. Expected: user!tokenid=secret")
            sys.exit(1)
        user_token, secret = parts
        if "!" in user_token:
            user, token_id = user_token.split("!", 1)
        else:
            user = args.username
            token_id = user_token
        creds = Credentials(
            url=url,
            username=user,
            auth_method=AuthMethod.API_TOKEN,
            api_token_id=token_id,
            api_token_secret=secret,
            verify_tls=verify_tls,
        )
        # Quick validation: attempt a version check
        auth_mgr = AuthManager()
        auth_mgr.set_api_token(user, token_id, secret)
        test_client = ProxmoxClient(url, auth_mgr, verify_tls=verify_tls, timeout=10)
        try:
            test_client.get("/version")
        except Exception as exc:
            log_error(f"Failed to validate token: {exc}")
            sys.exit(1)
    elif password:
        creds = Credentials(
            url=url,
            username=args.username,
            auth_method=AuthMethod.PASSWORD,
            password=password,
            verify_tls=verify_tls,
        )
        # Quick validation: attempt a version check
        auth_mgr = AuthManager()
        auth_mgr.authenticate_password(url, args.username, password, verify=verify_tls)
        test_client = ProxmoxClient(url, auth_mgr, verify_tls=verify_tls, timeout=10)
        try:
            test_client.get("/version")
        except Exception as exc:
            log_error(f"Failed to validate credentials: {exc}")
            sys.exit(1)
    else:
        log_error("Either --password, --password-stdin, or --api-token is required")
        sys.exit(1)

    path = loader.save(creds)
    log_info(f"Credentials saved to {path}")
    return {"status": "authenticated", "url": url, "user": creds.username}


def _auth_status(args: argparse.Namespace, client: ProxmoxClient | None = None) -> dict:
    """Display current authentication status."""
    loader = ConfigLoader()
    creds = loader.load_or_none()
    if creds is None:
        return {"status": "not authenticated"}

    return {
        "status": "authenticated",
        "url": creds.url,
        "username": creds.username,
        "auth_method": creds.auth_method.value,
        "verify_tls": creds.verify_tls,
        "config_file": str(loader._user_dir / "credentials.json"),
    }


def _auth_clear(args: argparse.Namespace, client: ProxmoxClient | None = None) -> dict:
    """Remove saved credentials."""
    loader = ConfigLoader()
    loader.clear()
    log_info("Credentials cleared.")
    return {"status": "cleared"}
