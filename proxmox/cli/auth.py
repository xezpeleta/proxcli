"""`proxmox auth` subcommand — authentication status and permission setup."""

from __future__ import annotations

import argparse
import sys
from urllib.parse import urlencode

from rich.console import Console
from rich.prompt import Prompt

from proxmox.client.client import ProxmoxClient
from proxmox.client.exceptions import ConfigError, ProxmoxAPIError, ProxmoxError
from proxmox.config.config import ConfigLoader
from proxmox.config.models import AuthMethod
from proxmox.config.writer import ConfigWriter
from proxmox.ssh.runner import SetupResult, SshError, SshRunner, parse_setup_output
from proxmox.ssh.script import SetupSpec, generate_setup_script

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
    # SDN bridges/vnets are SDN-managed — attaching a VM NIC to one needs
    # SDN.Use on top of VM.Config.Network. SDN.Allocate (create/modify fabric)
    # is intentionally NOT included.
    "proxcli-network": "SDN.Audit,SDN.Use",
}

# ACL paths for each role
PROXCLI_ACLS: list[tuple[str, str]] = [
    ("/", "proxcli-sys"),
    ("/storage", "proxcli-storage"),
    ("/vms", "proxcli-vm"),
    ("/nodes", "proxcli-node"),
    ("/sdn", "proxcli-network"),
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

    # ── SDN (attach VM NIC to an SDN bridge/vnet) ──
    ("SDN overview",            "GET",  "/cluster/sdn",         "SDN.Audit"),
    ("SDN zones",               "GET",  "/cluster/sdn/zones",   "SDN.Audit"),

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


SETUP_EPILOG = """\
examples:
  # Interactive (recommended) — prompts for host, writes credentials.json:
  proxmox auth setup

  # Fully non-interactive over SSH with key auth:
  proxmox auth setup --via ssh --host pve1.lan --non-interactive

  # Non-interactive with a password (requires sshpass):
  proxmox auth setup --host pve1.lan --ssh-password-stdin --non-interactive < pw

  # Rotate an existing token's secret:
  proxmox auth setup --host pve1.lan --regenerate --force

  # Preview the script without running anything:
  proxmox auth setup --host pve1.lan --dry-run

  # Machine-readable result for agents/scripts:
  proxmox auth setup --host pve1.lan --non-interactive --json

  # Legacy: use an existing admin token over the REST API (roles + ACLs only):
  proxmox --url https://pve:8006 --api-token 'root@pam!admin=SECRET' \\
      auth setup --via api

what it does (ssh mode):
  1. SSH into <host> as <ssh-user> (key auth by default; password via sshpass).
  2. Run an idempotent bash script as root@pam that:
       - creates/syncs the proxcli-* roles,
       - creates the <pve-user>!<token-name> API token (capturing its secret), and
       - binds each role to the token on the right ACL path.
  3. Write the token to ~/.config/proxmox-cli/credentials.json (mode 0600),
     backing up any existing file to credentials.json.bak.

notes:
  - 'ssh' mode needs no existing credentials.json; 'api' mode does.
  - The token secret is shown ONCE at creation; capture --json or use --no-write.
"""


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
    setup = auth_sub.add_parser(
        "setup",
        help="Bootstrap proxcli roles, an API token, and ACLs",
        description=(
            "Create the recommended proxcli roles, an API token, and the ACLs "
            "that bind them — then write the resulting token to credentials.json."
        ),
        epilog=SETUP_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    setup.add_argument(
        "--via", choices=["ssh", "api"], default="ssh",
        help="Transport: 'ssh' (default) runs an idempotent script on a PVE node "
             "as root@pam and writes credentials.json; 'api' uses an existing "
             "admin token over the REST API (roles + ACLs only, legacy).",
    )
    # SSH transport
    setup.add_argument("--host", help="PVE node hostname/IP to SSH into (ssh mode; prompted if omitted).")
    setup.add_argument("--ssh-user", default="root", help="SSH login user (default: root).")
    setup.add_argument("--port", type=int, default=22, help="SSH port (default: 22).")
    setup.add_argument("-i", "--identity", help="SSH private key file.")
    setup.add_argument(
        "--ssh-password",
        help="SSH password (requires sshpass). Prefer key auth; use "
             "--ssh-password-stdin to read from stdin instead.",
    )
    setup.add_argument(
        "--ssh-password-stdin", action="store_true",
        help="Read the SSH password from stdin (requires sshpass).",
    )
    # Target PVE user / token
    setup.add_argument(
        "--pve-user", default="root@pam",
        help="Proxmox user the token is created for (default: root@pam).",
    )
    setup.add_argument(
        "--token-name", default="proxcli",
        help="API token ID to create (default: proxcli).",
    )
    setup.add_argument(
        "--api-url",
        help="Proxmox API URL written to credentials.json (default: "
             "https://<host>:8006).",
    )
    setup.add_argument(
        "--privsep", dest="privsep", action="store_true", default=True,
        help="Token uses separated privileges (default): effective perms = its "
             "ACLs only.",
    )
    setup.add_argument(
        "--no-privsep", dest="privsep", action="store_false",
        help="Token inherits the full privileges of the PVE user (less secure).",
    )
    setup.add_argument(
        "--regenerate", action="store_true",
        help="If the token already exists, rotate its secret (revokes the old one).",
    )
    # Output / behaviour
    setup.add_argument(
        "--non-interactive", action="store_true",
        help="Never prompt; fail if a required value is missing.",
    )
    setup.add_argument(
        "--force", action="store_true",
        help="Overwrite an existing credentials.json (a .json.bak backup is kept).",
    )
    setup.add_argument(
        "--no-write", action="store_true",
        help="Do not write credentials.json; print the token secret instead.",
    )
    setup.add_argument(
        "--dry-run", action="store_true", default=argparse.SUPPRESS,
        help="Print the generated script + ssh command without executing.",
    )
    setup.add_argument(
        "--json", action="store_true",
        help="Emit machine-readable JSON to stdout (for scripts/agents).",
    )
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


def _want_json(args: argparse.Namespace) -> bool:
    """True if the user asked for JSON output (via --json or global --output json)."""
    if getattr(args, "json", False):
        return True
    for i, a in enumerate(sys.argv):
        if a == "--output" and i + 1 < len(sys.argv) and sys.argv[i + 1] == "json":
            return True
        if a.startswith("--output=") and a.split("=", 1)[1] == "json":
            return True
    return False


def _auth_setup(args: argparse.Namespace, client: ProxmoxClient | None = None) -> dict | None:
    """Bootstrap proxcli roles, an API token, and ACLs.

    Dispatches on ``--via``: ``ssh`` (default) runs an idempotent script on a
    PVE node and writes credentials.json; ``api`` uses an existing admin token
    over the REST API (roles + ACLs only).
    """
    json_mode = _want_json(args)
    if getattr(args, "via", "ssh") == "api":
        return _auth_setup_api(args, client, json_mode)
    return _auth_setup_ssh(args, json_mode)


def _auth_setup_ssh(args: argparse.Namespace, json_mode: bool) -> dict | None:
    """SSH-based setup: create roles + token + ACLs on a node, write config."""
    console = Console(stderr=True, quiet=json_mode)

    pve_user = getattr(args, "pve_user", "root@pam") or "root@pam"
    token_name = getattr(args, "token_name", "proxcli") or "proxcli"
    privsep = bool(getattr(args, "privsep", True))
    regenerate = bool(getattr(args, "regenerate", False))
    dry_run = bool(getattr(args, "dry_run", False))

    # 1. Build the idempotent script (no host/credentials needed for the text).
    spec = SetupSpec(
        pve_user=pve_user,
        token_name=token_name,
        privsep=privsep,
        regenerate=regenerate,
        roles=dict(PROXCLI_ROLES),
        acls=list(PROXCLI_ACLS),
    )
    script = generate_setup_script(spec)

    # 2. Dry-run: preview only — no SSH, no prompts.
    if dry_run:
        host = getattr(args, "host", None) or "pve"
        ssh_user = getattr(args, "ssh_user", "root") or "root"
        port = getattr(args, "port", 22) or 22
        identity = getattr(args, "identity", None)
        ssh_cmd = SshRunner(
            host=host, user=ssh_user, port=port, identity=identity
        ).build_command("bash -s")
        payload = {"via": "ssh", "host": host, "ssh_command": ssh_cmd, "script": script}
        if json_mode:
            return payload
        console.print("[bold]SSH command:[/]")
        console.print("  " + " ".join(ssh_cmd))
        console.print("\n[bold]Script (piped to ssh stdin):[/]")
        sys.stdout.write(script)
        return None

    # 3. Resolve host (interactive prompt when allowed).
    host = getattr(args, "host", None)
    if not host:
        if getattr(args, "non_interactive", False):
            raise ProxmoxError("--host is required in --non-interactive mode")
        host = Prompt.ask("[bold]PVE node hostname or IP to SSH into[/]", console=console)
    if not host:
        raise ProxmoxError("a PVE host is required")

    ssh_user = getattr(args, "ssh_user", "root") or "root"
    port = getattr(args, "port", 22) or 22
    identity = getattr(args, "identity", None)

    # 4. Resolve SSH password (stdin / flag / interactive prompt; blank = key auth).
    password = getattr(args, "ssh_password", None)
    if getattr(args, "ssh_password_stdin", False):
        password = sys.stdin.readline().rstrip("\n") or None
    if not password and not getattr(args, "non_interactive", False):
        entered = Prompt.ask(
            "SSH password (leave blank to use SSH key auth)",
            password=True, console=console, default="",
        )
        if entered:
            password = entered

    runner = SshRunner(host=host, user=ssh_user, port=port, identity=identity, password=password)

    # 5. Execute on the node.
    console.print(f"[bold]Connecting to[/] {ssh_user}@{host}:{port} …")
    try:
        res = runner.run_script(script, timeout=180)
    except SshError as exc:
        raise ProxmoxError(str(exc)) from exc

    if not res.ok:
        detail = res.stderr.strip() or res.stdout.strip() or f"exit code {res.returncode}"
        raise ProxmoxError(f"SSH setup failed on {host}: {detail}")

    result = parse_setup_output(res.stdout)
    if not result.done:
        raise ProxmoxError(
            f"Setup script did not signal completion. SSH stdout:\n{res.stdout}"
        )
    _print_setup_summary(console, result, host)

    # 5. Write credentials.json (or print the secret).
    wrote = False
    if result.token_secret and not getattr(args, "no_write", False):
        api_url = getattr(args, "api_url", None) or f"https://{host}:8006"
        verify_tls = not getattr(args, "insecure", False)
        creds = {
            "url": api_url,
            "username": pve_user,
            "auth_method": AuthMethod.API_TOKEN.value,
            "api_token_id": token_name,
            "api_token_secret": result.token_secret,
            "verify_tls": verify_tls,
        }
        try:
            path = ConfigWriter().save(creds, force=getattr(args, "force", False))
            wrote = True
            console.print(f"\n[green]✓[/] Credentials written to [bold]{path}[/] (mode 0600)")
            console.print("    Verify with: [bold]proxmox auth status --permissions[/]")
        except ConfigError as exc:
            console.print(f"\n[yellow]![/] {exc}")
            console.print("    Re-run with [bold]--force[/] to overwrite (a .bak is kept),")
            console.print("    or [bold]--no-write[/] to print the secret instead.")
    elif result.token_secret and getattr(args, "no_write", False):
        console.print("\n[yellow]![/] --no-write: token secret not saved to disk.")
        console.print("    Secret (copy now, shown once):")
        sys.stdout.write(result.token_secret + "\n")
    elif result.token_status == "exists":
        console.print(
            "\n[yellow]![/] Token already exists — its secret cannot be recovered. "
            "Re-run with [bold]--regenerate[/] to rotate it."
        )

    if json_mode:
        out = result.to_dict()
        out["via"] = "ssh"
        out["host"] = host
        out["credentials_written"] = wrote
        return out
    return None


def _print_setup_summary(console: Console, result: SetupResult, host: str) -> None:
    """Print a human-readable summary of the setup result."""
    console.print(f"\n[bold]Setup results on[/] {host}:")
    if result.roles_created:
        console.print(f"  [green]+[/] roles created: {', '.join(result.roles_created)}")
    if result.roles_updated:
        console.print(f"  [green]↻[/] roles synced:   {', '.join(result.roles_updated)}")
    if result.role_failures:
        console.print(f"  [red]✗[/] role failures:   {', '.join(result.role_failures)}")
    console.print(f"  [cyan]•[/] token {result.token_ug}: {result.token_status}")
    if result.acls_set:
        console.print(f"  [green]+[/] ACLs set:       {len(result.acls_set)}")
    if result.acl_failures:
        console.print(f"  [red]✗[/] ACL failures:   {', '.join(result.acl_failures)}")


def _auth_setup_api(args: argparse.Namespace, client: ProxmoxClient, json_mode: bool) -> dict | None:
    """Create roles + ACLs for the configured token via the REST API (legacy).

    Requires an existing admin token (passed as ``client``). Unlike the SSH
    path, this does not create a token or write credentials.json — it only
    provisions the roles and ACLs for the currently-configured token.
    """
    console = Console(stderr=True, quiet=json_mode)
    created_roles: list[str] = []
    skipped_roles: list[str] = []
    created_acls: list[str] = []
    skipped_acls: list[str] = []

    # 1. Create roles (hoist the list fetch out of the loop).
    existing_roles = client.get("/access/roles")
    for role_name, privs in PROXCLI_ROLES.items():
        if any(r.get("roleid") == role_name for r in existing_roles):
            skipped_roles.append(role_name)
            continue
        content = _safe_encode({"roleid": role_name, "privs": privs})
        client.request("POST", "/access/roles", content=content)
        created_roles.append(role_name)

    # 2. Create ACLs for the token using 'tokens' parameter (plural — the API
    #    docs say 'tokenid' but the actual HTTP param is 'tokens').
    loader = ConfigLoader()
    creds = loader.load()
    token_ug = (
        f"{creds.username}!{creds.api_token_id}" if creds.api_token_id else creds.username
    )

    existing_acls = client.get("/access/acl")
    for path, role in PROXCLI_ACLS:
        already = any(
            a.get("path") == path
            and a.get("roleid") == role
            and a.get("ugid") == token_ug
            and a.get("type") == "token"
            for a in existing_acls
        )
        if already:
            skipped_acls.append(f"{path} → {role}")
            continue
        content = _safe_encode({"path": path, "roles": role, "tokens": token_ug})
        client.request("PUT", "/access/acl", content=content)
        created_acls.append(f"{path} → {role}")

    summary = {
        "via": "api",
        "token": token_ug,
        "roles_created": created_roles,
        "roles_skipped": skipped_roles,
        "acls_created": created_acls,
        "acls_skipped": skipped_acls,
    }
    if json_mode:
        return summary
    console.print(f"[green]✓[/] Setup via API complete for token {token_ug}")
    if created_roles:
        console.print(f"  roles created: {', '.join(created_roles)}")
    if skipped_roles:
        console.print(f"  roles skipped: {', '.join(skipped_roles)}")
    if created_acls:
        console.print(f"  ACLs created:  {', '.join(created_acls)}")
    if skipped_acls:
        console.print(f"  ACLs skipped:  {', '.join(skipped_acls)}")
    return None


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
    expected_roles = set("proxcli-" + suffix for suffix in ["sys", "storage", "vm", "node", "network"])
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
        console.print("   Keep only: [bold green]proxcli-sys, proxcli-storage, proxcli-vm, proxcli-node, proxcli-network[/]")
        console.print()
        # Add note to summary
        console.print(
            f"[bold yellow]⚠ {len(stray)} stray role(s) — remove after verifying proxcli roles work.[/]"
        )
