"""`proxmox auth` subcommand — authentication status and permission setup."""

from __future__ import annotations

import argparse
from urllib.parse import urlencode

from proxmox.client.client import ProxmoxClient
from proxmox.client.exceptions import ProxmoxAPIError
from proxmox.config.config import ConfigLoader

# Recommended roles for proxcli (see docs/api-permissions.md)
PROXCLI_ROLES: dict[str, str] = {
    "proxcli-sys": "Sys.Audit,Sys.Modify,Pool.Allocate,Pool.Audit",
    "proxcli-storage": "Datastore.Allocate,Datastore.AllocateSpace,"
                       "Datastore.AllocateTemplate,Datastore.Audit",
    "proxcli-vm": "VM.Allocate,VM.Audit,VM.Backup,VM.Clone,"
                  "VM.Config.CDROM,VM.Config.Cloudinit,VM.Config.CPU,"
                  "VM.Config.Disk,VM.Config.HWType,VM.Config.Memory,"
                  "VM.Config.Network,VM.Config.Options,VM.Console,"
                  "VM.GuestAgent.Audit,VM.GuestAgent.FileRead,"
                  "VM.Migrate,VM.PowerMgmt,VM.Snapshot,"
                  "VM.Snapshot.Rollback",
    "proxcli-node": "VM.GuestAgent.Audit,VM.GuestAgent.FileRead",
}

# ACL paths for each role
PROXCLI_ACLS: list[tuple[str, str]] = [
    ("/", "proxcli-sys"),
    ("/storage", "proxcli-storage"),
    ("/vms", "proxcli-vm"),
    ("/nodes", "proxcli-node"),
]


# Permission checks: (label, method, path, privilege_needed)
# The handler does a dry-run-like GET/POST to check if 403 is returned.
PERMISSION_CHECKS: list[tuple[str, str, str, str]] = [
    # ── read-only / system ──
    ("Cluster status",          "GET",  "/cluster/status",      "Sys.Audit"),
    ("Node list",               "GET",  "/nodes",               "Sys.Audit"),
    ("Task list",               "GET",  "/cluster/tasks",       "Sys.Audit"),
    ("Cluster log",             "GET",  "/cluster/log",         "Sys.Audit"),
    ("Ceph status",             "GET",  "/cluster/ceph/status", "Sys.Audit"),
    ("Cluster options",         "GET",  "/cluster/options",     "Sys.Audit"),

    # ── storage ──
    ("Storage list",            "GET",  "/storage",             "Datastore.Audit"),
    ("Storage upload",          "POST", "/nodes/{node}/storage/{storage}/upload",
     "Datastore.AllocateTemplate"),
    ("Storage status",          "GET",  "/nodes/{node}/storage/{storage}/status",
     "Datastore.Audit"),

    # ── VMs (read) ──
    ("VM list",                 "GET",  "/cluster/resources",   "VM.Audit"),
    ("VM config",               "GET",  "/nodes/{node}/qemu/{vmid}/config",
     "VM.Audit"),
    ("VM status",               "GET",  "/nodes/{node}/qemu/{vmid}/status/current",
     "VM.Audit"),

    # ── VMs (lifecycle) ──
    ("VM create (nextid)",      "GET",  "/cluster/nextid",      "VM.Allocate"),
    ("VM create (save)",        "POST", "/nodes/{node}/qemu",   "VM.Allocate"),
    ("VM start",                "POST", "/nodes/{node}/qemu/{vmid}/status/start",
     "VM.PowerMgmt"),
    ("VM stop",                 "POST", "/nodes/{node}/qemu/{vmid}/status/stop",
     "VM.PowerMgmt"),
    ("VM delete",               "DELETE", "/nodes/{node}/qemu/{vmid}", "VM.Allocate"),

    # ── VMs (config) ──
    ("VM set memory/cores",     "PUT",  "/nodes/{node}/qemu/{vmid}/config",
     "VM.Config.Memory"),
    ("VM set network",          "PUT",  "/nodes/{node}/qemu/{vmid}/config",
     "VM.Config.Network"),
    ("VM set disk",             "PUT",  "/nodes/{node}/qemu/{vmid}/config",
     "VM.Config.Disk"),
    ("VM set cloud-init",       "PUT",  "/nodes/{node}/qemu/{vmid}/config",
     "VM.Config.Cloudinit"),
    ("VM set CDROM",            "PUT",  "/nodes/{node}/qemu/{vmid}/config",
     "VM.Config.CDROM"),
    ("VM set options",          "PUT",  "/nodes/{node}/qemu/{vmid}/config",
     "VM.Config.Options"),

    # ── VMs (snapshots) ──
    ("VM snapshot list",        "GET",  "/nodes/{node}/qemu/{vmid}/snapshot",
     "VM.Snapshot"),
    ("VM snapshot create",      "POST", "/nodes/{node}/qemu/{vmid}/snapshot",
     "VM.Snapshot"),
    ("VM snapshot rollback",    "POST", "/nodes/{node}/qemu/{vmid}/snapshot/{snapname}/rollback",
     "VM.Snapshot.Rollback"),

    # ── VMs (backup/clone/migrate) ──
    ("VM backup",               "POST", "/nodes/{node}/vzdump",  "VM.Backup"),
    ("VM clone",                "POST", "/nodes/{node}/qemu/{vmid}/clone",
     "VM.Clone"),
    ("VM migrate",              "POST", "/nodes/{node}/qemu/{vmid}/migrate",
     "VM.Migrate"),

    # ── QEMU guest agent ──
    ("VM guest agent",          "GET",  "/nodes/{node}/qemu/{vmid}/agent/network-get-interfaces",
     "VM.GuestAgent.Audit"),

    # ── containers ──
    ("Container list",          "GET",  "/nodes/{node}/lxc",    "VM.Audit"),
    ("Container start",         "POST", "/nodes/{node}/lxc/{vmid}/status/start",
     "VM.PowerMgmt"),

    # ── firewall ──
    ("Cluster firewall rules",  "GET",  "/cluster/firewall/rules",
     "Sys.Modify"),
    ("VM firewall rules",       "GET",  "/nodes/{node}/qemu/{vmid}/firewall/rules",
     "VM.Allocate"),

    # ── pools ──
    ("Pool list",               "GET",  "/pools",               "Pool.Audit"),
    ("Pool create",             "POST", "/pools",               "Pool.Allocate"),

    # ── ACL / users / roles (admin-only) ──
    ("User list",               "GET",  "/access/users",        "Permissions.Modify"),
    ("Role list",               "GET",  "/access/roles",        "Permissions.Modify"),
    ("ACL list",                "GET",  "/access/acl",          "Permissions.Modify"),
]


def _safe_encode(data: dict[str, str]) -> str:
    """URL-encode dict as form data, preserving literal commas in values.

    Proxmox expects literal commas in ``privs`` values, but httpx's
    default form-encoding converts them to ``%2C``.
    """
    return urlencode(data, safe=",")


def register_auth_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the `proxmox auth` subcommand tree."""
    auth_parser = subparsers.add_parser("auth", help="Authentication and permissions")
    auth_sub = auth_parser.add_subparsers(dest="action", title="actions", required=True)

    # --- auth status ---
    status = auth_sub.add_parser("status", help="Show current authentication status")
    status.add_argument("--permissions", "-p", action="store_true",
                        help="Also show effective permissions of the current token")
    status.set_defaults(func=_auth_status)

    # --- auth setup ---
    setup = auth_sub.add_parser("setup", help="Create recommended roles and ACLs for proxcli")
    setup.set_defaults(func=_auth_setup)

    # --- auth check ---
    check = auth_sub.add_parser("check", help="Test each permission endpoint live")
    check.set_defaults(func=_auth_check, output_format="table")


def _auth_status(args: argparse.Namespace, client: ProxmoxClient | None = None) -> dict:
    """Display current authentication status."""
    loader = ConfigLoader()
    creds = loader.load_or_none()
    if creds is None:
        return {"status": "not authenticated"}

    found_path = loader.find_file()
    result: dict = {
        "status": "authenticated",
        "url": creds.url,
        "username": creds.username,
        "auth_method": creds.auth_method.value,
        "verify_tls": creds.verify_tls,
        "config_file": str(found_path) if found_path else "unknown",
    }

    if client is not None and args.permissions:
        perms = client.get("/access/permissions")
        result["permissions"] = perms

    return result


def _auth_setup(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    """Create the recommended proxcli roles and ACLs."""
    created_roles: list[str] = []
    skipped_roles: list[str] = []
    created_acls: list[str] = []
    skipped_acls: list[str] = []

    # 1. Create roles
    for role_name, privs in PROXCLI_ROLES.items():
        existing = client.get("/access/roles")
        if any(r.get("roleid") == role_name for r in existing):
            skipped_roles.append(role_name)
            continue
        content = _safe_encode({"roleid": role_name, "privs": privs})
        client.request("POST", "/access/roles", content=content)
        created_roles.append(role_name)

    # 2. Create ACLs for the token using 'tokens' parameter (plural —
    #    the API docs say 'tokenid' but the actual HTTP param is 'tokens')
    loader = ConfigLoader()
    creds = loader.load()
    token_ug = f"{creds.username}!{creds.api_token_id}" if creds.api_token_id else creds.username

    for path, role in PROXCLI_ACLS:
        existing_acls = client.get("/access/acl")
        already = any(
            a.get("path") == path
            and a.get("roleid") == role
            and a.get("ugid") == token_ug
            and a.get("type") == "token"
            for a in existing_acls
        )
        if already:
            skipped_acls.append(f"{path} → {role} ({token_ug})")
            continue
        content = _safe_encode({"path": path, "roles": role, "tokens": token_ug})
        client.request("PUT", "/access/acl", content=content)
        created_acls.append(f"{path} → {role} ({token_ug})")


def _auth_check(args: argparse.Namespace, client: ProxmoxClient) -> None:
    """Test each proxcli endpoint and report permission status."""
    # Rich for colored output
    from rich.console import Console
    from rich.text import Text

    console = Console(highlight=False, force_terminal=True, width=120)

    # Resolve a real node name for paths that need it
    nodes = client.get("/nodes")
    node = nodes[0]["node"] if nodes else "pve"

    total = len(PERMISSION_CHECKS)
    passed = 0
    failed = 0

    for idx, (label, method, path, needed_priv) in enumerate(PERMISSION_CHECKS, 1):
        real_path = path.replace("{node}", node).replace("{vmid}", "99999") \
                         .replace("{storage}", "local").replace("{snapname}", "test")

        try:
            if method in ("GET", "DELETE"):
                client.request(method, real_path)
            else:
                client.request(method, real_path, data={"dry": "1"})
            status = "PASS"
            passed += 1
        except ProxmoxAPIError as exc:
            if exc.status_code == 403:
                status = "FAIL"
                failed += 1
            else:
                status = "PASS"
                passed += 1

        # Print inline with colors
        color = "green" if status == "PASS" else "red"
        status_text = Text(status, style=f"bold {color}")
        console.print(
            f"[{idx}/{total}]",
            status_text,
            f"{needed_priv:<28s}",
            label,
        )

    # Summary
    console.print()
    console.print(f"Passed: [bold green]{passed}[/], Failed: [bold red]{failed}[/], Total: {total}")
    if failed == 0:
        console.print("[bold green]✓ All permissions configured correctly!")
    else:
        console.print("[bold yellow]⚠ Some permissions are missing. Run 'proxmox auth setup' or check docs/api-permissions.md")

    # ── Check for stray/leftover roles on the token ──
    loader = ConfigLoader()
    creds = loader.load()
    token_ug = f"{creds.username}!{creds.api_token_id}" if creds.api_token_id else creds.username

    acls = client.get("/access/acl")
    token_acls = [a for a in acls if a.get("ugid") == token_ug and a.get("type") == "token"]
    expected_roles = set("proxcli-" + suffix for suffix in ["sys", "storage", "vm", "node"])
    stray = [a for a in token_acls if a.get("roleid") not in expected_roles]

    if stray:
        console.print()
        console.print(
            f"[bold yellow]⚠ The token [bold]{token_ug}[/] has extra roles[/] "
            f"[dim](not needed after initial setup)[/]:"
        )
        for a in stray:
            console.print(f"     Path: [bold]{a['path']:<10s}[/]  Role: [bold red]{a['roleid']}[/]")
        console.print()
        console.print("   Remove them in Datacenter → Permissions → API Token Permissions.")
        console.print("   Keep only: [bold green]proxcli-sys, proxcli-storage, proxcli-vm, proxcli-node[/]")
        console.print()
        # Add note to summary
        console.print(
            f"[bold yellow]⚠ {len(stray)} stray role(s) — remove after verifying proxcli roles work.[/]"
        )
