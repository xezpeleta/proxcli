"""Root CLI parser and main entry point."""

from __future__ import annotations

import argparse
import os
import sys
from importlib.metadata import version
from typing import Any

from proxmox.client.auth import AuthManager
from proxmox.client.client import ProxmoxClient
from proxmox.client.exceptions import ConfigError, ProxmoxAPIError, ProxmoxError
from proxmox.config.config import ConfigLoader
from proxmox.config.models import AuthMethod as AuthMethodModel
from proxmox.config.models import Credentials
from proxmox.output.formatter import format_output
from proxmox.utils.logging import log_error


def build_root_parser() -> argparse.ArgumentParser:
    """Build the root argument parser with global flags and subcommands."""
    parser = argparse.ArgumentParser(
        prog="proxmox",
        description="CLI tool to interact with Proxmox VE via the REST API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Global flags
    parser.add_argument("--url", help="Proxmox API URL (e.g. https://pve:8006)")
    parser.add_argument("--username", help="Username (e.g. root@pam)")
    parser.add_argument("--password", help="Password (for password auth)")
    parser.add_argument("--password-stdin", action="store_true", help="Read password from stdin")
    parser.add_argument("--api-token", help="API token in format: user!tokenid=secret")
    parser.add_argument(
        "--output",
        choices=["json", "table", "yaml"],
        default="json",
        help="Output format (default: json)",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Print the API request without executing it"
    )
    parser.add_argument(
        "--insecure", action="store_true", help="Skip TLS certificate verification"
    )
    parser.add_argument(
        "--timeout", type=int, default=30, help="Request timeout in seconds (default: 30)"
    )
    parser.add_argument("--verbose", action="store_true", help="Enable debug output to stderr")
    parser.add_argument(
        "--version", action="version", version=f"proxmox {version('proxcli')}"
    )

    subparsers = parser.add_subparsers(dest="resource", title="resources", required=False)

    # Import and register subcommands
    from proxmox.cli.auth import register_auth_parser
    from proxmox.cli.cluster import register_cluster_parser
    from proxmox.cli.completion import register_completion_parser
    from proxmox.cli.container import register_container_parser
    from proxmox.cli.node import register_node_parser
    from proxmox.cli.pool import register_pool_parser
    from proxmox.cli.storage import register_storage_parser
    from proxmox.cli.tasks import register_task_parser
    from proxmox.cli.vm import register_vm_parser

    register_auth_parser(subparsers)
    register_vm_parser(subparsers)
    register_node_parser(subparsers)
    register_pool_parser(subparsers)
    register_container_parser(subparsers)
    register_storage_parser(subparsers)
    register_cluster_parser(subparsers)
    register_completion_parser(subparsers)
    register_task_parser(subparsers)

    return parser


def _merge_config(args: argparse.Namespace) -> tuple[Credentials | None, dict[str, Any]]:
    """Merge config file, env vars, and CLI flags.

    Returns (credentials, overrides) where overrides has keys: url, username, password,
    api_token_id, api_token_secret, verify_tls. CLI flags win over env vars and config file.
    """
    loader = ConfigLoader()
    creds = loader.load_or_none()

    overrides: dict[str, Any] = {
        "url": None,
        "username": None,
        "password": None,
        "api_token_id": None,
        "api_token_secret": None,
    }

    # Apply config file values first
    if creds:
        overrides["url"] = creds.url
        overrides["username"] = creds.username
        overrides["verify_tls"] = creds.verify_tls
        if creds.auth_method == AuthMethodModel.PASSWORD:
            overrides["password"] = creds.password
        elif creds.auth_method == AuthMethodModel.API_TOKEN:
            overrides["api_token_id"] = creds.api_token_id
            overrides["api_token_secret"] = creds.api_token_secret

    # Env var override
    env_password = os.environ.get("PROXMOX_PASSWORD")
    if env_password:
        overrides["password"] = env_password

    # CLI flag overrides (highest priority)
    if args.url:
        overrides["url"] = args.url
    if args.username:
        overrides["username"] = args.username
    if args.password:
        overrides["password"] = args.password
    if args.password_stdin:
        overrides["password"] = sys.stdin.readline().rstrip("\n")
    if args.api_token:
        parts = args.api_token.split("=", 1)
        if len(parts) == 2:
            user_token, secret = parts
            if "!" in user_token:
                user, token_id = user_token.split("!", 1)
                overrides["username"] = user
                overrides["api_token_id"] = token_id
                overrides["api_token_secret"] = secret
            else:
                overrides["username"] = user_token
                overrides["api_token_secret"] = secret
        else:
            log_error("Invalid --api-token format. Expected: user!tokenid=secret")
    if args.insecure:
        overrides["verify_tls"] = False
    elif "verify_tls" not in overrides:
        overrides["verify_tls"] = True

    return creds, overrides


def _build_client(overrides: dict[str, Any], args: argparse.Namespace) -> ProxmoxClient:
    """Build a ProxmoxClient from merged config overrides."""
    if not overrides["url"]:
        raise ConfigError("No Proxmox URL configured. Use --url or run 'proxmox auth login'.")

    auth_mgr = AuthManager()

    if overrides["api_token_id"] and overrides["api_token_secret"]:
        auth_mgr.set_api_token(
            overrides["username"] or "root@pam",
            overrides["api_token_id"],
            overrides["api_token_secret"],
        )
    elif overrides["password"] and not args.dry_run:
        auth_mgr.authenticate_password(
            overrides["url"],
            overrides["username"] or "root@pam",
            overrides["password"],
            verify=overrides["verify_tls"],
        )

    client = ProxmoxClient(
        base_url=overrides["url"],
        auth_manager=auth_mgr,
        timeout=args.timeout,
        verify_tls=overrides["verify_tls"],
        dry_run=args.dry_run,
        verbose=args.verbose,
    )

    # Store for lazy re-auth
    if overrides["password"]:
        client.set_credentials(overrides["username"] or "root@pam", overrides["password"])

    return client


def _print_command_help(args: argparse.Namespace) -> None:
    """When a subcommand has no explicit handler set, print the parent parser's help."""
    # Try to reconstruct the appropriate parser and show its help
    cmd_parts = ["proxmox", args.resource]
    if hasattr(args, "fw_resource"):
        cmd_parts.append("firewall")
        cmd_parts.append(args.fw_resource)
    elif hasattr(args, "action"):
        cmd_parts.append(args.action)
    log_error(
        f"Missing required argument. Run '{' '.join(cmd_parts)} --help' for usage."
    )


def main(argv: list[str] | None = None) -> None:
    """Main entry point."""
    parser = build_root_parser()
    args = parser.parse_args(argv)

    # --help or no subcommand: just show help
    if args.resource is None:
        parser.print_help()
        return

    try:
        # auth status, clear, and completion don't need a client
        if (args.resource == "auth" and args.action in ("status", "clear")) or args.resource == "completion":
            if hasattr(args, "func"):
                result = args.func(args, None)
                if result is not None:
                    if args.resource == "completion":
                        # Completion scripts are raw shell code, not JSON
                        print(result)
                    else:
                        output = format_output(result, args.output)
                        print(output)
            return

        _, overrides = _merge_config(args)
        client = _build_client(overrides, args)

        # Each subcommand sets args.func during registration
        if hasattr(args, "func"):
            result = args.func(args, client)
            if result is not None:
                output = format_output(result, args.output)
                print(output)
        else:
            # No handler was set — show relevant help
            _print_command_help(args)

    except ConfigError as exc:
        log_error(str(exc))
        sys.exit(1)
    except ProxmoxAPIError as exc:
        if args.output == "json":
            print(
                format_output(
                    {"error": exc.message, "status_code": exc.status_code}, "json"
                )
            )
        else:
            log_error(str(exc))
        sys.exit(exc.status_code if exc.status_code > 0 else 1)
    except ProxmoxError as exc:
        log_error(str(exc))
        sys.exit(1)


if __name__ == "__main__":
    main()
