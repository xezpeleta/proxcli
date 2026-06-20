"""CLI subcommand for role management (`proxmox role`)."""

from __future__ import annotations

import argparse

from ..client.client import ProxmoxClient

# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------

def _role_list(args: argparse.Namespace, client: ProxmoxClient) -> list | dict:
    result = client.get("/access/roles")
    if isinstance(result, list):
        return result
    if isinstance(result, dict) and "data" in result:
        return result["data"]
    return result


def _role_show(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    return client.get(f"/access/roles/{args.roleid}")


def _role_create(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    data: dict = {"roleid": args.roleid}
    if args.privs:
        data["privs"] = args.privs
    return client.post("/access/roles", data=data)


def _role_update(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    data: dict = {}
    if args.privs:
        data["privs"] = args.privs
    if not data:
        return {"error": "No fields to update"}
    return client.put(f"/access/roles/{args.roleid}", data=data)


def _role_delete(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    return client.delete(f"/access/roles/{args.roleid}")


# ---------------------------------------------------------------------------
# Parser registration
# ---------------------------------------------------------------------------

def register_role_parser(subparsers: argparse._SubParsersAction) -> None:
    role_parser = subparsers.add_parser("role", help="Manage roles")
    role_sub = role_parser.add_subparsers(dest="action", title="actions", required=True)

    # role list
    role_list = role_sub.add_parser("list", help="List roles")
    role_list.set_defaults(func=_role_list)

    # role show
    role_show = role_sub.add_parser("show", help="Show role details")
    role_show.add_argument("roleid", help="Role ID (e.g. PVEAdmin)")
    role_show.set_defaults(func=_role_show)

    # role create
    role_create = role_sub.add_parser("create", help="Create role")
    role_create.add_argument("roleid", help="Role ID")
    role_create.add_argument("--privs", help="Comma-separated privilege list")
    role_create.set_defaults(func=_role_create)

    # role update
    role_update = role_sub.add_parser("update", help="Update role privileges")
    role_update.add_argument("roleid", help="Role ID")
    role_update.add_argument("--privs", help="Comma-separated privilege list")
    role_update.set_defaults(func=_role_update)

    # role delete
    role_delete = role_sub.add_parser("delete", help="Delete role")
    role_delete.add_argument("roleid", help="Role ID")
    role_delete.set_defaults(func=_role_delete)
