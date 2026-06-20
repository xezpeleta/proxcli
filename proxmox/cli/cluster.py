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

    # --- cluster log ---
    cl_log = cl_sub.add_parser("log", help="Show cluster log")
    cl_log.add_argument("--limit", type=int, default=50, help="Number of entries (default: 50)")
    cl_log.add_argument("--follow", "-f", action="store_true", help="Follow log output")
    cl_log.set_defaults(func=_cl_log, output_format="log")

    # --- cluster options ---
    cl_opts = cl_sub.add_parser("options", help="Show cluster-wide options")
    cl_opts.set_defaults(func=_cl_options)

    # --- firewall ---
    fw = cl_sub.add_parser("firewall", help="Manage cluster firewall")
    fw_sub = fw.add_subparsers(dest="fw_resource", title="resources", required=True)

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
    rules = fw_sub.add_parser("rules", help="Manage cluster firewall rules")
    rules.set_defaults(func=_cl_fw_rules)
    rules_sub = rules.add_subparsers(dest="fw_action", title="rule actions", required=False)

    rules_list = rules_sub.add_parser("list", help="List rules")
    rules_list.set_defaults(func=_cl_fw_rules)

    rules_add = rules_sub.add_parser("add", help="Add a rule")
    add_firewall_rule_args(rules_add)
    rules_add.set_defaults(func=_cl_fw_rule_add)

    rules_show = rules_sub.add_parser("show", help="Show a rule by position")
    rules_show.add_argument("pos", type=int, help="Rule position")
    rules_show.set_defaults(func=_cl_fw_rule_show)

    rules_upd = rules_sub.add_parser("update", help="Update a rule by position")
    rules_upd.add_argument("pos", type=int, help="Rule position")
    add_firewall_rule_args(rules_upd)
    for action in rules_upd._actions:
        if action.dest == "action":
            action.required = False
            action.default = None
    rules_upd.set_defaults(func=_cl_fw_rule_upd)

    rules_del = rules_sub.add_parser("delete", help="Delete a rule by position")
    rules_del.add_argument("pos", type=int, help="Rule position")
    rules_del.set_defaults(func=_cl_fw_rule_del)

    # firewall aliases
    aliases = fw_sub.add_parser("aliases", help="Manage firewall aliases")
    aliases.set_defaults(func=_cl_fw_aliases)
    aliases_sub = aliases.add_subparsers(dest="fw_action", title="alias actions", required=False)

    aliases_list = aliases_sub.add_parser("list", help="List aliases")
    aliases_list.set_defaults(func=_cl_fw_aliases)

    aliases_add = aliases_sub.add_parser("add", help="Add an alias")
    aliases_add.add_argument("name", help="Alias name")
    aliases_add.add_argument("--cidr", required=True, help="CIDR notation (e.g. 10.0.0.0/8)")
    aliases_add.add_argument("--comment", default=None, help="Comment / description")
    aliases_add.set_defaults(func=_cl_fw_alias_add)

    aliases_del = aliases_sub.add_parser("delete", help="Delete an alias")
    aliases_del.add_argument("name", help="Alias name")
    aliases_del.set_defaults(func=_cl_fw_alias_del)

    # firewall ipsets
    ipsets = fw_sub.add_parser("ipsets", help="Manage firewall ipsets")
    ipsets.set_defaults(func=_cl_fw_ipsets)
    ipsets_sub = ipsets.add_subparsers(dest="fw_action", title="ipset actions", required=False)

    ipsets_list = ipsets_sub.add_parser("list", help="List ipsets")
    ipsets_list.set_defaults(func=_cl_fw_ipsets)

    ipsets_add = ipsets_sub.add_parser("add", help="Add an ipset")
    ipsets_add.add_argument("name", help="IPset name")
    ipsets_add.add_argument("--comment", default=None, help="Comment / description")
    ipsets_add.set_defaults(func=_cl_fw_ipset_add)

    ipsets_show = ipsets_sub.add_parser("show", help="Show ipset contents")
    ipsets_show.add_argument("name", help="IPset name")
    ipsets_show.set_defaults(func=_cl_fw_ipset_show)

    ipsets_del = ipsets_sub.add_parser("delete", help="Delete an ipset")
    ipsets_del.add_argument("name", help="IPset name")
    ipsets_del.set_defaults(func=_cl_fw_ipset_del)

    ipsets_add_cidr = ipsets_sub.add_parser("add-cidr", help="Add a CIDR to an ipset")
    ipsets_add_cidr.add_argument("name", help="IPset name")
    ipsets_add_cidr.add_argument("--cidr", required=True, help="CIDR to add")
    ipsets_add_cidr.add_argument("--comment", default=None, help="Comment")
    ipsets_add_cidr.add_argument("--nomatch", action="store_true", help="Exclude match")
    ipsets_add_cidr.set_defaults(func=_cl_fw_ipset_add_cidr)

    ipsets_del_cidr = ipsets_sub.add_parser("delete-cidr", help="Remove a CIDR from an ipset")
    ipsets_del_cidr.add_argument("name", help="IPset name")
    ipsets_del_cidr.add_argument("--cidr", required=True, help="CIDR to remove")
    ipsets_del_cidr.set_defaults(func=_cl_fw_ipset_del_cidr)

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


def _cl_log(args: argparse.Namespace, client: ProxmoxClient) -> list | None:
    if args.follow:
        client.stream_log("/cluster/log", follow=True, params={"max": args.limit})
        return None
    data = client.get("/cluster/log", params={"max": args.limit})
    return list(reversed(data)) if isinstance(data, list) else data


def _cl_options(_args: argparse.Namespace, client: ProxmoxClient) -> dict:
    return client.get("/cluster/options")


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
    data = {k: v for k, v in build_rule_data(args).items() if v is not None and v != 0}
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
