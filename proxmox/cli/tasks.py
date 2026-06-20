"""`proxmox task` subcommand — task management."""

from __future__ import annotations

import argparse

from proxmox.client.client import ProxmoxClient


def register_task_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the `proxmox task` subcommand tree."""
    task_parser = subparsers.add_parser("task", help="Manage Proxmox tasks/logs")
    task_sub = task_parser.add_subparsers(dest="action", title="actions", required=True)

    # --- task list ---
    task_list = task_sub.add_parser("list", help="List recent tasks")
    task_list.add_argument("--node", help="Filter by node name")
    task_list.set_defaults(func=_task_list)

    # --- task show ---
    task_show = task_sub.add_parser("show", help="Show task details")
    task_show.add_argument("upid", help="Task UPID")
    task_show.set_defaults(func=_task_show)


def _extract_node_from_upid(upid: str) -> str | None:
    """Parse node name from a Proxmox UPID string: UPID:{node}:..."""
    parts = upid.split(":")
    if len(parts) >= 2:
        return parts[1]
    return None


def _task_list(args: argparse.Namespace, client: ProxmoxClient) -> dict | list:
    if args.node:
        return client.get(f"/nodes/{args.node}/tasks")
    # Iterate all nodes
    nodes = client.get("/nodes")
    if isinstance(nodes, dict):
        nodes = nodes.get("data", [])
    tasks: list[dict] = []
    for n in (nodes if isinstance(nodes, list) else []):
        node_name = n.get("node") if isinstance(n, dict) else n
        try:
            node_tasks = client.get(f"/nodes/{node_name}/tasks")
            if isinstance(node_tasks, list):
                for t in node_tasks:
                    if isinstance(t, dict):
                        t["_node"] = node_name
                    tasks.append(t)
            elif isinstance(node_tasks, dict):
                for t in node_tasks.get("data", []):
                    if isinstance(t, dict):
                        t["_node"] = node_name
                    tasks.append(t)
        except Exception:
            pass
    return tasks


def _task_show(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    node = _extract_node_from_upid(args.upid)
    if not node:
        return {"error": f"Could not extract node from UPID: {args.upid}"}
    return client.get(f"/nodes/{node}/tasks/{args.upid}/status")
