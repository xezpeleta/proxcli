"""`proxmox network` subcommand — network interface management."""

from __future__ import annotations

import argparse

from proxmox.client.client import ProxmoxClient


def register_network_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the `proxmox network` subcommand tree."""
    net_parser = subparsers.add_parser(
        "network",
        help="Manage network interfaces",
    )
    net_sub = net_parser.add_subparsers(dest="action", title="actions", required=True)

    # --- network list ---
    net_list = net_sub.add_parser("list", help="List network interfaces on a node")
    net_list.add_argument("--node", default="localhost", help="Node name (default: localhost)")
    net_list.add_argument(
        "--type",
        choices=["bridge", "bond", "eth", "alias", "vlan", "fabric",
                 "OVSBridge", "OVSBond", "OVSPort", "OVSIntPort", "vnet",
                 "any_bridge", "any_local_bridge", "include_sdn"],
        help="Filter by interface type",
    )
    net_list.set_defaults(func=_network_list)

    # --- network show ---
    net_show = net_sub.add_parser("show", help="Show a network interface configuration")
    net_show.add_argument("iface", help="Interface name (e.g., vmbr0, bond0)")
    net_show.add_argument("--node", default="localhost", help="Node name (default: localhost)")
    net_show.set_defaults(func=_network_show)


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------

def _network_list(args: argparse.Namespace, client: ProxmoxClient) -> list | dict:
    params: dict = {}
    if args.type:
        params["type"] = args.type
    return client.get(f"/nodes/{args.node}/network", params=params if params else None)


def _network_show(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    return client.get(f"/nodes/{args.node}/network/{args.iface}")
