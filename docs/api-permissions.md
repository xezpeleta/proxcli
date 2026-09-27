# API Token Permissions

proxcli uses the Proxmox VE REST API.  This document describes how to create
an API token with the right permissions.

## Creating an API Token

The recommended way is `proxmox auth setup --host <node>` (see Quickstart below): it creates the token over SSH **with privilege separation ON** and assigns the `proxcli-*` roles directly to the token via ACLs — the token holds exactly the privileges it needs.

To create one manually in the Proxmox VE UI: **Datacenter → Permissions → API Tokens → Add**

1. Select **User**
2. Enter **Token ID** (e.g. `proxcli`)
3. **Privilege Separation**: leave checked and assign roles directly to the token
   (this is what `auth setup` does). Unchecking makes the token inherit all of
   the user's roles — simpler but broader.

The **Secret** is shown only once — save it immediately (or let `auth setup`
write it to `credentials.json` for you).

> **Privilege Separation**: when checked, you must assign roles directly to the
> token (via ACLs). When unchecked, the token inherits all of the user's roles.
> `auth setup` uses privilege separation ON with a dedicated `proxcli-*` role set
> — the least-privilege model.

## Quickstart (one command)

`proxmox auth setup` is the recommended path — by default it prints the exact
`pveum`/`pvesh` commands to run on a node as `root` (no SSH access required),
or with `--auto` it runs them over SSH in one idempotent pass:

```bash
# Default (manual): print the pveum/pvesh commands to review and run on a node.
# After running them, paste the token secret back when prompted (writes credentials.json):
proxmox auth setup

# Automatic over SSH into a node as root@pam; creates roles + token + ACLs
# and writes credentials.json:
proxmox auth setup --auto --host pve01.lan

# Preview the commands without touching the node:
proxmox auth setup --dry-run

# JSON output (for agents/automation) — emits the commands + a credentials template:
proxmox auth setup --non-interactive --json

# Done — everything works
proxmox auth status
proxmox cluster status
proxmox vm list
```

`auth setup` creates the token **with privilege separation ON** and assigns the
`proxcli-*` roles directly to the token via ACLs — the token holds exactly the
privileges it needs, independent of the user. (The legacy `--via api` path only
creates roles + ACLs using an existing Administrator token; it cannot capture or
write the secret, so prefer the default `manual` mode or `--auto`.)

### Fully manual alternative

If you can't run `auth setup` at all, create the token in the UI
(**Datacenter → Permissions → API Tokens → Add**) and hand-write
`credentials.json`:

```bash
cat > ~/.config/proxmox-cli/credentials.json <<'EOF'
{
  "url": "https://your-pve.example.com:8006",
  "username": "xezpeleta@pve",
  "auth_method": "api_token",
  "api_token_id": "proxcli",
  "api_token_secret": "your-token-secret-here",
  "verify_tls": false
}
EOF
chmod 600 ~/.config/proxmox-cli/credentials.json
```

Then run `proxmox auth setup --via api` (with an Administrator token already in
`credentials.json`) to create the roles + ACLs — or just run the default
`proxmox auth setup` to get the `pveum` commands to run on a node.

## Recommended Roles

Split privileges by path so each ACL only carries what it needs:

```
Role name: proxcli-sys

  Sys.Audit                    ← cluster/nodes/status/tasks/logs (read-only)
  Sys.Modify                   ← cluster firewall


Role name: proxcli-storage

  Datastore.AllocateSpace
  Datastore.AllocateTemplate
  Datastore.Audit
  # Datastore.Allocate is intentionally ABSENT — it is the sole privilege
  # PVE checks for deleting storage content (backups/volumes).  Without it
  # the token can upload, create disks, and read storage, but CANNOT delete
  # backups.  See "Backups are read-only by default" below.


Role name: proxcli-vm

  VM.Allocate
  VM.Audit
  # VM.Backup is intentionally ABSENT — it is required to create vzdump
  # backups AND is the alternative path to delete backup volumes.  Without
  # it `backup create` and `backup delete` are both blocked.  See below.
  VM.Clone
  VM.Config.CDROM
  VM.Config.Cloudinit
  VM.Config.CPU
  VM.Config.Disk
  VM.Config.HWType
  VM.Config.Memory
  VM.Config.Network
  VM.Config.Options
  VM.Console
  VM.GuestAgent.Audit            ← read-only agent queries (interfaces, osinfo, …)
  VM.GuestAgent.FileRead         ← agent file-read
  VM.Migrate
  VM.PowerMgmt
  VM.Snapshot
  VM.Snapshot.Rollback
  VM.GuestAgent.Unrestricted     ← OPTIONAL: `vm agent exec` (see below)

  Pool.Allocate
  Pool.Audit


Role name: proxcli-node

  VM.GuestAgent.Audit
  VM.GuestAgent.FileRead


Role name: proxcli-network

  SDN.Audit                     ← read SDN zones/vnets/controllers
  SDN.Use                       ← attach a VM NIC to an SDN bridge/vnet
                                 (required on top of VM.Config.Network
                                  when the bridge is SDN-managed, e.g. vmbr0)
```

```bash
# Assign each role to the token — use 'proxmox auth setup' (does this automatically):
proxmox auth setup

# Or manually via pvesh:
pvesh set /access/acl --path /        --roles proxcli-sys      --tokenid proxcli --users xezpeleta@pve
pvesh set /access/acl --path /storage --roles proxcli-storage  --tokenid proxcli --users xezpeleta@pve
pvesh set /access/acl --path /vms     --roles proxcli-vm       --tokenid proxcli --users xezpeleta@pve
pvesh set /access/acl --path /nodes   --roles proxcli-node    --tokenid proxcli --users xezpeleta@pve
pvesh set /access/acl --path /sdn     --roles proxcli-network --tokenid proxcli --users xezpeleta@pve
```

> **One-liner**: `proxmox auth setup` creates both roles and token ACLs
> automatically if your token has Administrator privileges.
>
> **Safe by design**: ACLs target the **token** (`--tokenid proxcli`),
> not the user.  Your user account keeps whatever roles it already has
> (PVEAdmin, Administrator, etc.).  The token gets exactly the proxcli
> privileges without touching anything else.

| Path | Role | Why |
|------|------|-----|
| `/` | `proxcli-sys` | `cluster status`, `node show`, `task list`, `ceph status`, `cluster log`, `cluster firewall`, `cluster ha` (read-only) |
| `/storage` | `proxcli-storage` | `storage list/upload`, `vm create` (disk + import) |
| `/vms` | `proxcli-vm` | `vm list/create/start/stop`, snapshots, backups, `pool` |
| `/nodes` | `proxcli-node` | QEMU guest agent interfaces, per-node Ceph logs |
| `/sdn` | `proxcli-network` | attach VM NICs to SDN-managed bridges/vnets (e.g. `vmbr0`); read SDN state |

> **Why a separate SDN role?** `proxcli-vm` already has `VM.Config.Network`,
> but when a bridge (like `vmbr0`) is **SDN-managed**, attaching a NIC to it
> additionally requires `SDN.Use`, and reading SDN state requires `SDN.Audit`.
> Without `proxcli-network`, VM creation fails at the `net0` step with HTTP 403
> `Permission check failed (/sdn, SDN.Use)`. `SDN.Allocate` (creating/modifying
> the SDN fabric itself) is intentionally **not** included — proxcli only
> *consumes* existing SDN networks, never redefines them.
>
> **Guest-agent exec (`vm agent exec`)** requires `VM.GuestAgent.Unrestricted`
> on `/vms/{vmid}`, which is **not** in the default `proxcli-vm` role — alone it
> grants *all* guest-agent operations (exec + file-write). Enable it explicitly:
> ```bash
> proxmox auth setup --host <node> --allow-guest-exec
> ```
> This adds the privilege to `proxcli-vm`; re-running syncs the role in place
> (`pveum role modify` replaces privs), so an **existing token gains exec
> immediately — no `--regenerate`, no rotation**. Drop the flag and re-run to
> revoke it again.

> **ACL management** (`proxmox acl`) and **user management**
> (`proxmox user`) require `Permissions.Modify`, which is only in the
> built-in **Administrator** role.  These are admin-only operations —
> add `Permissions.Modify` to `proxcli` if you need them, but it's a
> powerful privilege.

## Permission Model (Reference)

Proxmox permissions follow the pattern:

```
/path/to/resource    PrivilegeName[,PrivilegeName...]
```

- Paths can be broad (`/`) or specific (`/vms/100`)
- Privileges are inherited — permissions on `/` propagate to all sub-paths
- An API token's effective permissions are the **intersection** of:
  1. The token's own ACLs
  2. The user's ACLs (if privilege separation is enabled)

## Narrower Scoping (Optional)

If you want to limit what a token can touch, use the bare minimum
privileges per workflow:

### Cloud-Init VM Workflow

The complete workflow of uploading a cloud image, creating a VM with
cloud-init, and starting it:

| Step | Method | Endpoint | Privilege |
|------|--------|----------|-----------|
| 1 | GET | `/cluster/nextid` | `Sys.Audit` |
| 2 | POST | `/nodes/{node}/storage/{storage}/upload` | `Datastore.AllocateTemplate` |
| 3 | POST | `/nodes/{node}/qemu` | `VM.Allocate` |
| 3 | — | (reads imported image) | `Datastore.AllocateSpace` or `Datastore.Audit` |
| 3 | — | (allocates disk on target storage) | `Datastore.AllocateSpace` |
| 3 | — | (attaches scsi0 disk) | `VM.Config.Disk` |
| 3 | — | (sets net0) | `VM.Config.Network` (+ `SDN.Use` if bridge is SDN-managed) |
| 3 | — | (sets cloud-init: citype, ciuser, …) | `VM.Config.Cloudinit` |
| 3 | — | (sets bios, machine, boot order) | `VM.Config.Options` |
| 4 | POST | `/nodes/{node}/qemu/{vmid}/status/start` | `VM.PowerMgmt` |
| 5 | GET | `/nodes/{node}/qemu/{vmid}/status/current` | `VM.Audit` |

**Minimal role `PVECloudInitAdmin`**: `Sys.Audit`, `Datastore.Allocate`,
`Datastore.AllocateSpace`, `Datastore.AllocateTemplate`, `VM.Allocate`,
`VM.Audit`, `VM.Config.Cloudinit`, `VM.Config.Disk`, `VM.Config.Network`,
`VM.Config.Options`, `VM.PowerMgmt`.

### Additional Privileges by Feature

| Feature | Extra Privileges Needed |
|---------|------------------------|
| Snapshots | `VM.Snapshot`, `VM.Snapshot.Rollback` |
| Clone VM | `VM.Clone` |
| Change memory/CPU | `VM.Config.Memory`, `VM.Config.CPU` |
| Attach ISOs | `VM.Config.CDROM` |
| Migrate VM | `VM.Migrate` |
| Backup VM | `VM.Backup` |
| Delete VM | `VM.Allocate` (already needed), `Datastore.AllocateSpace` |
| QEMU guest agent | `VM.GuestAgent.Audit`, `VM.GuestAgent.FileRead` |
| Containers | `VM.Allocate`, `VM.Audit`, `VM.PowerMgmt` |
| Pools | `Pool.Allocate`, `Pool.Audit` |
| SDN-managed NICs (vmbr0, vnets) | `SDN.Use`, `SDN.Audit` (→ `proxcli-network` at `/sdn`) |
| Cluster/node/VM firewall | `Sys.Modify`, `Sys.Audit` |
| ACL management | `Permissions.Modify` (Administrator role) |
| User/role management | `Permissions.Modify` (Administrator role) |

### Built-in Roles (for reference)

**PVEVMAdmin**: `VM.Allocate`, `VM.Audit`, `VM.Backup`, `VM.Clone`,
`VM.Config.CDROM`, `VM.Config.Cloudinit`, `VM.Config.CPU`,
`VM.Config.Disk`, `VM.Config.HWType`, `VM.Config.Memory`,
`VM.Config.Network`, `VM.Config.Options`, `VM.Console`, `VM.Migrate`,
`VM.PowerMgmt`, `VM.Snapshot`, `VM.Snapshot.Rollback`

**PVEDatastoreAdmin**: `Datastore.Allocate`, `Datastore.AllocateSpace`,
`Datastore.AllocateTemplate`, `Datastore.Audit`, `Datastore.Copy`

**PVEPoolAdmin**: `Pool.Allocate`, `Pool.Audit`

## Verifying Permissions

Check your current effective permissions:

```bash
proxmox auth permissions
```

Or test a specific action with dry-run:

```bash
proxmox --dry-run vm create --node <node> --memory 512 --cores 1
```

If any privilege is missing, Proxmox returns a **403 Forbidden**.

## Applying permissions via `pveum` (node shell)

`proxmox auth setup` creates the roles + ACLs for you, but it requires a
token that already has `Permissions.Modify` (i.e. **Administrator**). For a
fresh cluster or a locked-down token, run these on a **Proxmox node shell as
`root@pam`** (`pveum` is the CLI front-end to the access-control API).

### A. Fix an existing token (add SDN only)

If your token already has the four `proxcli-*` roles but fails on
SDN-managed bridges (`vmbr0`), just add `proxcli-network`:

```bash
# Run on a Proxmox node as root@pam

# 1. Create the SDN role (idempotent — skip if it exists)
pveum role add proxcli-network -privs "SDN.Audit,SDN.Use"

# 2. Grant it to the existing token at /sdn (propagates to all SDN sub-paths)
pveum aclmod /sdn -token 'xezpeleta@pve!proxcli' -roles proxcli-network

# 3. Verify
pveum acl list | grep proxcli-network
proxmox api GET /cluster/sdn          # was 403, now returns SDN state
```

### B. Create a brand-new token from scratch (all five roles)

```bash
# Run on a Proxmox node as root@pam
USER=xezpeleta@pve
TOKEN=vmanager

# ── 1. Create the five proxcli roles (idempotent) ──
pveum role add proxcli-sys      -privs "Sys.Audit,Sys.Modify,Pool.Allocate,Pool.Audit"
pveum role add proxcli-storage  -privs "Datastore.AllocateSpace,Datastore.AllocateTemplate,Datastore.Audit"
pveum role add proxcli-vm       -privs "VM.Allocate,VM.Audit,VM.Clone,VM.Config.CDROM,VM.Config.Cloudinit,VM.Config.CPU,VM.Config.Disk,VM.Config.HWType,VM.Config.Memory,VM.Config.Network,VM.Config.Options,VM.Console,VM.GuestAgent.Audit,VM.GuestAgent.FileRead,VM.Migrate,VM.PowerMgmt,VM.Snapshot,VM.Snapshot.Rollback"
pveum role add proxcli-node     -privs "VM.GuestAgent.Audit,VM.GuestAgent.FileRead"
pveum role add proxcli-network  -privs "SDN.Audit,SDN.Use"

# ── 2. Create the token (privilege separation ON → token gets its own ACLs) ──
#    The SECRET is printed ONCE — capture it immediately.
pveum user token add "$USER" "$TOKEN" -privsep 1

# ── 3. Assign each role at its path (propagates by default) ──
UG="$USER!$TOKEN"
pveum aclmod /        -token "$UG" -roles proxcli-sys
pveum aclmod /storage -token "$UG" -roles proxcli-storage
pveum aclmod /vms     -token "$UG" -roles proxcli-vm
pveum aclmod /nodes   -token "$UG" -roles proxcli-node
pveum aclmod /sdn     -token "$UG" -roles proxcli-network

# ── 4. Verify ──
pveum acl list | grep "$UG"
```

Then write the new token's secret into `~/.config/proxmox-cli/credentials.json`
(`api_token_id: vmanager`, `api_token_secret: <captured secret>`) and run
`proxmox auth status` / `proxmox auth permissions` to confirm.

> **UI equivalent** (Datacenter → Permissions → Add → API Token Permission):
> Path `/sdn` may not appear as a selectable node in the path tree — only its
> children (`/sdn/zones`, `/sdn/fabrics`, …) do. Assigning the role at
> `/sdn/zones` with **Propagate** enabled also works for VM NIC attach, but the
> canonical, unambiguous path is `/sdn` via `pveum` as shown above.

## Backups are read-only by default

The default `proxcli-storage` and `proxcli-vm` roles are deliberately
**missing two privileges** so that a freshly-bootstrapped token **cannot
create or delete backups**:

| Privilege | Absent from | What it controls on PVE |
|-----------|-------------|-------------------------|
| `Datastore.Allocate` | `proxcli-storage` | Deleting storage content — it is the *sole* privilege checked by `DELETE /nodes/{node}/storage/{storage}/content/{volid}`. |
| `VM.Backup` | `proxcli-vm` | Creating vzdump backups (`POST /nodes/{node}/vzdump`) **and** the alternative delete path (a backup volume can be deleted with `Datastore.AllocateSpace` + `VM.Backup` on the owning VM). |

Removing both closes **every** door to backup mutation:

| Command | Method | Required privilege | Default? |
|---------|--------|--------------------|----------|
| `backup list` / `show` | GET | `Datastore.Audit` | ✅ granted |
| `backup tasks` / `defaults` | GET | `Sys.Audit` | ✅ granted |
| `backup create` | POST `/vzdump` | `VM.Backup` | ❌ blocked |
| `backup delete` (path A) | DELETE content | `Datastore.Allocate` | ❌ blocked |
| `backup delete` (path B) | DELETE content | `Datastore.AllocateSpace` + `VM.Backup` | ❌ blocked |
| `backup restore` | POST `/qemu` | `VM.Allocate` | ✅ granted¹ |

> ¹ Restore shares `VM.Allocate` with `vm create` / `vm clone` — it cannot be
> blocked without breaking core VM lifecycle. Restore is non-destructive to
> the backup itself (it reads the backup and writes a *new* VM), so this is an
> acceptable trade-off.

**No collateral damage.** The privileges that remain are sufficient for every
other workflow:

- `storage upload` → `Datastore.AllocateTemplate` ✅
- `vm create` (with disk) → `Datastore.AllocateSpace` ✅
- `vm create --import-from` (cloud images) → `Datastore.AllocateSpace` or `Datastore.Audit` ✅
- `vm disk import` → `VM.Config.Disk` + `Datastore.AllocateSpace` ✅
- `storage list` / `show` / `status` → `Datastore.Audit` ✅

This was verified against the PVE source (`PVE::Storage::check_volume_access`
and `PVE::API2::Storage::Content`): `Datastore.Allocate` is checked **only** in
the volume-delete handler.

### Enabling backup create/delete (opt-in)

If you *want* a token to run vzdump or prune old backups, add the missing
privilege to a custom role:

```bash
# Create a role that can create+delete backups, then assign it at /storage + /vms
pveum role add proxcli-backup -privs "VM.Backup,Datastore.Allocate"
pveum aclmod /storage -token "$UG" -roles proxcli-backup
pveum aclmod /vms     -token "$UG" -roles proxcli-backup
```

Snapshots (`VM.Snapshot`, `VM.Snapshot.Rollback`) remain in the default
`proxcli-vm` role — they are a separate, lighter-weight mechanism and are
considered safe enough for day-to-day use.
