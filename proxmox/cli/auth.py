"""`proxmox auth` subcommand — authentication status and permission setup."""

from __future__ import annotations

import argparse

from proxmox.client.client import ProxmoxClient
from proxmox.config.config import ConfigLoader

# Recommended roles for proxcli (see docs/api-permissions.md)
PROXCLI_ROLES: dict[str, str] = {
    "proxcli-sys": "Sys.Audit,Sys.Modify",
    "proxcli-storage": "Datastore.Allocate,Datastore.AllocateSpace,"
                       "Datastore.AllocateTemplate,Datastore.Audit",
    "proxcli-vm": "VM.Allocate,VM.Audit,VM.Backup,VM.Clone,"
                  "VM.Config.CDROM,VM.Config.Cloudinit,VM.Config.CPU,"
                  "VM.Config.Disk,VM.Config.HWType,VM.Config.Memory,"
                  "VM.Config.Network,VM.Config.Options,VM.Console,"
                  "VM.Migrate,VM.Monitor,VM.PowerMgmt,VM.Snapshot,"
                  "VM.Snapshot.Rollback,Pool.Allocate,Pool.Audit",
    "proxcli-node": "VM.GuestAgent.Audit,VM.GuestAgent.FileRead",
}

# ACL paths for each role
PROXCLI_ACLS: list[tuple[str, str]] = [
    ("/", "proxcli-sys"),
    ("/storage", "proxcli-storage"),
    ("/vms", "proxcli-vm"),
    ("/nodes", "proxcli-node"),
]


def register_auth_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the `proxmox auth` subcommand tree."""
    auth_parser = subparsers.add_parser("auth", help="Authentication and permissions")
    auth_sub = auth_parser.add_subparsers(dest="action", title="actions", required=True)

    # --- auth status ---
    status = auth_sub.add_parser("status", help="Show current authentication status")
    status.set_defaults(func=_auth_status)

    # --- auth setup ---
    setup = auth_sub.add_parser("setup", help="Create recommended roles and ACLs for proxcli")
    setup.set_defaults(func=_auth_setup)


def _auth_status(args: argparse.Namespace, client: ProxmoxClient | None = None) -> dict:
    """Display current authentication status."""
    loader = ConfigLoader()
    creds = loader.load_or_none()
    if creds is None:
        return {"status": "not authenticated"}

    found_path = loader.find_file()
    return {
        "status": "authenticated",
        "url": creds.url,
        "username": creds.username,
        "auth_method": creds.auth_method.value,
        "verify_tls": creds.verify_tls,
        "config_file": str(found_path) if found_path else "unknown",
    }


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
        client.post("/access/roles", data={"roleid": role_name, "privs": privs})
        created_roles.append(role_name)

    # 2. Create ACLs
    # We need the username from config to assign ACLs
    loader = ConfigLoader()
    creds = loader.load()
    ug = creds.username

    for path, role in PROXCLI_ACLS:
        existing_acls = client.get("/access/acl")
        # Check if this exact ACL already exists
        already = any(
            a.get("path") == path
            and a.get("roleid") == role
            and a.get("ugid") == ug
            for a in existing_acls
        )
        if already:
            skipped_acls.append(f"{path} → {role} ({ug})")
            continue
        client.put(
            "/access/acl",
            data={"path": path, "roles": role, "users": ug},
        )
        created_acls.append(f"{path} → {role} ({ug})")

    return {
        "created_roles": created_roles,
        "skipped_roles": skipped_roles,
        "created_acls": created_acls,
        "skipped_acls": skipped_acls,
    }
