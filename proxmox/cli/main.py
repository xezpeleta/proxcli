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
        choices=["json", "table", "yaml", "log"],
        default="json",
        help="Output format (default: json)",
    )
    parser.add_argument(
        "--columns",
        default=None,
        help="Columns to show in table output, comma-separated "
             "(e.g. --columns vmid,name,status). Works before or after the subcommand.",
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
        "--version", action="version", version=f"proxcli {version('proxcli')}"
    )

    subparsers = parser.add_subparsers(dest="resource", title="resources", required=False)

    # Import and register subcommands
    from proxmox.cli.acl import register_acl_parser
    from proxmox.cli.api import register_api_parser
    from proxmox.cli.auth import register_auth_parser
    from proxmox.cli.backup import register_backup_parser
    from proxmox.cli.ceph import register_ceph_parser
    from proxmox.cli.cluster import register_cluster_parser
    from proxmox.cli.completion import register_completion_parser
    from proxmox.cli.container import register_container_parser
    from proxmox.cli.network import register_network_parser
    from proxmox.cli.node import register_node_parser
    from proxmox.cli.pool import register_pool_parser
    from proxmox.cli.role import register_role_parser
    from proxmox.cli.storage import register_storage_parser
    from proxmox.cli.tasks import register_task_parser
    from proxmox.cli.update import register_update_parser
    from proxmox.cli.user import register_user_parser
    from proxmox.cli.vm import register_vm_parser

    register_acl_parser(subparsers)
    register_api_parser(subparsers)
    register_auth_parser(subparsers)
    register_backup_parser(subparsers)
    register_ceph_parser(subparsers)
    register_vm_parser(subparsers)
    register_node_parser(subparsers)
    register_network_parser(subparsers)
    register_pool_parser(subparsers)
    register_container_parser(subparsers)
    register_storage_parser(subparsers)
    register_cluster_parser(subparsers)
    register_completion_parser(subparsers)
    register_task_parser(subparsers)
    register_role_parser(subparsers)
    register_user_parser(subparsers)
    register_update_parser(subparsers)

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


GLOBAL_FLAGS = {
    "--url", "--username", "--password", "--password-stdin", "--api-token",
    "--output", "--dry-run", "--insecure", "--timeout", "--verbose", "--version", "--columns",
}

# Flags that take a value (the value follows the flag)
GLOBAL_FLAGS_WITH_VALUE = {"--url", "--username", "--password", "--api-token", "--output", "--timeout", "--columns"}

# Top-level resource keywords (the first one on the command line).
RESOURCES = {
    "acl", "api", "auth", "backup", "ceph", "vm", "node", "pool",
    "container", "storage", "cluster", "completion", "task", "user",
    "role", "network", "update",
}

# Global flags safe to relocate before the resource. `--timeout` is excluded:
# `task wait` and `vm agent exec` define their own --timeout with different
# units/meaning, so hoisting it would silently change behaviour.
HOISTABLE_FLAGS = GLOBAL_FLAGS - {"--timeout"}
HOISTABLE_VALUE_FLAGS = GLOBAL_FLAGS_WITH_VALUE - {"--timeout"}


def _hoist_global_flags(argv: list[str]) -> list[str]:
    """Relocate global flags that appear *after* the resource to before it.

    argparse only registers global flags on the root parser, so without this
    `proxmox vm list --dry-run` or `proxmox vm list --output yaml` fails with
    "unrecognized arguments". Hoisting them in front of the resource makes
    global flags work in either position — the form agents try first
    (`... <subcommand> --flag`) just works.

    Everything after a bare `--` is left untouched so positional flag-like
    tokens survive (e.g. `vm agent exec 100 -- ls -la /etc`).
    """
    res_pos = None
    for i, arg in enumerate(argv):
        if arg in RESOURCES:
            res_pos = i
            break
    if res_pos is None:
        return argv

    before = argv[:res_pos]
    rest = argv[res_pos:]

    hoisted: list[str] = []
    kept: list[str] = [rest[0]]  # the resource token itself stays put
    i = 1
    while i < len(rest):
        tok = rest[i]
        # `--` ends option parsing for this subcommand; keep it and everything
        # after verbatim so positional flag-like tokens are preserved.
        if tok == "--":
            kept.extend(rest[i:])
            break
        # `--flag=value` form of a global flag
        if tok.startswith("--") and "=" in tok:
            flag = tok.split("=", 1)[0]
            if flag in HOISTABLE_FLAGS:
                hoisted.append(tok)
                i += 1
                continue
        # bare `--flag` form
        if tok in HOISTABLE_FLAGS:
            hoisted.append(tok)
            if tok in HOISTABLE_VALUE_FLAGS and i + 1 < len(rest):
                hoisted.append(rest[i + 1])
                i += 2
            else:
                i += 1
            continue
        kept.append(tok)
        i += 1

    return before + hoisted + kept


def _resolve_columns(args: argparse.Namespace) -> list[str] | None:
    """Split the --columns string into a list (comma- or whitespace-separated)."""
    raw = getattr(args, "columns", None)
    if not raw:
        return None
    if isinstance(raw, list):  # defensive: legacy nargs='+' value
        return raw or None
    parts = [c.strip() for c in raw.replace(",", " ").split()]
    return [p for p in parts if p] or None


def _print_cheat_sheet() -> None:
    """Print a focused quick-start for the no-argument / first-run case.

    Agents frequently skip `--help` and guess subcommands. Printing the most
    common tasks on a zero-arg invocation teaches the syntax up front.
    """
    print(
        f"proxcli {version('proxcli')} — Proxmox VE CLI. "
        f"Binary: `proxmox` (alias: `proxcli`).\n"
        "\n"
        "Common tasks:\n"
        "  proxmox vm list --name unifi                 # find a VM by name (returns vmid + node)\n"
        "  proxmox vm show 100                          # show a VM (node auto-detected)\n"
        "  proxmox node list                            # list all nodes\n"
        "  proxmox vm snapshot create 100 pre-update --wait   # snapshot, block until done\n"
        "  proxmox task wait UPID:pve01:...             # block until an async task finishes\n"
        "  proxmox vm start 100 && proxmox vm stop 100\n"
        "\n"
        "Agent-friendly flags (work before OR after the subcommand):\n"
        "  --dry-run        print the API request without executing it\n"
        "  --output yaml    clean key:value output (easiest to parse; default is json)\n"
        "  --columns a,b,c  pick columns for --output table\n"
        "  --insecure       skip TLS certificate verification\n"
        "\n"
        "Run `proxmox --help` for the full reference, or `proxmox <resource> --help`."
    )


def _resolve_output(args: argparse.Namespace) -> str:
    """Resolve the effective output format.

    If the user explicitly passed --output on the command line, use that.
    Otherwise, use the subparser's output_format default hint if set.
    Falls back to 'json'.
    """
    # Check if --output was explicitly passed anywhere on the command line
    for i, arg in enumerate(sys.argv):
        if arg == "--output" and i + 1 < len(sys.argv):
            return sys.argv[i + 1]
        if arg.startswith("--output="):
            return arg.split("=", 1)[1]
    # Use the subparser hint
    hint = getattr(args, "output_format", None)
    if hint:
        return hint
    return args.output


def main(argv: list[str] | None = None) -> None:
    """Main entry point."""
    parser = build_root_parser()

    effective_argv = argv if argv is not None else sys.argv[1:]

    # Relocate global flags that appear after the resource so they parse in
    # either position (e.g. `proxmox vm list --dry-run` == `proxmox --dry-run vm list`).
    effective_argv = _hoist_global_flags(effective_argv)

    try:
        args = parser.parse_args(effective_argv)
    except SystemExit as e:
        sys.exit(e.code if isinstance(e.code, int) else 1)

    # No subcommand: print a focused cheat sheet (agents skip --help, so make
    # the zero-arg case teach the syntax). Use --help for the full reference.
    if args.resource is None:
        _print_cheat_sheet()
        return

    try:
        # These commands don't need a pre-built client:
        #   - completion / update           : self-contained
        #   - auth status (no --permissions): reads config file only
        #   - auth setup --via ssh          : bootstraps credentials itself
        auth_setup_ssh = (
            args.resource == "auth"
            and getattr(args, "action", None) == "setup"
            and getattr(args, "via", "ssh") == "ssh"
        )
        if (
            args.resource == "completion"
            or args.resource == "update"
            or auth_setup_ssh
            or (
                args.resource == "auth"
                and args.action == "status"
                and not getattr(args, "permissions", False)
            )
        ):
            if hasattr(args, "func"):
                result = args.func(args, None)
                if result is not None:
                    if args.resource == "completion":
                        # Completion scripts are raw shell code, not JSON
                        print(result)
                    else:
                        output = format_output(
                            result, _resolve_output(args),
                            columns=_resolve_columns(args),
                        )
                        print(output)
            return

        _, overrides = _merge_config(args)
        client = _build_client(overrides, args)

        # Each subcommand sets args.func during registration
        if hasattr(args, "func"):
            result = args.func(args, client)
            if result is not None:
                # Cloud-init dump returns raw YAML string — print directly
                if (
                    args.resource == "vm"
                    and getattr(args, "cloudinit_action", None) == "dump"
                    and isinstance(result, str)
                ):
                    print(result)
                else:
                    output = format_output(
                        result, _resolve_output(args), columns=_resolve_columns(args)
                    )
                    print(output)
        else:
            # No handler was set — show relevant help
            _print_command_help(args)

    except ConfigError as exc:
        log_error(str(exc))
        sys.exit(1)
    except ProxmoxAPIError as exc:
        if _resolve_output(args) == "json":
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
