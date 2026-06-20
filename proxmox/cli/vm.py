"""`proxmox vm` subcommand — QEMU virtual machine management."""

from __future__ import annotations

import argparse

from proxmox.client.client import ProxmoxClient
from proxmox.utils.helpers import vmid_type


def register_vm_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the `proxmox vm` subcommand tree."""
    vm_parser = subparsers.add_parser("vm", help="Manage QEMU virtual machines")
    vm_sub = vm_parser.add_subparsers(dest="action", title="actions", required=True)

    # --- vm list ---
    vm_list = vm_sub.add_parser("list", help="List virtual machines")
    vm_list.add_argument("--node", help="Filter by node name")
    vm_list.set_defaults(func=_vm_list)

    # --- vm show ---
    vm_show = vm_sub.add_parser("show", help="Show VM details")
    vm_show.add_argument("vmid", type=vmid_type, help="VM ID")
    vm_show.add_argument("--node", help="Node name (auto-detected if omitted)")
    vm_show.set_defaults(func=_vm_show)

    # --- vm create ---
    vm_create = vm_sub.add_parser("create", help="Create a new VM")
    vm_create.add_argument("--node", required=True, help="Target node")
    vm_create.add_argument("--vmid", type=vmid_type, required=True, help="VM ID")
    vm_create.add_argument("--memory", type=int, required=True, help="Memory in MB")
    vm_create.add_argument("--cores", type=int, default=1, help="CPU cores (default: 1)")
    vm_create.add_argument("--net", default=None, help="Network config (e.g. model=virtio,bridge=vmbr0)")
    vm_create.add_argument("--storage", default=None, help="Storage for the VM disk")
    vm_create.add_argument("--ostemplate", default=None, help="OS template/ISO")
    vm_create.add_argument("--name", default=None, help="VM name")
    vm_create.set_defaults(func=_vm_create)

    # --- vm start ---
    vm_start = vm_sub.add_parser("start", help="Start a VM")
    vm_start.add_argument("vmid", type=vmid_type, help="VM ID")
    vm_start.add_argument("--node", help="Node name (auto-detected if omitted)")
    vm_start.set_defaults(func=_vm_start)

    # --- vm stop ---
    vm_stop = vm_sub.add_parser("stop", help="Stop a VM")
    vm_stop.add_argument("vmid", type=vmid_type, help="VM ID")
    vm_stop.add_argument("--node", help="Node name (auto-detected if omitted)")
    vm_stop.set_defaults(func=_vm_stop)

    # --- vm reboot ---
    vm_reboot = vm_sub.add_parser("reboot", help="Reboot a VM")
    vm_reboot.add_argument("vmid", type=vmid_type, help="VM ID")
    vm_reboot.add_argument("--node", help="Node name (auto-detected if omitted)")
    vm_reboot.set_defaults(func=_vm_reboot)

    # --- vm suspend ---
    vm_suspend = vm_sub.add_parser("suspend", help="Suspend a VM")
    vm_suspend.add_argument("vmid", type=vmid_type, help="VM ID")
    vm_suspend.add_argument("--node", help="Node name (auto-detected if omitted)")
    vm_suspend.set_defaults(func=_vm_suspend)

    # --- vm resume ---
    vm_resume = vm_sub.add_parser("resume", help="Resume a VM")
    vm_resume.add_argument("vmid", type=vmid_type, help="VM ID")
    vm_resume.add_argument("--node", help="Node name (auto-detected if omitted)")
    vm_resume.set_defaults(func=_vm_resume)

    # --- vm delete ---
    vm_delete = vm_sub.add_parser("delete", help="Delete a VM")
    vm_delete.add_argument("vmid", type=vmid_type, help="VM ID")
    vm_delete.add_argument("--node", help="Node name (auto-detected if omitted)")
    vm_delete.add_argument("--force", action="store_true", help="Force removal")
    vm_delete.add_argument("--purge", action="store_true", help="Purge VM from all configurations")
    vm_delete.set_defaults(func=_vm_delete)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_node(client: ProxmoxClient, node: str | None, vmid: int) -> str | None:
    """Resolve which node hosts a given VMID, unless node is already provided."""
    if node:
        return node
    # Try cluster resources lookup
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

def _vm_list(args: argparse.Namespace, client: ProxmoxClient) -> dict | list:
    if args.node:
        result = client.get(f"/nodes/{args.node}/qemu")
        return result if isinstance(result, list) else result.get("data", result)
    # All nodes: iterate
    nodes = client.get("/nodes")
    if isinstance(nodes, dict):
        nodes = nodes.get("data", [])
    vms: list[dict] = []
    for n in (nodes if isinstance(nodes, list) else []):
        node_name = n.get("node") if isinstance(n, dict) else n
        try:
            node_vms = client.get(f"/nodes/{node_name}/qemu")
            if isinstance(node_vms, list):
                for vm in node_vms:
                    if isinstance(vm, dict):
                        vm["_node"] = node_name
                    vms.append(vm)
            elif isinstance(node_vms, dict):
                for vm in node_vms.get("data", []):
                    if isinstance(vm, dict):
                        vm["_node"] = node_name
                    vms.append(vm)
        except Exception:
            pass
    return vms


def _vm_show(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    node = _resolve_node(client, args.node, args.vmid)
    if not node:
        return {"error": f"VM {args.vmid} not found on any node"}
    resources = client.get(f"/nodes/{node}/qemu/{args.vmid}/status/current")
    if isinstance(resources, dict):
        resources["_node"] = node
    else:
        resources = {"data": resources, "_node": node}
    return resources


def _vm_create(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    data: dict = {
        "vmid": args.vmid,
        "memory": args.memory,
        "cores": args.cores,
    }
    if args.net:
        data["net0"] = args.net
    if args.name:
        data["name"] = args.name
    if args.ostemplate:
        data["ostemplate"] = args.ostemplate
    if args.storage:
        data["storage"] = args.storage

    result = client.post(f"/nodes/{args.node}/qemu", data=data)
    return result if isinstance(result, dict) else {"data": result}


def _vm_start(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    node = _resolve_node(client, args.node, args.vmid)
    if not node:
        return {"error": f"VM {args.vmid} not found"}
    result = client.post(f"/nodes/{node}/qemu/{args.vmid}/status/start")
    return result if isinstance(result, dict) else {"data": result}


def _vm_stop(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    node = _resolve_node(client, args.node, args.vmid)
    if not node:
        return {"error": f"VM {args.vmid} not found"}
    result = client.post(f"/nodes/{node}/qemu/{args.vmid}/status/stop")
    return result if isinstance(result, dict) else {"data": result}


def _vm_reboot(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    node = _resolve_node(client, args.node, args.vmid)
    if not node:
        return {"error": f"VM {args.vmid} not found"}
    result = client.post(f"/nodes/{node}/qemu/{args.vmid}/status/reboot")
    return result if isinstance(result, dict) else {"data": result}


def _vm_suspend(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    node = _resolve_node(client, args.node, args.vmid)
    if not node:
        return {"error": f"VM {args.vmid} not found"}
    result = client.post(f"/nodes/{node}/qemu/{args.vmid}/status/suspend")
    return result if isinstance(result, dict) else {"data": result}


def _vm_resume(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    node = _resolve_node(client, args.node, args.vmid)
    if not node:
        return {"error": f"VM {args.vmid} not found"}
    result = client.post(f"/nodes/{node}/qemu/{args.vmid}/status/resume")
    return result if isinstance(result, dict) else {"data": result}


def _vm_delete(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    node = _resolve_node(client, args.node, args.vmid)
    if not node:
        return {"error": f"VM {args.vmid} not found"}
    params: dict = {}
    if args.force:
        params["force"] = 1
    if args.purge:
        params["purge"] = 1
    result = client.delete(f"/nodes/{node}/qemu/{args.vmid}", params=params or None)
    return result if isinstance(result, dict) else {"data": result}
