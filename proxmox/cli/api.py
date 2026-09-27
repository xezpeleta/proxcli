"""`proxmox api` subcommand — raw authenticated API calls."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from proxmox.client.client import ProxmoxClient

# Curated catalog of common Proxmox VE API endpoints, grouped by resource.
# Used by `proxmox api --list-endpoints` to give agents (and humans) a
# browsable map of the API surface, including the node-vs-cluster path
# convention that is otherwise learned only by trial and error.
#
# Each entry: (method, path_template, description). Path parameters in
# {braces} are substituted with real values at call time.
API_ENDPOINTS: list[tuple[str, str, str, str]] = [
    # --- Cluster-wide (no node in path) ---
    ("Cluster", "GET", "/cluster/status", "Cluster quorum status and node membership"),
    ("Cluster", "GET", "/cluster/log", "Cluster-wide task log (last 100)"),
    ("Cluster", "GET", "/cluster/options", "Cluster-wide configuration options"),
    ("Cluster", "GET", "/cluster/resources", "All resources; filter with ?type=vm|storage|node|sdn|ha"),
    ("Cluster", "GET", "/cluster/ha/status/current", "HA manager status"),
    ("Cluster", "GET", "/cluster/ha/resources", "HA-managed resources"),
    ("Cluster", "GET", "/cluster/ha/groups", "HA groups"),
    ("Cluster", "GET", "/cluster/sdn", "SDN overview"),
    ("Cluster", "GET", "/cluster/sdn/zones", "SDN zones"),
    ("Cluster", "GET", "/cluster/sdn/vnets", "SDN virtual networks"),
    ("Cluster", "GET", "/cluster/firewall/options", "Cluster firewall options"),
    ("Cluster", "GET", "/cluster/firewall/rules", "Cluster firewall rules"),
    ("Cluster", "GET", "/cluster/ceph/status", "Ceph cluster health (cluster-level)"),
    ("Cluster", "GET", "/cluster/backup", "Scheduled datacenter backup jobs"),
    ("Cluster", "GET", "/cluster/notifications", "Notification targets & matchers"),

    # --- Per-node (/nodes/{node}/...) ---
    ("Nodes", "GET", "/nodes", "List all nodes in the cluster"),
    ("Nodes", "GET", "/nodes/{node}/status", "Node status (CPU, memory, uptime, load)"),
    ("Nodes", "GET", "/nodes/{node}/disks/list", "Physical disk inventory (health, wearout, osdid)"),
    ("Nodes", "GET", "/nodes/{node}/ceph/osd", "Ceph OSD CRUSH tree with utilization (cluster-wide view)"),
    ("Nodes", "GET", "/nodes/{node}/ceph/pool", "Ceph pools with capacity/PGs (cluster-wide view)"),
    ("Nodes", "GET", "/nodes/{node}/ceph/status", "Ceph status (per-node manager view)"),
    ("Nodes", "GET", "/nodes/{node}/network", "Network interfaces on a node"),
    ("Nodes", "GET", "/nodes/{node}/services", "systemd services on a node"),
    ("Nodes", "GET", "/nodes/{node}/tasks", "Tasks running/finished on a node"),
    ("Nodes", "GET", "/nodes/{node}/qemu", "VMs on a node"),
    ("Nodes", "GET", "/nodes/{node}/lxc", "Containers on a node"),
    ("Nodes", "GET", "/nodes/{node}/storage", "Storage registered on a node"),
    ("Nodes", "GET", "/nodes/{node}/subscription", "Subscription status"),
    ("Nodes", "GET", "/nodes/{node}/apt/update", "Available package updates"),

    # --- VMs (QEMU) ---
    ("VMs", "GET", "/nodes/{node}/qemu", "List VMs on a node"),
    ("VMs", "GET", "/nodes/{node}/qemu/{vmid}/status/current", "VM current status"),
    ("VMs", "GET", "/nodes/{node}/qemu/{vmid}/config", "VM configuration"),
    ("VMs", "POST", "/nodes/{node}/qemu", "Create a VM"),
    ("VMs", "POST", "/nodes/{node}/qemu/{vmid}/status/start", "Start a VM"),
    ("VMs", "POST", "/nodes/{node}/qemu/{vmid}/status/stop", "Stop (hard power-off) a VM"),
    ("VMs", "POST", "/nodes/{node}/qemu/{vmid}/status/reboot", "Reboot a VM"),
    ("VMs", "POST", "/nodes/{node}/qemu/{vmid}/snapshot", "Create a VM snapshot"),
    ("VMs", "GET", "/nodes/{node}/qemu/{vmid}/snapshot", "List VM snapshots"),
    ("VMs", "POST", "/nodes/{node}/qemu/{vmid}/clone", "Clone a VM"),
    ("VMs", "POST", "/nodes/{node}/qemu/{vmid}/migrate", "Migrate a VM"),
    ("VMs", "GET", "/nodes/{node}/qemu/{vmid}/agent/network-get-interfaces", "VM guest IPs (needs qemu-guest-agent)"),

    # --- Containers (LXC) ---
    ("Containers", "GET", "/nodes/{node}/lxc", "List containers on a node"),
    ("Containers", "GET", "/nodes/{node}/lxc/{vmid}/status/current", "Container status"),
    ("Containers", "GET", "/nodes/{node}/lxc/{vmid}/config", "Container configuration"),
    ("Containers", "POST", "/nodes/{node}/lxc", "Create a container"),
    ("Containers", "GET", "/nodes/{node}/lxc/{vmid}/interfaces", "Container network interfaces"),

    # --- Storage ---
    ("Storage", "GET", "/storage", "List all storage (cluster-wide)"),
    ("Storage", "GET", "/storage/{storage}", "Storage configuration"),
    ("Storage", "GET", "/nodes/{node}/storage/{storage}/content", "Volumes/images in a storage"),
    ("Storage", "POST", "/nodes/{node}/storage/{storage}/upload", "Upload an ISO/image to storage"),

    # --- Access control ---
    ("Access", "GET", "/access/users", "List users"),
    ("Access", "GET", "/access/roles", "List roles"),
    ("Access", "GET", "/access/acl", "List ACLs"),
    ("Access", "GET", "/access/domains", "Auth domains (PAM, LDAP, AD, ...)"),

    # --- Tasks ---
    ("Tasks", "GET", "/nodes/{node}/tasks", "List tasks on a node"),
    ("Tasks", "GET", "/nodes/{node}/tasks/{upid}/status", "Task status (running/stopped + exit code)"),
    ("Tasks", "GET", "/nodes/{node}/tasks/{upid}/log", "Task log lines"),

    # --- Pools & backup ---
    ("Pools", "GET", "/pools", "List resource pools"),
    ("Backup", "POST", "/nodes/{node}/vzdump", "Run a backup (vzdump) of a guest"),
    ("Backup", "GET", "/cluster/backup/default", "Default vzdump settings"),
]


def _endpoints_as_records() -> list[dict[str, str]]:
    """Return the endpoint catalog as a flat list of dicts (for output)."""
    return [
        {"category": cat, "method": method, "path": path, "description": desc}
        for cat, method, path, desc in API_ENDPOINTS
    ]


_API_EPILOG = """\
examples:
  # Cluster-wide resources (no node in the path)
  proxmox api GET /cluster/resources
  proxmox api GET /cluster/resources?type=vm

  # Per-node status (substitute a real node name)
  proxmox api GET /nodes/pve01/status

  # Mutating call with a JSON body
  proxmox api PUT /nodes/pve01/qemu/100/config -d '{"memory": 4096}'
  echo '{"memory": 4096}' | proxmox api PUT /nodes/pve01/qemu/100/config

  # Browse known endpoint patterns
  proxmox api --list-endpoints
  proxmox api --list-endpoints --output table

path conventions:
  - Cluster-wide:  /cluster/...        (e.g. /cluster/status, /cluster/sdn/zones)
  - Per-node:      /nodes/{node}/...   (e.g. /nodes/pve01/qemu, /nodes/pve01/ceph/osd)
  - {node}, {vmid}, {storage} are path parameters — substitute real values.
  - The /api2/json prefix is added automatically (strip it if you paste a full URL).
"""


def register_api_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the `proxmox api` subcommand."""
    api_parser = subparsers.add_parser(
        "api",
        help="Make a raw authenticated API call (for endpoints not yet covered by subcommands)",
        description=(
            "Make a raw authenticated API call to any Proxmox VE endpoint. "
            "Use --list-endpoints to browse known endpoint patterns."
        ),
        epilog=_API_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    api_parser.add_argument(
        "--list-endpoints",
        action="store_true",
        help="Print known API endpoint patterns grouped by resource, then exit",
    )
    api_parser.add_argument(
        "method",
        nargs="?",
        choices=["GET", "POST", "PUT", "DELETE"],
        help="HTTP method (required unless --list-endpoints)",
    )
    api_parser.add_argument(
        "path",
        nargs="?",
        help="API path (e.g. /nodes/pve01/qemu/100/config). The /api2/json prefix is added automatically.",
    )
    api_parser.add_argument(
        "--data", "-d", default=None,
        help="Request body as JSON string (for POST/PUT)",
    )
    api_parser.add_argument(
        "--data-file", "-f", default=None, dest="data_file",
        help="Read request body from a JSON file (for POST/PUT)",
    )
    api_parser.set_defaults(func=_api_call)


def _api_call(args: argparse.Namespace, client: ProxmoxClient) -> dict[str, Any] | list[Any]:
    """Execute a raw API call, or print the endpoint catalog.

    Wraps ``ProxmoxClient.request(method, path, ...)``. When
    ``--list-endpoints`` is set, returns the curated endpoint catalog instead
    of making a request.
    """
    if getattr(args, "list_endpoints", False):
        return _endpoints_as_records()

    if not args.method:
        return {
            "error": "method is required (GET/POST/PUT/DELETE), "
                     "or use --list-endpoints to browse known paths"
        }
    if not args.path:
        return {"error": "path is required (e.g. /nodes/pve01/status)"}

    # Normalise path: strip leading slash, strip /api2/json prefix if present
    path = args.path.lstrip("/")
    if path.startswith("api2/json/"):
        path = path[len("api2/json/"):]

    # Parse body
    body: dict[str, Any] | None = None
    if args.data_file:
        try:
            with open(args.data_file) as f:
                body = json.load(f)
        except (OSError, FileNotFoundError) as e:
            return {"error": f"Cannot read data file: {e}"}
        except json.JSONDecodeError as e:
            return {"error": f"Invalid JSON in data file: {e}"}
    elif args.data:
        try:
            body = json.loads(args.data)
        except json.JSONDecodeError as e:
            return {"error": f"Invalid JSON in --data: {e}. Use valid JSON, e.g. '{{\"key\": \"value\"}}'"}

    # Read additional body from stdin if piped (and no --data/--data-file)
    if body is None and not sys.stdin.isatty():
        stdin_data = sys.stdin.read().strip()
        if stdin_data:
            try:
                body = json.loads(stdin_data)
            except json.JSONDecodeError as e:
                return {"error": f"Invalid JSON from stdin: {e}"}

    result = client.request(args.method, f"/{path}", data=body)
    return result if isinstance(result, (dict, list)) else {"data": result}
