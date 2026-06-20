"""`proxmox cluster` subcommand — cluster management."""

from __future__ import annotations

import argparse

from proxmox.cli.firewall_helpers import add_firewall_rule_args, build_rule_data
from proxmox.client.client import ProxmoxClient


def register_cluster_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the `proxmox cluster` subcommand tree."""
    cl_parser = subparsers.add_parser("cluster", help="Manage Proxmox cluster")
    cl_sub = cl_parser.add_subparsers(dest="action", title="actions", required=True)

    # --- cluster status ---
    cl_status = cl_sub.add_parser("status", help="Show cluster status")
    cl_status.set_defaults(func=_cl_status)

    # --- firewall ---
    fw_parser = cl_sub.add_parser("firewall", help="Manage cluster firewall")
    fw_sub = fw_parser.add_subparsers(dest="fw_action", title="firewall actions", required=True)

    # firewall options
    fw_opts = fw_sub.add_parser("options", help="Show cluster firewall options")
    fw_opts.set_defaults(func=_cl_fw_options)

    fw_opts_set = fw_sub.add_parser("enable", help="Enable cluster firewall")
    fw_opts_set.set_defaults(func=_cl_fw_enable)

    fw_opts_disable = fw_sub.add_parser("disable", help="Disable cluster firewall")
    fw_opts_disable.set_defaults(func=_cl_fw_disable)

    fw_policy = fw_sub.add_parser("policy", help="Set default firewall policy")
    fw_policy.add_argument("--in-policy", choices=["ACCEPT", "DENY", "REJECT"], default=None,
                           help="Default input policy")
    fw_policy.add_argument("--out-policy", choices=["ACCEPT", "DENY", "REJECT"], default=None,
                           help="Default output policy")
    fw_policy.set_defaults(func=_cl_fw_policy)

    # firewall rules
    fw_rules = fw_sub.add_parser("rules", help="List cluster firewall rules")
    fw_rules.set_defaults(func=_cl_fw_rules)

    fw_rule_add = fw_sub.add_parser("add-rule", help="Add a cluster firewall rule")
    add_firewall_rule_args(fw_rule_add)
    fw_rule_add.set_defaults(func=_cl_fw_rule_add)

    fw_rule_show = fw_sub.add_parser("show-rule", help="Show a cluster firewall rule")
    fw_rule_show.add_argument("pos", type=int, help="Rule position")
    fw_rule_show.set_defaults(func=_cl_fw_rule_show)

    fw_rule_upd = fw_sub.add_parser("update-rule", help="Update a cluster firewall rule")
    fw_rule_upd.add_argument("pos", type=int, help="Rule position")
    add_firewall_rule_args(fw_rule_upd)
    # Make action optional for updates
    for action in fw_rule_upd._actions:
        if action.dest == "action":
            action.required = False
            action.default = None
    fw_rule_upd.set_defaults(func=_cl_fw_rule_upd)

    fw_rule_del = fw_sub.add_parser("delete-rule", help="Delete a cluster firewall rule")
    fw_rule_del.add_argument("pos", type=int, help="Rule position")
    fw_rule_del.set_defaults(func=_cl_fw_rule_del)

    # firewall aliases
    fw_aliases = fw_sub.add_parser("aliases", help="List cluster firewall aliases")
    fw_aliases.set_defaults(func=_cl_fw_aliases)

    fw_alias_add = fw_sub.add_parser("add-alias", help="Add a cluster firewall alias")
    fw_alias_add.add_argument("name", help="Alias name")
    fw_alias_add.add_argument("--cidr", required=True, help="CIDR notation (e.g. 10.0.0.0/8)")
    fw_alias_add.add_argument("--comment", default=None, help="Comment / description")
    fw_alias_add.set_defaults(func=_cl_fw_alias_add)

    fw_alias_del = fw_sub.add_parser("delete-alias", help="Delete a cluster firewall alias")
    fw_alias_del.add_argument("name", help="Alias name")
    fw_alias_del.set_defaults(func=_cl_fw_alias_del)

    # firewall ipset
    fw_ipsets = fw_sub.add_parser("ipsets", help="List cluster firewall ipsets")
    fw_ipsets.set_defaults(func=_cl_fw_ipsets)

    fw_ipset_add = fw_sub.add_parser("add-ipset", help="Add a cluster firewall ipset")
    fw_ipset_add.add_argument("name", help="IPset name")
    fw_ipset_add.add_argument("--comment", default=None, help="Comment / description")
    fw_ipset_add.set_defaults(func=_cl_fw_ipset_add)

    fw_ipset_show = fw_sub.add_parser("show-ipset", help="Show ipset contents")
    fw_ipset_show.add_argument("name", help="IPset name")
    fw_ipset_show.set_defaults(func=_cl_fw_ipset_show)

    fw_ipset_del = fw_sub.add_parser("delete-ipset", help="Delete a cluster firewall ipset")
    fw_ipset_del.add_argument("name", help="IPset name")
    fw_ipset_del.set_defaults(func=_cl_fw_ipset_del)

    fw_ipset_add_cidr = fw_sub.add_parser("add-ipset-cidr", help="Add a CIDR to an ipset")
    fw_ipset_add_cidr.add_argument("name", help="IPset name")
    fw_ipset_add_cidr.add_argument("--cidr", required=True, help="CIDR to add")
    fw_ipset_add_cidr.add_argument("--comment", default=None, help="Comment")
    fw_ipset_add_cidr.add_argument("--nomatch", action="store_true", help="Exclude match")
    fw_ipset_add_cidr.set_defaults(func=_cl_fw_ipset_add_cidr)

    fw_ipset_del_cidr = fw_sub.add_parser("delete-ipset-cidr", help="Remove a CIDR from an ipset")
    fw_ipset_del_cidr.add_argument("name", help="IPset name")
    fw_ipset_del_cidr.add_argument("--cidr", required=True, help="CIDR to remove")
    fw_ipset_del_cidr.set_defaults(func=_cl_fw_ipset_del_cidr)

    # firewall refs
    fw_refs = fw_sub.add_parser("refs", help="List firewall references")
    fw_refs.add_argument("--type", default=None, choices=["alias", "ipset", "group"],
                         help="Filter by reference type")
    fw_refs.set_defaults(func=_cl_fw_refs)


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------

def _cl_status(_args: argparse.Namespace, client: ProxmoxClient) -> dict | list:
    return client.get("/cluster/status")


# --- Firewall options ---

def _cl_fw_options(_args: argparse.Namespace, client: ProxmoxClient) -> dict:
    return client.get("/cluster/firewall/options")


def _cl_fw_enable(_args: argparse.Namespace, client: ProxmoxClient) -> dict:
    return client.put("/cluster/firewall/options", data={"enable": 1})


def _cl_fw_disable(_args: argparse.Namespace, client: ProxmoxClient) -> dict:
    return client.put("/cluster/firewall/options", data={"enable": 0})


def _cl_fw_policy(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    data: dict = {}
    if args.in_policy is not None:
        data["policy_in"] = args.in_policy
    elif args.out_policy is not None:
        data["policy_out"] = args.out_policy
    if args.in_policy is not None:
        data["policy_in"] = args.in_policy
    if args.out_policy is not None:
        data["policy_out"] = args.out_policy
    if not data:
        return {"error": "No policy specified. Use --in-policy or --out-policy"}
    return client.put("/cluster/firewall/options", data=data)


# --- Firewall rules ---

def _cl_fw_rules(_args: argparse.Namespace, client: ProxmoxClient) -> dict | list:
    return client.get("/cluster/firewall/rules")


def _cl_fw_rule_add(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    return client.post("/cluster/firewall/rules", data=build_rule_data(args))


def _cl_fw_rule_show(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    return client.get(f"/cluster/firewall/rules/{args.pos}")


def _cl_fw_rule_upd(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    data = build_rule_data(args)
    # Remove None values so only provided fields are updated
    data = {k: v for k, v in data.items() if v is not None and v != 0}
    if "enable" in data or "action" not in args or args.action is not None:
        data["enable"] = args.enable
    return client.put(f"/cluster/firewall/rules/{args.pos}", data=data)


def _cl_fw_rule_del(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    return client.delete(f"/cluster/firewall/rules/{args.pos}")


# --- Firewall aliases ---

def _cl_fw_aliases(_args: argparse.Namespace, client: ProxmoxClient) -> dict | list:
    return client.get("/cluster/firewall/aliases")


def _cl_fw_alias_add(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    data = {"name": args.name, "cidr": args.cidr}
    if args.comment:
        data["comment"] = args.comment
    return client.post("/cluster/firewall/aliases", data=data)


def _cl_fw_alias_del(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    return client.delete(f"/cluster/firewall/aliases/{args.name}")


# --- Firewall ipsets ---

def _cl_fw_ipsets(_args: argparse.Namespace, client: ProxmoxClient) -> dict | list:
    return client.get("/cluster/firewall/ipset")


def _cl_fw_ipset_add(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    data: dict = {"name": args.name}
    if args.comment:
        data["comment"] = args.comment
    return client.post("/cluster/firewall/ipset", data=data)


def _cl_fw_ipset_show(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    return client.get(f"/cluster/firewall/ipset/{args.name}")


def _cl_fw_ipset_del(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    return client.delete(f"/cluster/firewall/ipset/{args.name}")


def _cl_fw_ipset_add_cidr(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    data: dict = {"cidr": args.cidr}
    if args.comment:
        data["comment"] = args.comment
    if args.nomatch:
        data["nomatch"] = 1
    return client.post(f"/cluster/firewall/ipset/{args.name}", data=data)


def _cl_fw_ipset_del_cidr(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    return client.delete(f"/cluster/firewall/ipset/{args.name}/{args.cidr}")


# --- Firewall refs ---

def _cl_fw_refs(args: argparse.Namespace, client: ProxmoxClient) -> dict | list:
    params = {"type": args.type} if args.type else None
    return client.get("/cluster/firewall/refs", params=params)
