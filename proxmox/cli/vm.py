"""`proxmox vm` subcommand — QEMU virtual machine management."""

from __future__ import annotations

import argparse
from typing import Any

from proxmox.cli.firewall_helpers import add_firewall_rule_args, build_rule_data
from proxmox.client.client import ProxmoxClient
from proxmox.utils.helpers import resolve_vmid, vmid_type


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
    vm_create.add_argument("--node", default=None, help="Target node (required if not in --file)")
    vm_create.add_argument("--vmid", type=vmid_type, default=None, help="VM ID (auto-assigned if omitted)")
    vm_create.add_argument("--memory", type=int, default=None, help="Memory in MB (required if not in --file)")
    vm_create.add_argument("--cores", type=int, default=None, help="CPU cores (default: 1)")
    vm_create.add_argument(
        "--net", default=None, action="append", dest="net_ifaces",
        help="Network config (e.g. virtio=MAC,bridge=vmbr0). Repeat for multiple NICs."
    )
    vm_create.add_argument("--storage", default=None, help="Storage for the VM disk")
    vm_create.add_argument("--cdrom", default=None, help="ISO volume for install (e.g. local:iso/debian.iso)")
    vm_create.add_argument("--name", default=None, help="VM name")
    vm_create.add_argument("--scsihw", default=None, choices=["lsi", "lsi53c810", "virtio-scsi-pci", "virtio-scsi-single", "megasas", "pvscsi"],
                           help="SCSI controller type")
    vm_create.add_argument("--bios", default=None, choices=["seabios", "ovmf"], help="BIOS type")
    vm_create.add_argument("--machine", default=None, help="Machine type (e.g. q35)")
    vm_create.add_argument("--boot", default=None, help="Boot order (e.g. order=cd;net)")
    vm_create.add_argument("--disk", default=None, help="Disk size (e.g. 32G). Uses --storage if set, else local-lvm.")
    vm_create.add_argument("--citype", default=None, choices=["nocloud", "configdrive2"],
                           help="Cloud-init type")
    vm_create.add_argument("--ciuser", default=None, help="Cloud-init user")
    vm_create.add_argument("--cipassword", default=None, help="Cloud-init password")
    vm_create.add_argument("--sshkeys", default=None, help="Cloud-init SSH public keys (file path or inline)")
    vm_create.add_argument("--nameserver", default=None, help="Cloud-init DNS server")
    vm_create.add_argument("--searchdomain", default=None, help="Cloud-init DNS search domain")
    vm_create.add_argument("--cicustom", default=None, help="Cloud-init custom config (user=...,vendor=...)")
    vm_create.add_argument("--import-from", default=None, dest="import_from",
                           help="Import disk from existing volume (e.g. local:import/deb12.qcow2)")
    vm_create.add_argument("--file", default=None, dest="spec_file",
                           help="YAML file with VM spec (flat Proxmox config keys). CLI flags override file values.")
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

    # --- vm clone ---
    vm_clone = vm_sub.add_parser("clone", help="Clone a VM to a new VMID")
    vm_clone.add_argument("vmid", type=vmid_type, help="Source VM ID")
    vm_clone.add_argument("--newid", type=vmid_type, required=True, help="Target VM ID for the clone")
    vm_clone.add_argument("--node", help="Source node (auto-detected if omitted)")
    vm_clone.add_argument("--name", default=None, help="Name for the cloned VM")
    vm_clone.add_argument("--target-node", default=None, dest="target_node",
                           help="Target node (default: same as source)")
    vm_clone.add_argument("--target-storage", default=None, dest="target_storage",
                           help="Target storage (default: same as source)")
    vm_clone.add_argument("--full", type=int, choices=[0, 1], default=1,
                           help="Full clone (1) or linked clone (0). Default: 1 (full)")
    vm_clone.add_argument("--description", default=None, help="Description for the cloned VM")
    vm_clone.add_argument("--pool", default=None, help="Add the clone to a pool")
    vm_clone.set_defaults(func=_vm_clone)

    # --- vm config ---
    vm_config = vm_sub.add_parser("config", help="Show VM configuration (clean, suitable for --file import)")
    vm_config.add_argument("vmid", type=vmid_type, help="VM ID")
    vm_config.add_argument("--node", help="Node name (auto-detected if omitted)")
    vm_config.set_defaults(func=_vm_config)

    # --- snapshot ---
    snap = vm_sub.add_parser("snapshot", help="Manage VM snapshots")
    snap_sub = snap.add_subparsers(dest="snap_action", title="snapshot actions", required=True)

    snap_list = snap_sub.add_parser("list", help="List snapshots")
    snap_list.add_argument("vmid", type=vmid_type, help="VM ID")
    snap_list.add_argument("--node", help="Node name (auto-detected if omitted)")
    snap_list.set_defaults(func=_vm_snapshot_list)

    snap_create = snap_sub.add_parser("create", help="Create a snapshot")
    snap_create.add_argument("vmid", type=vmid_type, help="VM ID")
    snap_create.add_argument("snapname", help="Snapshot name")
    snap_create.add_argument("--node", help="Node name (auto-detected if omitted)")
    snap_create.add_argument("--description", default=None, help="Snapshot description")
    snap_create.add_argument("--vmstate", type=int, choices=[0, 1], default=0,
                             help="Include RAM state (1=yes, 0=no, default: 0)")
    snap_create.set_defaults(func=_vm_snapshot_create)

    snap_show = snap_sub.add_parser("show", help="Show snapshot details")
    snap_show.add_argument("vmid", type=vmid_type, help="VM ID")
    snap_show.add_argument("snapname", help="Snapshot name")
    snap_show.add_argument("--node", help="Node name (auto-detected if omitted)")
    snap_show.set_defaults(func=_vm_snapshot_show)

    snap_rollback = snap_sub.add_parser("rollback", help="Rollback to a snapshot")
    snap_rollback.add_argument("vmid", type=vmid_type, help="VM ID")
    snap_rollback.add_argument("snapname", help="Snapshot name")
    snap_rollback.add_argument("--node", help="Node name (auto-detected if omitted)")
    snap_rollback.add_argument("--start", type=int, choices=[0, 1], default=0,
                               help="Start VM after rollback (1=yes, 0=no, default: 0)")
    snap_rollback.set_defaults(func=_vm_snapshot_rollback)

    snap_delete = snap_sub.add_parser("delete", help="Delete a snapshot")
    snap_delete.add_argument("vmid", type=vmid_type, help="VM ID")
    snap_delete.add_argument("snapname", help="Snapshot name")
    snap_delete.add_argument("--node", help="Node name (auto-detected if omitted)")
    snap_delete.add_argument("--force", type=int, choices=[0, 1], default=0,
                             help="Force removal (1=yes, 0=no, default: 0)")
    snap_delete.set_defaults(func=_vm_snapshot_delete)

    # --- agent ---
    agent = vm_sub.add_parser("agent", help="Query QEMU guest agent")
    agent_sub = agent.add_subparsers(dest="agent_action", title="agent actions", required=True)

    agent_ifaces = agent_sub.add_parser("interfaces", help="List network interfaces via guest agent")
    agent_ifaces.add_argument("vmid", type=vmid_type, help="VM ID")
    agent_ifaces.add_argument("--node", help="Node name (auto-detected if omitted)")
    agent_ifaces.set_defaults(func=_vm_agent_interfaces)

    # --- cloudinit ---
    cloudinit = vm_sub.add_parser("cloudinit", help="Manage cloud-init")
    cloudinit_sub = cloudinit.add_subparsers(dest="cloudinit_action", title="cloud-init actions", required=True)

    ci_generate = cloudinit_sub.add_parser("generate", help="Regenerate cloud-init ISO from current config")
    ci_generate.add_argument("vmid", type=vmid_type, help="VM ID")
    ci_generate.add_argument("--node", help="Node name (auto-detected if omitted)")
    ci_generate.set_defaults(func=_vm_cloudinit_generate)

    # --- firewall ---
    fw = vm_sub.add_parser("firewall", help="Manage VM firewall")
    fw_sub = fw.add_subparsers(dest="fw_resource", title="resources", required=True)

    fw_opts = fw_sub.add_parser("options", help="Show VM firewall options")
    fw_opts.add_argument("vmid", type=vmid_type, help="VM ID")
    fw_opts.add_argument("--node", help="Node name (auto-detected if omitted)")
    fw_opts.set_defaults(func=_vm_fw_options)

    fw_enable = fw_sub.add_parser("enable", help="Enable VM firewall")
    fw_enable.add_argument("vmid", type=vmid_type, help="VM ID")
    fw_enable.add_argument("--node", help="Node name (auto-detected if omitted)")
    fw_enable.set_defaults(func=_vm_fw_enable)

    fw_disable = fw_sub.add_parser("disable", help="Disable VM firewall")
    fw_disable.add_argument("vmid", type=vmid_type, help="VM ID")
    fw_disable.add_argument("--node", help="Node name (auto-detected if omitted)")
    fw_disable.set_defaults(func=_vm_fw_disable)

    fw_policy = fw_sub.add_parser("policy", help="Set default input/output policy for VM")
    fw_policy.add_argument("vmid", type=vmid_type, help="VM ID")
    fw_policy.add_argument("--node", help="Node name (auto-detected if omitted)")
    fw_policy.add_argument("--in-policy", choices=["ACCEPT", "DENY", "REJECT"], default=None,
                           help="Default input policy")
    fw_policy.add_argument("--out-policy", choices=["ACCEPT", "DENY", "REJECT"], default=None,
                           help="Default output policy")
    fw_policy.set_defaults(func=_vm_fw_policy)

    # firewall rules
    rules = fw_sub.add_parser("rules", help="Manage VM firewall rules")
    rules_sub = rules.add_subparsers(dest="fw_action", title="rule actions", required=False)

    rules_list = rules_sub.add_parser("list", help="List rules")
    rules_list.add_argument("vmid", type=vmid_type, help="VM ID")
    rules_list.add_argument("--node", help="Node name (auto-detected if omitted)")
    rules_list.set_defaults(func=_vm_fw_rules)

    rules_add = rules_sub.add_parser("add", help="Add a rule")
    rules_add.add_argument("vmid", type=vmid_type, help="VM ID")
    rules_add.add_argument("--node", help="Node name (auto-detected if omitted)")
    add_firewall_rule_args(rules_add)
    rules_add.set_defaults(func=_vm_fw_rule_add)

    rules_show = rules_sub.add_parser("show", help="Show a rule by position")
    rules_show.add_argument("vmid", type=vmid_type, help="VM ID")
    rules_show.add_argument("--node", help="Node name (auto-detected if omitted)")
    rules_show.add_argument("pos", type=int, help="Rule position")
    rules_show.set_defaults(func=_vm_fw_rule_show)

    rules_upd = rules_sub.add_parser("update", help="Update a rule by position")
    rules_upd.add_argument("vmid", type=vmid_type, help="VM ID")
    rules_upd.add_argument("--node", help="Node name (auto-detected if omitted)")
    rules_upd.add_argument("pos", type=int, help="Rule position")
    add_firewall_rule_args(rules_upd)
    for action in rules_upd._actions:
        if action.dest == "action":
            action.required = False
            action.default = None
    rules_upd.set_defaults(func=_vm_fw_rule_upd)

    rules_del = rules_sub.add_parser("delete", help="Delete a rule by position")
    rules_del.add_argument("vmid", type=vmid_type, help="VM ID")
    rules_del.add_argument("--node", help="Node name (auto-detected if omitted)")
    rules_del.add_argument("pos", type=int, help="Rule position")
    rules_del.set_defaults(func=_vm_fw_rule_del)

    # firewall refs
    fw_refs = fw_sub.add_parser("refs", help="List VM firewall references")
    fw_refs.add_argument("vmid", type=vmid_type, help="VM ID")
    fw_refs.add_argument("--node", help="Node name (auto-detected if omitted)")
    fw_refs.add_argument("--type", default=None, choices=["alias", "ipset", "group"],
                         help="Filter by reference type")
    fw_refs.set_defaults(func=_vm_fw_refs)


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


def _vm_config(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    """Return clean VM config (no status/runtime info, no internal fields).

    Suitable for piping through --output yaml to get a file ready for --file import.
    """
    from proxmox.cli.vm_spec import clean_vm_config

    node = _resolve_node(client, args.node, args.vmid)
    if not node:
        return {"error": f"VM {args.vmid} not found on any node"}
    config = client.get(f"/nodes/{node}/qemu/{args.vmid}/config")
    if not isinstance(config, dict):
        return {"error": f"Could not read config for VM {args.vmid}"}
    # Add node for export convenience
    cleaned = clean_vm_config(config)
    cleaned["node"] = node
    cleaned["vmid"] = args.vmid
    return cleaned


def _vm_create(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    """Create a VM from CLI flags and/or a YAML spec file.

    CLI flags take precedence over --file values. The file format
    uses native Proxmox VM config keys (name, memory, cores, net0, etc.).
    """
    # --- Load from file if --file is specified ---
    file_spec: dict[str, Any] = {}
    file_node: str | None = None

    if args.spec_file:
        from proxmox.cli.vm_spec import load_vm_spec

        file_spec = load_vm_spec(args.spec_file)
        if isinstance(file_spec, dict) and "error" in file_spec:
            return file_spec  # propagate YAML/parse errors
        # Extract node from file (not an API body param)
        file_node = file_spec.pop("_node", None)

    # --- Determine node: CLI flag > file > (required) ---
    node: str | None = args.node
    if not node and file_node:
        node = file_node
    if not node:
        return {"error": "--node is required (or set 'node:' in the spec file)"}

    # --- Build data dict: file_spec is base, CLI flags override ---
    vmid = resolve_vmid(client, args.vmid)
    data: dict[str, Any] = {"vmid": str(vmid)}

    # Start with file_spec values
    data.update(file_spec)

    # Override with CLI flags (only when explicitly set)
    if args.memory is not None:
        data["memory"] = str(args.memory)
    if args.cores is not None:
        data["cores"] = str(args.cores)
    if args.name:
        data["name"] = args.name
    if args.bios:
        data["bios"] = args.bios
    if args.machine:
        data["machine"] = args.machine
    if args.scsihw:
        data["scsihw"] = args.scsihw
    if args.boot:
        data["boot"] = args.boot

    # Network interfaces: net0, net1, ...
    if args.net_ifaces:
        for i, net_cfg in enumerate(args.net_ifaces):
            encoded = net_cfg.replace("=", "%3D").replace(":", "%3A").replace(",", "%2C")
            data[f"net{i}"] = encoded
    # If no CLI nets but file has them, keep file's net keys as-is (already pre-encoded by vm_spec)

    # CD-ROM / ISO
    if args.cdrom:
        ide_raw = f"file={args.cdrom},media=cdrom"
        data["ide2"] = ide_raw.replace("=", "%3D").replace(":", "%3A").replace(",", "%2C")

    # Disk / import
    if args.disk:
        storage = args.storage or "local-lvm"
        if ":" not in args.disk:
            disk_raw = f"{storage}:{args.disk}"
        else:
            disk_raw = args.disk
        data["scsi0"] = disk_raw.replace("=", "%3D").replace(":", "%3A").replace(",", "%2C")
    elif args.import_from:
        target_storage = args.storage or "rbd_ssd"
        import_raw = f"{target_storage}:0,import-from={args.import_from}"
        data["scsi0"] = import_raw.replace("=", "%3D").replace(":", "%3A").replace(",", "%2C")

    # Cloud-init
    if args.citype:
        data["citype"] = args.citype
    if args.ciuser:
        data["ciuser"] = args.ciuser
    if args.cipassword:
        data["cipassword"] = args.cipassword
    if args.nameserver:
        data["nameserver"] = args.nameserver
    if args.searchdomain:
        data["searchdomain"] = args.searchdomain
    if args.cicustom:
        data["cicustom"] = args.cicustom
    if args.sshkeys:
        # sshkeys can be a file path or inline content
        try:
            with open(args.sshkeys) as f:
                data["sshkeys"] = f.read().strip().replace("\n", "%0A").replace("\r", "%0D").replace("=", "%3D").replace(",", "%2C").replace(":", "%3A")
        except (OSError, FileNotFoundError):
            data["sshkeys"] = args.sshkeys.replace("\n", "%0A").replace("\r", "%0D").replace("=", "%3D").replace(",", "%2C").replace(":", "%3A")

    # Cloud-init drive: add if cloud-init params present and no cdrom set
    cloudinit_keys = {"citype", "ciuser", "cipassword", "sshkeys", "nameserver", "searchdomain", "cicustom"}
    has_cloudinit = any(k in data for k in cloudinit_keys)
    has_cdrom = "ide2" in data and "cloudinit" not in str(data.get("ide2", ""))
    if has_cloudinit and not has_cdrom:
        data["ide2"] = "local:cloudinit,media=cdrom"

    # Validate required fields
    if "memory" not in data:
        return {"error": "--memory is required (or set 'memory:' in the spec file)"}
    if "cores" not in data:
        data["cores"] = "1"  # default when neither CLI nor file provides it

    # Pre-encode values from file_spec that might contain special chars (:, =, ,)
    # File spec values are passed as-is; only CLI values go through manual encoding.
    # For file_spec, we assume the user writes native Proxmox values which need encoding.
    _encode_spec_values_for_api(data)

    # Build form-encoded body
    from urllib.parse import urlencode
    body = urlencode(data, safe="%")

    result = client.request("POST", f"/nodes/{node}/qemu", content=body)
    return result if isinstance(result, dict) else {"data": result}


def _encode_spec_values_for_api(data: dict[str, Any]) -> None:
    """Pre-encode values that contain special characters for the Proxmox API.

    The Proxmox API's form parser treats ``:``, ``,``, and ``=`` as delimiters
    within values. We URL-encode these characters to prevent parsing issues.
    Only encodes values that aren't already pre-encoded (don't contain %XX sequences).
    """
    for key in list(data):
        value = str(data[key])
        # Skip if already pre-encoded (contains %XX patterns)
        if "%" in value:
            continue
        # Only encode values that actually contain special chars
        if any(c in value for c in (":", ",", "=")):
            data[key] = value.replace("=", "%3D").replace(":", "%3A").replace(",", "%2C")
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


# ---------------------------------------------------------------------------
# VM guest agent handlers
# ---------------------------------------------------------------------------

def _vm_clone(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    """Clone a VM to a new VMID.

    Wraps ``POST /nodes/{node}/qemu/{vmid}/clone``.
    """
    node = _resolve_node(client, args.node, args.vmid)
    if not node:
        return {"error": f"Source VM {args.vmid} not found"}

    data: dict[str, Any] = {"newid": args.newid}
    if args.name:
        data["name"] = args.name
    if args.target_node:
        data["target"] = args.target_node
    if args.target_storage:
        data["storage"] = args.target_storage
    if args.full is not None:
        data["full"] = args.full
    if args.description:
        data["description"] = args.description
    if args.pool:
        data["pool"] = args.pool

    result = client.post(f"/nodes/{node}/qemu/{args.vmid}/clone", data=data)
    if isinstance(result, dict) and "data" not in result and "error" not in result:
        result = {"data": result, "source_vmid": args.vmid, "new_vmid": args.newid, "_node": node}
    return result


def _vm_agent_interfaces(args: argparse.Namespace, client: ProxmoxClient) -> dict | list:
    """Retrieve network interfaces via QEMU guest agent.

    Requires qemu-guest-agent installed in the VM and agent enabled in VM options.
    """
    node = _resolve_node(client, args.node, args.vmid)
    if not node:
        return {"error": f"VM {args.vmid} not found"}
    result = client.get(f"/nodes/{node}/qemu/{args.vmid}/agent/network-get-interfaces")
    # The result is a list of interfaces, each with 'name', 'ip-addresses', etc.
    if isinstance(result, list):
        for iface in result:
            if isinstance(iface, dict):
                iface["_node"] = node
                iface["_vmid"] = args.vmid
    return result


# ---------------------------------------------------------------------------
# VM cloud-init handlers
# ---------------------------------------------------------------------------

def _vm_cloudinit_generate(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    """Regenerate the cloud-init ISO from the VM's current cloud-init config.

    In Proxmox VE 9, cloud-init ISOs are regenerated automatically when
    config changes. This triggers regeneration by re-setting the citype.
    """
    node = _resolve_node(client, args.node, args.vmid)
    if not node:
        return {"error": f"VM {args.vmid} not found"}
    # Proxmox VE 9 regenerates cloud-init on config change.
    # Re-submit the current citype to trigger regeneration.
    config = client.get(f"/nodes/{node}/qemu/{args.vmid}/config")
    if not isinstance(config, dict):
        return {"error": f"Could not read config for VM {args.vmid}"}
    citype = config.get("citype")
    if not citype:
        return {"error": f"VM {args.vmid} has no cloud-init configured (missing citype)"}
    result = client.put(
        f"/nodes/{node}/qemu/{args.vmid}/config",
        data={"citype": citype},
    )
    return {"data": result} if isinstance(result, (str, type(None))) or not isinstance(result, dict) else result


# ---------------------------------------------------------------------------
# VM snapshot handlers
# ---------------------------------------------------------------------------

def _vm_snapshot_list(args: argparse.Namespace, client: ProxmoxClient) -> dict | list:
    node = _resolve_node(client, args.node, args.vmid)
    if not node:
        return {"error": f"VM {args.vmid} not found"}
    result = client.get(f"/nodes/{node}/qemu/{args.vmid}/snapshot")
    # Add _node for consistency
    if isinstance(result, list):
        for snap in result:
            if isinstance(snap, dict):
                snap["_node"] = node
                snap["_vmid"] = args.vmid
    return result


def _vm_snapshot_create(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    node = _resolve_node(client, args.node, args.vmid)
    if not node:
        return {"error": f"VM {args.vmid} not found"}
    data: dict = {"snapname": args.snapname}
    if args.description:
        data["description"] = args.description
    if args.vmstate:
        data["vmstate"] = args.vmstate
    result = client.post(f"/nodes/{node}/qemu/{args.vmid}/snapshot", data=data)
    return result if isinstance(result, dict) else {"data": result}


def _vm_snapshot_show(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    node = _resolve_node(client, args.node, args.vmid)
    if not node:
        return {"error": f"VM {args.vmid} not found"}
    result = client.get(f"/nodes/{node}/qemu/{args.vmid}/snapshot/{args.snapname}")
    if isinstance(result, dict):
        result["_node"] = node
        result["_vmid"] = args.vmid
    return result


def _vm_snapshot_rollback(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    node = _resolve_node(client, args.node, args.vmid)
    if not node:
        return {"error": f"VM {args.vmid} not found"}
    data: dict = {}
    if args.start:
        data["start"] = args.start
    result = client.post(
        f"/nodes/{node}/qemu/{args.vmid}/snapshot/{args.snapname}/rollback",
        data=data or None,
    )
    return result if isinstance(result, dict) else {"data": result}


def _vm_snapshot_delete(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    node = _resolve_node(client, args.node, args.vmid)
    if not node:
        return {"error": f"VM {args.vmid} not found"}
    params: dict = {}
    if args.force:
        params["force"] = args.force
    result = client.delete(
        f"/nodes/{node}/qemu/{args.vmid}/snapshot/{args.snapname}",
        params=params or None,
    )
    return result if isinstance(result, dict) else {"data": result}


# ---------------------------------------------------------------------------
# VM firewall handlers
# ---------------------------------------------------------------------------

def _vm_fw_options(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    node = _resolve_node(client, args.node, args.vmid)
    if not node:
        return {"error": f"VM {args.vmid} not found"}
    return client.get(f"/nodes/{node}/qemu/{args.vmid}/firewall/options")


def _vm_fw_enable(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    node = _resolve_node(client, args.node, args.vmid)
    if not node:
        return {"error": f"VM {args.vmid} not found"}
    return client.put(f"/nodes/{node}/qemu/{args.vmid}/firewall/options", data={"enable": 1})


def _vm_fw_disable(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    node = _resolve_node(client, args.node, args.vmid)
    if not node:
        return {"error": f"VM {args.vmid} not found"}
    return client.put(f"/nodes/{node}/qemu/{args.vmid}/firewall/options", data={"enable": 0})


def _vm_fw_policy(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    node = _resolve_node(client, args.node, args.vmid)
    if not node:
        return {"error": f"VM {args.vmid} not found"}
    data: dict = {}
    if args.in_policy:
        data["policy_in"] = args.in_policy
    if args.out_policy:
        data["policy_out"] = args.out_policy
    if not data:
        return {"error": "No policy specified. Use --in-policy or --out-policy"}
    return client.put(f"/nodes/{node}/qemu/{args.vmid}/firewall/options", data=data)


def _vm_fw_rules(args: argparse.Namespace, client: ProxmoxClient) -> dict | list:
    node = _resolve_node(client, args.node, args.vmid)
    if not node:
        return {"error": f"VM {args.vmid} not found"}
    return client.get(f"/nodes/{node}/qemu/{args.vmid}/firewall/rules")


def _vm_fw_rule_add(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    node = _resolve_node(client, args.node, args.vmid)
    if not node:
        return {"error": f"VM {args.vmid} not found"}
    return client.post(f"/nodes/{node}/qemu/{args.vmid}/firewall/rules",
                       data=build_rule_data(args))


def _vm_fw_rule_show(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    node = _resolve_node(client, args.node, args.vmid)
    if not node:
        return {"error": f"VM {args.vmid} not found"}
    return client.get(f"/nodes/{node}/qemu/{args.vmid}/firewall/rules/{args.pos}")


def _vm_fw_rule_upd(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    node = _resolve_node(client, args.node, args.vmid)
    if not node:
        return {"error": f"VM {args.vmid} not found"}
    data = {k: v for k, v in build_rule_data(args).items() if v is not None and v != 0}
    return client.put(f"/nodes/{node}/qemu/{args.vmid}/firewall/rules/{args.pos}", data=data)


def _vm_fw_rule_del(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    node = _resolve_node(client, args.node, args.vmid)
    if not node:
        return {"error": f"VM {args.vmid} not found"}
    return client.delete(f"/nodes/{node}/qemu/{args.vmid}/firewall/rules/{args.pos}")


def _vm_fw_refs(args: argparse.Namespace, client: ProxmoxClient) -> dict | list:
    node = _resolve_node(client, args.node, args.vmid)
    if not node:
        return {"error": f"VM {args.vmid} not found"}
    params: dict | None = {"type": args.type} if args.type else None
    return client.get(f"/nodes/{node}/qemu/{args.vmid}/firewall/refs", params=params)
