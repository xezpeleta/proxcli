"""`proxmox storage` subcommand — storage management."""

from __future__ import annotations

import argparse

from proxmox.client.client import ProxmoxClient


def register_storage_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the `proxmox storage` subcommand tree."""
    st_parser = subparsers.add_parser("storage", help="Manage Proxmox storage")
    st_sub = st_parser.add_subparsers(dest="action", title="actions", required=True)

    # --- storage list ---
    st_list = st_sub.add_parser("list", help="List all storages")
    st_list.add_argument("--node", help="Filter by node name")
    st_list.set_defaults(func=_st_list)

    # --- storage show ---
    st_show = st_sub.add_parser("show", help="Show storage details")
    st_show.add_argument("storage_name", help="Storage name")
    st_show.set_defaults(func=_st_show)

    # --- storage content ---
    st_content = st_sub.add_parser("content", help="List storage contents")
    st_content.add_argument("storage_name", help="Storage name")
    st_content.add_argument("--node", help="Node name (auto-detected if omitted)")
    st_content.set_defaults(func=_st_content)


def _st_list(args: argparse.Namespace, client: ProxmoxClient) -> dict | list:
    if args.node:
        return client.get(f"/nodes/{args.node}/storage")
    return client.get("/storage")


def _st_show(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    return client.get(f"/storage/{args.storage_name}/status")


def _resolve_storage_node(client: ProxmoxClient, storage: str) -> str | None:
    """Find which node a storage belongs to."""
    try:
        storages = client.get("/storage")
        if isinstance(storages, list):
            for s in storages:
                if isinstance(s, dict) and s.get("storage") == storage:
                    return s.get("node")
        elif isinstance(storages, dict):
            for s in storages.get("data", []):
                if isinstance(s, dict) and s.get("storage") == storage:
                    return s.get("node")
    except Exception:
        pass
    return None


def _st_content(args: argparse.Namespace, client: ProxmoxClient) -> dict | list:
    node = args.node or _resolve_storage_node(client, args.storage_name)
    if not node:
        return {"error": f"Could not determine node for storage '{args.storage_name}'"}
    return client.get(f"/nodes/{node}/storage/{args.storage_name}/content")
