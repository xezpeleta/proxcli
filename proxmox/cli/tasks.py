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

    # --- task log ---
    task_log = task_sub.add_parser("log", help="Show task log output")
    task_log.add_argument("upid", help="Task UPID")
    task_log.add_argument(
        "--follow", "-f",
        action="store_true",
        help="Follow log output until task completes (like tail -f)",
    )
    task_log.set_defaults(func=_task_log)

    # --- task wait ---
    task_wait = task_sub.add_parser("wait", help="Block until a task completes")
    task_wait.add_argument("upid", help="Task UPID")
    task_wait.add_argument(
        "--timeout", type=int, default=60000,
        help="Max wait in milliseconds (default: 60000 = 60s)"
    )
    task_wait.add_argument(
        "--poll", type=int, default=500,
        help="Poll interval in milliseconds (default: 500)"
    )
    task_wait.set_defaults(func=_task_wait)


def _extract_node_from_upid(upid: str) -> str | None:
    """Parse node name from a Proxmox UPID string: UPID:{node}:..."""
    return ProxmoxClient._extract_node_from_upid(upid)


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


def _task_log(args: argparse.Namespace, client: ProxmoxClient) -> None:
    """Stream task log (returns None so main.py skips JSON formatting)."""
    client.stream_task_log(args.upid, follow=args.follow)


def _task_wait(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    """Block until a task completes.

    Polls ``GET /nodes/{node}/tasks/{upid}/status`` until the task
    reaches a terminal state (``ok`` or ``error``) or timeout expires.
    """
    import time

    node = _extract_node_from_upid(args.upid)
    if not node:
        return {"error": f"Could not extract node from UPID: {args.upid}"}

    started = time.monotonic()
    timeout_s = args.timeout / 1000.0
    poll_s = args.poll / 1000.0

    while True:
        status = client.get(f"/nodes/{node}/tasks/{args.upid}/status")
        if not isinstance(status, dict):
            return {"error": "Failed to read task status", "detail": status}

        if status.get("status") == "stopped":
            exitstatus = status.get("exitstatus", "")
            status["_node"] = node
            status["elapsed_ms"] = int((time.monotonic() - started) * 1000)
            if exitstatus == "OK":
                return {"data": status, "result": "ok"}
            return {"data": status, "result": "error", "exitstatus": exitstatus}

        elapsed = time.monotonic() - started
        if elapsed >= timeout_s:
            return {
                "error": f"Task did not complete within {args.timeout}ms",
                "current_status": status.get("status"),
            }

        time.sleep(poll_s)
