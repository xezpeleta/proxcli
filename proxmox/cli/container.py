"""`proxmox container` subcommand — LXC container management."""

from __future__ import annotations

import argparse

from proxmox.cli.firewall_helpers import add_firewall_rule_args, build_rule_data
from proxmox.client.client import ProxmoxClient
from proxmox.utils.helpers import resolve_vmid, vmid_type


def register_container_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the `proxmox container` subcommand tree."""
    ct_parser = subparsers.add_parser("container", help="Manage LXC containers")
    ct_sub = ct_parser.add_subparsers(dest="action", title="actions", required=True)

    # --- container list ---
    ct_list = ct_sub.add_parser("list", help="List containers")
    ct_list.add_argument("--node", help="Filter by node name")
    ct_list.set_defaults(func=_ct_list)

    # --- container show ---
    ct_show = ct_sub.add_parser("show", help="Show container details")
    ct_show.add_argument("vmid", type=vmid_type, help="Container ID")
    ct_show.add_argument("--node", help="Node name (auto-detected if omitted)")
    ct_show.set_defaults(func=_ct_show)

    # --- container create ---
    ct_create = ct_sub.add_parser("create", help="Create a new container")
    ct_create.add_argument("--node", required=True, help="Target node")
    ct_create.add_argument("--vmid", type=vmid_type, default=None, help="Container ID (auto-assigned if omitted)")
    ct_create.add_argument("--ostemplate", required=True, help="OS template")
    ct_create.add_argument("--storage", default=None, help="Storage for the container")
    ct_create.add_argument("--memory", type=int, default=512, help="Memory in MB")
    ct_create.add_argument("--cores", type=int, default=1, help="CPU cores")
    ct_create.add_argument("--net", default=None, help="Network config (e.g. name=eth0,bridge=vmbr0,ip=dhcp)")
    ct_create.add_argument("--password", default=None, help="Root password")
    ct_create.set_defaults(func=_ct_create)

    # --- container start ---
    ct_start = ct_sub.add_parser("start", help="Start a container")
    ct_start.add_argument("vmid", type=vmid_type, help="Container ID")
    ct_start.add_argument("--node", help="Node name (auto-detected if omitted)")
    ct_start.set_defaults(func=_ct_start)

    # --- container stop ---
    ct_stop = ct_sub.add_parser("stop", help="Stop a container")
    ct_stop.add_argument("vmid", type=vmid_type, help="Container ID")
    ct_stop.add_argument("--node", help="Node name (auto-detected if omitted)")
    ct_stop.set_defaults(func=_ct_stop)

    # --- container delete ---
    ct_delete = ct_sub.add_parser("delete", help="Delete a container")
    ct_delete.add_argument("vmid", type=vmid_type, help="Container ID")
    ct_delete.add_argument("--node", help="Node name (auto-detected if omitted)")
    ct_delete.add_argument("--force", action="store_true", help="Force removal")
    ct_delete.add_argument("--purge", action="store_true", help="Purge from all configurations")
    ct_delete.set_defaults(func=_ct_delete)

    # --- container ip ---
    ct_ip = ct_sub.add_parser("ip", help="Show IP addresses of a container")
    ct_ip.add_argument("vmid", type=vmid_type, help="Container ID")
    ct_ip.add_argument("--node", help="Node name (auto-detected if omitted)")
    ct_ip.set_defaults(func=_ct_ip)

    # --- firewall ---
    fw = ct_sub.add_parser("firewall", help="Manage container firewall")
    fw_sub = fw.add_subparsers(dest="fw_resource", title="resources", required=True)

    fw_opts = fw_sub.add_parser("options", help="Show container firewall options")
    fw_opts.add_argument("vmid", type=vmid_type, help="Container ID")
    fw_opts.add_argument("--node", help="Node name (auto-detected if omitted)")
    fw_opts.set_defaults(func=_ct_fw_options)

    fw_enable = fw_sub.add_parser("enable", help="Enable container firewall")
    fw_enable.add_argument("vmid", type=vmid_type, help="Container ID")
    fw_enable.add_argument("--node", help="Node name (auto-detected if omitted)")
    fw_enable.set_defaults(func=_ct_fw_enable)

    fw_disable = fw_sub.add_parser("disable", help="Disable container firewall")
    fw_disable.add_argument("vmid", type=vmid_type, help="Container ID")
    fw_disable.add_argument("--node", help="Node name (auto-detected if omitted)")
    fw_disable.set_defaults(func=_ct_fw_disable)

    fw_policy = fw_sub.add_parser("policy", help="Set default input/output policy for container")
    fw_policy.add_argument("vmid", type=vmid_type, help="Container ID")
    fw_policy.add_argument("--node", help="Node name (auto-detected if omitted)")
    fw_policy.add_argument("--in-policy", choices=["ACCEPT", "DENY", "REJECT"], default=None,
                           help="Default input policy")
    fw_policy.add_argument("--out-policy", choices=["ACCEPT", "DENY", "REJECT"], default=None,
                           help="Default output policy")
    fw_policy.set_defaults(func=_ct_fw_policy)

    # firewall rules
    rules = fw_sub.add_parser("rules", help="Manage container firewall rules")
    rules_sub = rules.add_subparsers(dest="fw_action", title="rule actions", required=False)

    rules_list = rules_sub.add_parser("list", help="List rules")
    rules_list.add_argument("vmid", type=vmid_type, help="Container ID")
    rules_list.add_argument("--node", help="Node name (auto-detected if omitted)")
    rules_list.set_defaults(func=_ct_fw_rules)

    rules_add = rules_sub.add_parser("add", help="Add a rule")
    rules_add.add_argument("vmid", type=vmid_type, help="Container ID")
    rules_add.add_argument("--node", help="Node name (auto-detected if omitted)")
    add_firewall_rule_args(rules_add)
    rules_add.set_defaults(func=_ct_fw_rule_add)

    rules_show = rules_sub.add_parser("show", help="Show a rule by position")
    rules_show.add_argument("vmid", type=vmid_type, help="Container ID")
    rules_show.add_argument("--node", help="Node name (auto-detected if omitted)")
    rules_show.add_argument("pos", type=int, help="Rule position")
    rules_show.set_defaults(func=_ct_fw_rule_show)

    rules_upd = rules_sub.add_parser("update", help="Update a rule by position")
    rules_upd.add_argument("vmid", type=vmid_type, help="Container ID")
    rules_upd.add_argument("--node", help="Node name (auto-detected if omitted)")
    rules_upd.add_argument("pos", type=int, help="Rule position")
    add_firewall_rule_args(rules_upd)
    for action in rules_upd._actions:
        if action.dest == "action":
            action.required = False
            action.default = None
    rules_upd.set_defaults(func=_ct_fw_rule_upd)

    rules_del = rules_sub.add_parser("delete", help="Delete a rule by position")
    rules_del.add_argument("vmid", type=vmid_type, help="Container ID")
    rules_del.add_argument("--node", help="Node name (auto-detected if omitted)")
    rules_del.add_argument("pos", type=int, help="Rule position")
    rules_del.set_defaults(func=_ct_fw_rule_del)

    # firewall refs
    fw_refs = fw_sub.add_parser("refs", help="List container firewall references")
    fw_refs.add_argument("vmid", type=vmid_type, help="Container ID")
    fw_refs.add_argument("--node", help="Node name (auto-detected if omitted)")
    fw_refs.add_argument("--type", default=None, choices=["alias", "ipset", "group"],
                         help="Filter by reference type")
    fw_refs.set_defaults(func=_ct_fw_refs)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_ct_node(client: ProxmoxClient, node: str | None, vmid: int) -> str | None:
    if node:
        return node
    try:
        resources = client.get("/cluster/resources", params={"type": "vm"})
        if isinstance(resources, list):
            for r in resources:
                if r.get("vmid") == vmid:
                    return r.get("node")
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------

def _ct_list(args: argparse.Namespace, client: ProxmoxClient) -> dict | list:
    if args.node:
        return client.get(f"/nodes/{args.node}/lxc")
    nodes = client.get("/nodes")
    if isinstance(nodes, dict):
        nodes = nodes.get("data", [])
    cts: list[dict] = []
    for n in (nodes if isinstance(nodes, list) else []):
        node_name = n.get("node") if isinstance(n, dict) else n
        try:
            node_cts = client.get(f"/nodes/{node_name}/lxc")
            if isinstance(node_cts, list):
                for ct in node_cts:
                    if isinstance(ct, dict):
                        ct["_node"] = node_name
                    cts.append(ct)
            elif isinstance(node_cts, dict):
                for ct in node_cts.get("data", []):
                    if isinstance(ct, dict):
                        ct["_node"] = node_name
                    cts.append(ct)
        except Exception:
            pass
    return cts


def _ct_show(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    node = _resolve_ct_node(client, args.node, args.vmid)
    if not node:
        return {"error": f"Container {args.vmid} not found"}
    result = client.get(f"/nodes/{node}/lxc/{args.vmid}/status/current")
    if isinstance(result, dict):
        result["_node"] = node
    return result


def _ct_create(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    data: dict = {
        "vmid": resolve_vmid(client, args.vmid),
        "ostemplate": args.ostemplate,
        "memory": args.memory,
        "cores": args.cores,
    }
    if args.storage:
        data["storage"] = args.storage
    if args.net:
        data["net0"] = args.net
    if args.password:
        data["password"] = args.password
    return client.post(f"/nodes/{args.node}/lxc", data=data)


def _ct_start(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    node = _resolve_ct_node(client, args.node, args.vmid)
    if not node:
        return {"error": f"Container {args.vmid} not found"}
    return client.post(f"/nodes/{node}/lxc/{args.vmid}/status/start")


def _ct_stop(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    node = _resolve_ct_node(client, args.node, args.vmid)
    if not node:
        return {"error": f"Container {args.vmid} not found"}
    return client.post(f"/nodes/{node}/lxc/{args.vmid}/status/stop")


def _ct_delete(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    node = _resolve_ct_node(client, args.node, args.vmid)
    if not node:
        return {"error": f"Container {args.vmid} not found"}
    params: dict = {}
    if args.force:
        params["force"] = 1
    if args.purge:
        params["purge"] = 1
    return client.delete(f"/nodes/{node}/lxc/{args.vmid}", params=params or None)


def _ct_ip(args: argparse.Namespace, client: ProxmoxClient) -> dict | list:
    """Show IP addresses of a container.

    Wraps ``GET /nodes/{node}/lxc/{vmid}/interfaces``.
    """
    from typing import Any

    node = _resolve_ct_node(client, args.node, args.vmid)
    if not node:
        return {"error": f"Container {args.vmid} not found"}
    result = client.get(f"/nodes/{node}/lxc/{args.vmid}/interfaces")
    data = result if isinstance(result, list) else result.get("data", []) if isinstance(result, dict) else []

    ips: list[dict[str, Any]] = []
    for iface in data:
        if not isinstance(iface, dict):
            continue
        name = iface.get("name", "")
        # LXC interface model: name, inet (string), inet6 (string)
        for af, key in [("inet", "inet"), ("inet6", "inet6")]:
            addr_val = iface.get(key, "")
            if addr_val and addr_val != "auto" and "/" in str(addr_val):
                ip_part, prefix = str(addr_val).split("/", 1)
                if ip_part.startswith("127.") or ip_part == "::1" or ip_part.startswith("fe80:"):
                    continue
                ips.append({
                    "interface": name,
                    "family": af,
                    "ip": ip_part,
                    "prefix": int(prefix) if prefix.isdigit() else prefix,
                    "address": str(addr_val),
                    "_vmid": args.vmid,
                    "_node": node,
                })
    return ips if ips else {"message": f"No non-local IPs found for container {args.vmid}"}


# ---------------------------------------------------------------------------
# Container firewall handlers
# ---------------------------------------------------------------------------

def _ct_fw_options(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    node = _resolve_ct_node(client, args.node, args.vmid)
    if not node:
        return {"error": f"Container {args.vmid} not found"}
    return client.get(f"/nodes/{node}/lxc/{args.vmid}/firewall/options")


def _ct_fw_enable(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    node = _resolve_ct_node(client, args.node, args.vmid)
    if not node:
        return {"error": f"Container {args.vmid} not found"}
    return client.put(f"/nodes/{node}/lxc/{args.vmid}/firewall/options", data={"enable": 1})


def _ct_fw_disable(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    node = _resolve_ct_node(client, args.node, args.vmid)
    if not node:
        return {"error": f"Container {args.vmid} not found"}
    return client.put(f"/nodes/{node}/lxc/{args.vmid}/firewall/options", data={"enable": 0})


def _ct_fw_policy(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    node = _resolve_ct_node(client, args.node, args.vmid)
    if not node:
        return {"error": f"Container {args.vmid} not found"}
    data: dict = {}
    if args.in_policy:
        data["policy_in"] = args.in_policy
    if args.out_policy:
        data["policy_out"] = args.out_policy
    if not data:
        return {"error": "No policy specified. Use --in-policy or --out-policy"}
    return client.put(f"/nodes/{node}/lxc/{args.vmid}/firewall/options", data=data)


def _ct_fw_rules(args: argparse.Namespace, client: ProxmoxClient) -> dict | list:
    node = _resolve_ct_node(client, args.node, args.vmid)
    if not node:
        return {"error": f"Container {args.vmid} not found"}
    return client.get(f"/nodes/{node}/lxc/{args.vmid}/firewall/rules")


def _ct_fw_rule_add(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    node = _resolve_ct_node(client, args.node, args.vmid)
    if not node:
        return {"error": f"Container {args.vmid} not found"}
    return client.post(f"/nodes/{node}/lxc/{args.vmid}/firewall/rules",
                       data=build_rule_data(args))


def _ct_fw_rule_show(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    node = _resolve_ct_node(client, args.node, args.vmid)
    if not node:
        return {"error": f"Container {args.vmid} not found"}
    return client.get(f"/nodes/{node}/lxc/{args.vmid}/firewall/rules/{args.pos}")


def _ct_fw_rule_upd(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    node = _resolve_ct_node(client, args.node, args.vmid)
    if not node:
        return {"error": f"Container {args.vmid} not found"}
    data = {k: v for k, v in build_rule_data(args).items() if v is not None and v != 0}
    return client.put(f"/nodes/{node}/lxc/{args.vmid}/firewall/rules/{args.pos}", data=data)


def _ct_fw_rule_del(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    node = _resolve_ct_node(client, args.node, args.vmid)
    if not node:
        return {"error": f"Container {args.vmid} not found"}
    return client.delete(f"/nodes/{node}/lxc/{args.vmid}/firewall/rules/{args.pos}")


def _ct_fw_refs(args: argparse.Namespace, client: ProxmoxClient) -> dict | list:
    node = _resolve_ct_node(client, args.node, args.vmid)
    if not node:
        return {"error": f"Container {args.vmid} not found"}
    params: dict | None = {"type": args.type} if args.type else None
    return client.get(f"/nodes/{node}/lxc/{args.vmid}/firewall/refs", params=params)
