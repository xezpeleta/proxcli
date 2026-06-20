"""`proxmox node` subcommand — node management."""

from __future__ import annotations

import argparse

from proxmox.cli.firewall_helpers import add_firewall_rule_args, build_rule_data
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

    # --- firewall ---
    fw_parser = node_sub.add_parser("firewall", help="Manage node firewall")
    fw_sub = fw_parser.add_subparsers(dest="fw_action", title="firewall actions", required=True)

    fw_opts = fw_sub.add_parser("options", help="Show node firewall options")
    fw_opts.add_argument("node_name", help="Node name")
    fw_opts.set_defaults(func=_node_fw_options)

    fw_enable = fw_sub.add_parser("enable", help="Enable node firewall")
    fw_enable.add_argument("node_name", help="Node name")
    fw_enable.set_defaults(func=_node_fw_enable)

    fw_disable = fw_sub.add_parser("disable", help="Disable node firewall")
    fw_disable.add_argument("node_name", help="Node name")
    fw_disable.set_defaults(func=_node_fw_disable)

    fw_policy = fw_sub.add_parser("policy", help="Set default input/output policy")
    fw_policy.add_argument("node_name", help="Node name")
    fw_policy.add_argument("--in-policy", choices=["ACCEPT", "DENY", "REJECT"], default=None,
                           help="Default input policy")
    fw_policy.add_argument("--out-policy", choices=["ACCEPT", "DENY", "REJECT"], default=None,
                           help="Default output policy")
    fw_policy.set_defaults(func=_node_fw_policy)

    fw_rules = fw_sub.add_parser("rules", help="List node firewall rules")
    fw_rules.add_argument("node_name", help="Node name")
    fw_rules.set_defaults(func=_node_fw_rules)

    fw_rule_add = fw_sub.add_parser("add-rule", help="Add a node firewall rule")
    fw_rule_add.add_argument("node_name", help="Node name")
    add_firewall_rule_args(fw_rule_add)
    fw_rule_add.set_defaults(func=_node_fw_rule_add)

    fw_rule_show = fw_sub.add_parser("show-rule", help="Show a node firewall rule")
    fw_rule_show.add_argument("node_name", help="Node name")
    fw_rule_show.add_argument("pos", type=int, help="Rule position")
    fw_rule_show.set_defaults(func=_node_fw_rule_show)

    fw_rule_upd = fw_sub.add_parser("update-rule", help="Update a node firewall rule")
    fw_rule_upd.add_argument("node_name", help="Node name")
    fw_rule_upd.add_argument("pos", type=int, help="Rule position")
    add_firewall_rule_args(fw_rule_upd)
    for action in fw_rule_upd._actions:
        if action.dest == "action":
            action.required = False
            action.default = None
    fw_rule_upd.set_defaults(func=_node_fw_rule_upd)

    fw_rule_del = fw_sub.add_parser("delete-rule", help="Delete a node firewall rule")
    fw_rule_del.add_argument("node_name", help="Node name")
    fw_rule_del.add_argument("pos", type=int, help="Rule position")
    fw_rule_del.set_defaults(func=_node_fw_rule_del)

    fw_refs = fw_sub.add_parser("refs", help="List firewall references for node")
    fw_refs.add_argument("node_name", help="Node name")
    fw_refs.add_argument("--type", default=None, choices=["alias", "ipset", "group"],
                         help="Filter by reference type")
    fw_refs.set_defaults(func=_node_fw_refs)


# ---------------------------------------------------------------------------
# Node handlers
# ---------------------------------------------------------------------------

def _node_list(_args: argparse.Namespace, client: ProxmoxClient) -> dict | list:
    return client.get("/nodes")


def _node_show(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    return client.get(f"/nodes/{args.node_name}/status")


def _node_status(args: argparse.Namespace, client: ProxmoxClient) -> dict | list:
    if args.node_name:
        return client.get(f"/nodes/{args.node_name}/status")
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


# ---------------------------------------------------------------------------
# Node firewall handlers
# ---------------------------------------------------------------------------

def _node_fw_options(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    return client.get(f"/nodes/{args.node_name}/firewall/options")


def _node_fw_enable(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    return client.put(f"/nodes/{args.node_name}/firewall/options", data={"enable": 1})


def _node_fw_disable(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    return client.put(f"/nodes/{args.node_name}/firewall/options", data={"enable": 0})


def _node_fw_policy(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    data: dict = {}
    if args.in_policy:
        data["policy_in"] = args.in_policy
    if args.out_policy:
        data["policy_out"] = args.out_policy
    if not data:
        return {"error": "No policy specified. Use --in-policy or --out-policy"}
    return client.put(f"/nodes/{args.node_name}/firewall/options", data=data)


def _node_fw_rules(args: argparse.Namespace, client: ProxmoxClient) -> dict | list:
    return client.get(f"/nodes/{args.node_name}/firewall/rules")


def _node_fw_rule_add(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    return client.post(f"/nodes/{args.node_name}/firewall/rules", data=build_rule_data(args))


def _node_fw_rule_show(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    return client.get(f"/nodes/{args.node_name}/firewall/rules/{args.pos}")


def _node_fw_rule_upd(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    data = {k: v for k, v in build_rule_data(args).items() if v is not None and v != 0}
    return client.put(f"/nodes/{args.node_name}/firewall/rules/{args.pos}", data=data)


def _node_fw_rule_del(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    return client.delete(f"/nodes/{args.node_name}/firewall/rules/{args.pos}")


def _node_fw_refs(args: argparse.Namespace, client: ProxmoxClient) -> dict | list:
    params = {"type": args.type} if args.type else None
    return client.get(f"/nodes/{args.node_name}/firewall/refs", params=params)
