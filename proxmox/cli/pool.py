"""`proxmox pool` subcommand — resource pool management."""

from __future__ import annotations

import argparse

from proxmox.client.client import ProxmoxClient


def register_pool_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the `proxmox pool` subcommand tree."""
    pool_parser = subparsers.add_parser("pool", help="Manage resource pools")
    pool_sub = pool_parser.add_subparsers(dest="action", title="actions", required=True)

    # --- pool list ---
    pool_list = pool_sub.add_parser("list", help="List all pools")
    pool_list.set_defaults(func=_pool_list)

    # --- pool show ---
    pool_show = pool_sub.add_parser("show", help="Show pool details and members")
    pool_show.add_argument("poolid", help="Pool ID")
    pool_show.set_defaults(func=_pool_show)

    # --- pool create ---
    pool_create = pool_sub.add_parser("create", help="Create a new pool")
    pool_create.add_argument("poolid", help="Pool ID")
    pool_create.add_argument("--comment", default=None, help="Pool description / comment")
    pool_create.set_defaults(func=_pool_create)

    # --- pool update ---
    pool_update = pool_sub.add_parser("update", help="Update a pool's comment")
    pool_update.add_argument("poolid", help="Pool ID")
    pool_update.add_argument("--comment", default=None, help="New comment (omit to clear)")
    pool_update.add_argument("--allow-delete", action="store_true", help="Allow deletion of pool comment")
    pool_update.set_defaults(func=_pool_update)

    # --- pool delete ---
    pool_delete = pool_sub.add_parser("delete", help="Delete a pool")
    pool_delete.add_argument("poolid", help="Pool ID")
    pool_delete.set_defaults(func=_pool_delete)


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------

def _pool_list(_args: argparse.Namespace, client: ProxmoxClient) -> dict | list:
    return client.get("/pools")


def _pool_show(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    return client.get(f"/pools/{args.poolid}")


def _pool_create(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    data: dict = {"poolid": args.poolid}
    if args.comment:
        data["comment"] = args.comment
    return client.post("/pools", data=data)


def _pool_update(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    data: dict = {}
    if args.comment is not None:
        data["comment"] = args.comment
    if args.allow_delete:
        data["delete"] = 1
    if not data:
        return {"error": "Nothing to update. Use --comment or --allow-delete."}
    return client.put(f"/pools/{args.poolid}", data=data)


def _pool_delete(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    return client.delete(f"/pools/{args.poolid}")
