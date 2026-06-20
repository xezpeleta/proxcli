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

    # --- storage upload ---
    st_upload = st_sub.add_parser("upload", help="Upload a file to storage")
    st_upload.add_argument("--node", required=True, help="Target node")
    st_upload.add_argument("--storage", required=True, help="Storage ID (e.g. 'local')")
    st_upload.add_argument("--file", required=True, help="Path to the local file")
    st_upload.add_argument(
        "--content-type",
        default="iso",
        choices=["iso", "vztmpl", "import"],
        help="Content type (default: iso)",
    )
    st_upload.set_defaults(func=_st_upload)

    # --- storage status ---
    st_status = st_sub.add_parser("status", help="Show storage usage status")
    st_status.add_argument("storage_name", help="Storage name")
    st_status.add_argument("--node", help="Node name (auto-detected if omitted)")
    st_status.set_defaults(func=_st_status)


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


def _st_upload(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    return client.upload(
        node=args.node,
        storage=args.storage,
        file_path=args.file,
        content_type=args.content_type,
    )


def _st_status(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    node = args.node or _resolve_storage_node(client, args.storage_name)
    if not node:
        return {
            "error": f"Could not determine node for storage '{args.storage_name}'. "
                     "Use --node <name> to specify the node."
        }
    return client.get(f"/nodes/{node}/storage/{args.storage_name}/status")
