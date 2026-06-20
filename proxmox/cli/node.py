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
    fw = node_sub.add_parser("firewall", help="Manage node firewall")
    fw_sub = fw.add_subparsers(dest="fw_resource", title="resources", required=True)

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

    # firewall rules
    rules = fw_sub.add_parser("rules", help="Manage node firewall rules")
    rules.set_defaults(func=_node_fw_rules)
    rules_sub = rules.add_subparsers(dest="fw_action", title="rule actions", required=False)

    rules_list = rules_sub.add_parser("list", help="List rules")
    rules_list.add_argument("node_name", help="Node name")
    rules_list.set_defaults(func=_node_fw_rules)

    rules_add = rules_sub.add_parser("add", help="Add a rule")
    rules_add.add_argument("node_name", help="Node name")
    add_firewall_rule_args(rules_add)
    rules_add.set_defaults(func=_node_fw_rule_add)

    rules_show = rules_sub.add_parser("show", help="Show a rule by position")
    rules_show.add_argument("node_name", help="Node name")
    rules_show.add_argument("pos", type=int, help="Rule position")
    rules_show.set_defaults(func=_node_fw_rule_show)

    rules_upd = rules_sub.add_parser("update", help="Update a rule by position")
    rules_upd.add_argument("node_name", help="Node name")
    rules_upd.add_argument("pos", type=int, help="Rule position")
    add_firewall_rule_args(rules_upd)
    for action in rules_upd._actions:
        if action.dest == "action":
            action.required = False
            action.default = None
    rules_upd.set_defaults(func=_node_fw_rule_upd)

    rules_del = rules_sub.add_parser("delete", help="Delete a rule by position")
    rules_del.add_argument("node_name", help="Node name")
    rules_del.add_argument("pos", type=int, help="Rule position")
    rules_del.set_defaults(func=_node_fw_rule_del)

    # firewall refs
    fw_refs = fw_sub.add_parser("refs", help="List firewall references for node")
    fw_refs.add_argument("node_name", help="Node name")
    fw_refs.add_argument("--type", default=None, choices=["alias", "ipset", "group"],
                         help="Filter by reference type")
    fw_refs.set_defaults(func=_node_fw_refs)

    # --- node subscription ---
    subscr = node_sub.add_parser("subscription", help="Show node subscription status")
    subscr.add_argument("node_name", help="Node name")
    subscr.set_defaults(func=_node_subscription)

    # --- node dns ---
    dns = node_sub.add_parser("dns", help="Show node DNS configuration")
    dns.add_argument("node_name", help="Node name")
    dns.set_defaults(func=_node_dns)

    # --- node time ---
    time = node_sub.add_parser("time", help="Show node time and timezone")
    time.add_argument("node_name", help="Node name")
    time.set_defaults(func=_node_time)

    # --- node services ---
    svc = node_sub.add_parser("services", help="List node systemd services")
    svc.add_argument("node_name", help="Node name")
    svc.set_defaults(func=_node_services)

    # --- node pci ---
    pci = node_sub.add_parser("pci", help="List node PCI devices")
    pci.add_argument("node_name", help="Node name")
    pci.set_defaults(func=_node_pci)

    # --- node netstat ---
    netstat = node_sub.add_parser("netstat", help="Show node network statistics")
    netstat.add_argument("node_name", help="Node name")
    netstat.set_defaults(func=_node_netstat)

    # --- node config ---
    cfg = node_sub.add_parser("config", help="Show node configuration")
    cfg.add_argument("node_name", help="Node name")
    cfg.set_defaults(func=_node_config)


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


# ---------------------------------------------------------------------------
# Node system handlers
# ---------------------------------------------------------------------------

def _node_subscription(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    return client.get(f"/nodes/{args.node_name}/subscription")


def _node_dns(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    return client.get(f"/nodes/{args.node_name}/dns")


def _node_time(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    return client.get(f"/nodes/{args.node_name}/time")


def _node_services(args: argparse.Namespace, client: ProxmoxClient) -> list:
    return client.get(f"/nodes/{args.node_name}/services")


def _node_pci(args: argparse.Namespace, client: ProxmoxClient) -> list:
    data = client.get(f"/nodes/{args.node_name}/hardware/pci")
    # Simplify for display
    return [
        {
            "id": d.get("id", ""),
            "vendor": d.get("vendor_name", ""),
            "device": d.get("device_name", ""),
            "class": d.get("class", ""),
            "iommugroup": d.get("iommugroup", -1) if d.get("iommugroup", -1) >= 0 else "",
        }
        for d in data
    ]


def _node_netstat(args: argparse.Namespace, client: ProxmoxClient) -> list:
    return client.get(f"/nodes/{args.node_name}/netstat")


def _node_config(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    return client.get(f"/nodes/{args.node_name}/config")
