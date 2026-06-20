"""CLI subcommand for backup management (`proxmox backup`)."""

from __future__ import annotations

import argparse
import urllib.parse

from ..client.client import ProxmoxClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_all_nodes(client: ProxmoxClient) -> list[str]:
    """Get all node names from the cluster."""
    result = client.get("/nodes")
    nodes = (
        result
        if isinstance(result, list)
        else result.get("data", []) if isinstance(result, dict) else []
    )
    return [n.get("node", "") for n in nodes if isinstance(n, dict)]


def _list_backup_files(
    client: ProxmoxClient,
    node: str,
    storage: str | None,
    vmid: int | None,
) -> list | dict:
    """List backup files from storage content endpoints."""
    if node and storage:
        params: dict = {"content": "backup"}
        if vmid:
            params["vmid"] = vmid
        return client.get(f"/nodes/{node}/storage/{storage}/content", params=params)

    # If no storage specified, search all backup storages on the node
    result = client.get(f"/nodes/{node}/storage")
    storages = (
        result
        if isinstance(result, list)
        else (result.get("data", []) if isinstance(result, dict) else [])
    )

    all_backups: list = []
    for s in storages:
        if isinstance(s, dict) and "backup" in str(s.get("content", "")):
            sname = s.get("storage", "")
            params = {"content": "backup"}
            if vmid:
                params["vmid"] = vmid
            backup_result = client.get(
                f"/nodes/{node}/storage/{sname}/content", params=params
            )
            backups = (
                backup_result
                if isinstance(backup_result, list)
                else (
                    backup_result.get("data", [])
                    if isinstance(backup_result, dict)
                    else []
                )
            )
            for b in backups:
                if isinstance(b, dict):
                    b["_storage"] = sname
            all_backups.extend(backups)
    return all_backups


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------

def _backup_list(args: argparse.Namespace, client: ProxmoxClient) -> list | dict:
    return _list_backup_files(client, args.node, args.storage, args.vmid)


def _backup_show(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    # volid format: <storage>:<path>
    if ":" in args.volid:
        # Parse storage from volid
        storage, path = args.volid.split(":", 1)
        result = client.get(
            f"/nodes/{args.node}/storage/{storage}/content?content=backup&vmid={args.vmid}"
        )
        backups = (
            result
            if isinstance(result, list)
            else result.get("data", []) if isinstance(result, dict) else []
        )
        for b in backups:
            if isinstance(b, dict) and b.get("volid") == args.volid:
                b["_node"] = args.node
                return b
        return {"error": f"Backup {args.volid} not found on node {args.node}"}
    # No colon — search all backup storages
    nodes = [args.node] if args.node else _get_all_nodes(client)
    for n in nodes:
        result = client.get(f"/nodes/{n}/storage")
        storages = (
            result
            if isinstance(result, list)
            else result.get("data", []) if isinstance(result, dict) else []
        )
        for s in storages:
            sname = s.get("storage", "")
            if "backup" not in str(s.get("content", "")):
                continue
            content = client.get(
                f"/nodes/{n}/storage/{sname}/content?content=backup"
            )
            backups = (
                content
                if isinstance(content, list)
                else content.get("data", []) if isinstance(content, dict) else []
            )
            for b in backups:
                if isinstance(b, dict) and b.get("volid") == args.volid:
                    b["_node"] = n
                    return b
    return {"error": f"Backup {args.volid} not found"}


def _backup_create(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    data: dict = {}

    # What to back up
    if args.all:
        data["all"] = 1
    elif args.vmid:
        data["vmid"] = args.vmid
    else:
        return {"error": "Must specify --vmid or --all"}

    if args.storage:
        data["storage"] = args.storage
    if args.mode:
        data["mode"] = args.mode
    if args.compress is not None:
        data["compress"] = args.compress
    if args.remove is not None:
        data["remove"] = args.remove
    if args.bwlimit is not None:
        data["bwlimit"] = args.bwlimit
    if args.ionice is not None:
        data["ionice"] = args.ionice
    if args.lockwait is not None:
        data["lockwait"] = args.lockwait
    if args.stop:
        data["stop"] = 1
    if args.stopwait is not None:
        data["stopwait"] = args.stopwait
    if args.pigz is not None:
        data["pigz"] = args.pigz
    if args.zstd is not None:
        data["zstd"] = args.zstd
    if args.quiet:
        data["quiet"] = 1
    if args.mailnotification:
        data["mailnotification"] = args.mailnotification
    if args.prune_backups:
        data["prune-backups"] = args.prune_backups
    if args.nodelete:
        data["remove"] = 0

    return client.post(f"/nodes/{args.node}/vzdump", data=data)


def _backup_delete(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    # Delete a backup file from storage
    # volid: <storage>:<path>
    if ":" not in args.volid:
        return {"error": f"Invalid volid format: {args.volid}. Expected <storage>:<path>"}
    storage, path = args.volid.split(":", 1)
    # The volid in the delete path needs URL encoding, but typically the
    # path portion already includes the storage prefix
    encoded_volid = urllib.parse.quote(args.volid, safe="")
    return client.delete(
        f"/nodes/{args.node}/storage/{storage}/content/{encoded_volid}"
    )


def _backup_tasks(args: argparse.Namespace, client: ProxmoxClient) -> list | dict:
    params: dict = {"typefilter": "vzdump"}
    if args.limit:
        params["limit"] = args.limit
    if args.vmid:
        params["vmid"] = args.vmid
    result = client.get(f"/nodes/{args.node}/tasks", params=params)
    if isinstance(result, list):
        return result
    if isinstance(result, dict) and "data" in result:
        return result["data"]
    return result


def _backup_defaults(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    params: dict = {}
    if args.storage:
        params["storage"] = args.storage
    return client.get(f"/nodes/{args.node}/vzdump/defaults", params=params)


# ---------------------------------------------------------------------------
# Parser registration
# ---------------------------------------------------------------------------

def register_backup_parser(subparsers: argparse._SubParsersAction) -> None:
    backup_parser = subparsers.add_parser("backup", help="Manage backups (vzdump)")
    backup_sub = backup_parser.add_subparsers(
        dest="action", title="actions", required=True
    )

    # backup list
    backup_list = backup_sub.add_parser("list", help="List backup files")
    backup_list.add_argument(
        "--node", default="localhost", help="Node name (default: localhost)"
    )
    backup_list.add_argument("--storage", help="Filter by storage name")
    backup_list.add_argument("--vmid", type=int, help="Filter by VM/CT ID")
    backup_list.set_defaults(func=_backup_list)

    # backup show
    backup_show = backup_sub.add_parser("show", help="Show backup details")
    backup_show.add_argument("volid", help="Backup volume ID")
    backup_show.add_argument(
        "--node", default="localhost", help="Node name (default: localhost)"
    )
    backup_show.add_argument("--vmid", type=int, help="VM/CT ID (for faster lookup)")
    backup_show.set_defaults(func=_backup_show)

    # backup create
    backup_create = backup_sub.add_parser("create", help="Create a backup job")
    backup_create.add_argument(
        "--node",
        default="localhost",
        help="Node to back up from (default: localhost)",
    )
    backup_create.add_argument("--vmid", help="VM/CT ID to back up")
    backup_create.add_argument(
        "--all", action="store_true", help="Back up all guests on this node"
    )
    backup_create.add_argument(
        "--storage", help="Storage for the backup (e.g. pbs-bianditz)"
    )
    backup_create.add_argument(
        "--mode",
        choices=["snapshot", "suspend", "stop"],
        default="snapshot",
        help="Backup mode (default: snapshot)",
    )
    backup_create.add_argument(
        "--compress",
        choices=["0", "1", "zstd"],
        default=None,
        help="Compression: 0=none, 1=lzo, zstd",
    )
    backup_create.add_argument(
        "--remove",
        type=int,
        choices=[0, 1],
        default=None,
        help="Remove old backups (default: 1)",
    )
    backup_create.add_argument(
        "--nodelete",
        action="store_true",
        help="Do not remove old backups (overrides --remove)",
    )
    backup_create.add_argument(
        "--bwlimit", type=int, help="Bandwidth limit in KiB/s"
    )
    backup_create.add_argument(
        "--ionice", type=int, choices=range(0, 9), help="I/O priority (0-8)"
    )
    backup_create.add_argument(
        "--lockwait", type=int, help="Max minutes to wait for guest lock"
    )
    backup_create.add_argument(
        "--stop",
        action="store_true",
        help="Stop running guests for backup (not needed with snapshot mode)",
    )
    backup_create.add_argument(
        "--stopwait", type=int, help="Max minutes to wait for guest to stop"
    )
    backup_create.add_argument(
        "--pigz",
        type=int,
        choices=[0, 1],
        default=None,
        help="Use pigz for compression (0/1)",
    )
    backup_create.add_argument(
        "--zstd",
        type=int,
        choices=[0, 1],
        default=None,
        help="Use zstd for compression (0/1)",
    )
    backup_create.add_argument(
        "--quiet", action="store_true", help="Suppress progress output"
    )
    backup_create.add_argument(
        "--mailnotification",
        choices=["always", "failure", "never"],
        help="Email notification policy",
    )
    backup_create.add_argument(
        "--prune-backups",
        help="Prune settings (e.g. keep-daily=7,keep-weekly=4)",
    )
    backup_create.set_defaults(func=_backup_create)

    # backup delete
    backup_delete = backup_sub.add_parser("delete", help="Delete a backup file")
    backup_delete.add_argument("volid", help="Backup volume ID to delete")
    backup_delete.add_argument(
        "--node", default="localhost", help="Node name (default: localhost)"
    )
    backup_delete.set_defaults(func=_backup_delete)

    # backup tasks
    backup_tasks = backup_sub.add_parser(
        "tasks", help="List backup task history"
    )
    backup_tasks.add_argument(
        "--node", default="localhost", help="Node name (default: localhost)"
    )
    backup_tasks.add_argument(
        "--limit", type=int, default=50, help="Max tasks to return (default: 50)"
    )
    backup_tasks.add_argument("--vmid", type=int, help="Filter by VM/CT ID")
    backup_tasks.set_defaults(func=_backup_tasks)

    # backup defaults
    backup_defaults = backup_sub.add_parser(
        "defaults", help="Show backup defaults for a storage"
    )
    backup_defaults.add_argument(
        "--node", default="localhost", help="Node name (default: localhost)"
    )
    backup_defaults.add_argument(
        "--storage", help="Storage name (e.g. pbs-bianditz)"
    )
    backup_defaults.set_defaults(func=_backup_defaults)
