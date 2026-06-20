"""`proxmox node` subcommand — node management."""

from __future__ import annotations

import argparse

from proxmox.client.client import ProxmoxClient


def register_node_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the `proxmox node` subcommand tree."""
    node_parser = subparsers.add_parser("node", help="Manage Proxmox nodes")
    node_sub = node_parser.add_subparsers(dest="action", title="actions", required=True)

    # --- node list ---
    node_list = node_sub.add_parser("list", help="List all nodes")
    node_list.set_defaults(func=_node_list)

    # --- node show ---
    node_show = node_sub.add_parser("show", help="Show node details")
    node_show.add_argument("node_name", help="Node name")
    node_show.set_defaults(func=_node_show)

    # --- node status ---
    node_status = node_sub.add_parser("status", help="Show node status")
    node_status.add_argument("node_name", nargs="?", help="Node name (omit for all nodes)")
    node_status.set_defaults(func=_node_status)


def _node_list(args: argparse.Namespace, client: ProxmoxClient) -> dict | list:
    return client.get("/nodes")


def _node_show(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    return client.get(f"/nodes/{args.node_name}/status")


def _node_status(args: argparse.Namespace, client: ProxmoxClient) -> dict | list:
    if args.node_name:
        return client.get(f"/nodes/{args.node_name}/status")
    # Return all nodes' statuses
    nodes = client.get("/nodes")
    if isinstance(nodes, list):
        result = []
        for n in nodes:
            node_name = n.get("node") if isinstance(n, dict) else n
            try:
                status = client.get(f"/nodes/{node_name}/status")
                if isinstance(status, dict):
                    status["node"] = node_name
                result.append(status)
            except Exception:
                result.append({"node": node_name, "status": "error"})
        return result
    return nodes
