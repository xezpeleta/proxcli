"""`proxmox api` subcommand — raw authenticated API calls."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from proxmox.client.client import ProxmoxClient


def register_api_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the `proxmox api` subcommand."""
    api_parser = subparsers.add_parser(
        "api",
        help="Make a raw authenticated API call (for endpoints not yet covered by subcommands)",
    )
    api_parser.add_argument(
        "method",
        choices=["GET", "POST", "PUT", "DELETE"],
        help="HTTP method",
    )
    api_parser.add_argument(
        "path",
        help="API path (e.g. /nodes/pve01/qemu/100/config). The /api2/json prefix is added automatically.",
    )
    api_parser.add_argument(
        "--data", "-d", default=None,
        help="Request body as JSON string (for POST/PUT)",
    )
    api_parser.add_argument(
        "--data-file", "-f", default=None, dest="data_file",
        help="Read request body from a JSON file (for POST/PUT)",
    )
    api_parser.set_defaults(func=_api_call)


def _api_call(args: argparse.Namespace, client: ProxmoxClient) -> dict[str, Any] | list[Any]:
    """Execute a raw API call.

    Wraps ``ProxmoxClient.request(method, path, ...)``.
    """
    # Normalise path: strip leading slash, strip /api2/json prefix if present
    path = args.path.lstrip("/")
    if path.startswith("api2/json/"):
        path = path[len("api2/json/"):]

    # Parse body
    body: dict[str, Any] | None = None
    if args.data_file:
        try:
            with open(args.data_file) as f:
                body = json.load(f)
        except (OSError, FileNotFoundError) as e:
            return {"error": f"Cannot read data file: {e}"}
        except json.JSONDecodeError as e:
            return {"error": f"Invalid JSON in data file: {e}"}
    elif args.data:
        try:
            body = json.loads(args.data)
        except json.JSONDecodeError as e:
            return {"error": f"Invalid JSON in --data: {e}. Use valid JSON, e.g. '{{\"key\": \"value\"}}'"}

    # Read additional body from stdin if piped (and no --data/--data-file)
    if body is None and not sys.stdin.isatty():
        stdin_data = sys.stdin.read().strip()
        if stdin_data:
            try:
                body = json.loads(stdin_data)
            except json.JSONDecodeError as e:
                return {"error": f"Invalid JSON from stdin: {e}"}

    result = client.request(args.method, f"/{path}", data=body)
    return result if isinstance(result, (dict, list)) else {"data": result}
