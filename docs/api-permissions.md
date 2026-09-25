# API Token Permissions

proxcli uses the Proxmox VE REST API.  This document describes how to create
an API token with the right permissions.

## Creating an API Token

In the Proxmox VE UI: **Datacenter → Permissions → API Tokens → Add**

1. Select **User**
2. Enter **Token ID** (e.g. `proxcli`)
3. Uncheck **Privilege Separation** (recommended — see note below)

The **Secret** is shown only once — save it immediately.

> **Privilege Separation**: when unchecked, the token inherits all of the
> user's roles.  When checked, you must assign roles directly to the token.
> Unchecking is simpler but broader.  Check it if you want to lock down
> the token independently of the user.

## Quickstart (3 steps)

```bash
# 1. Bootstrap roles + ACLs (once, needs Administrator)
proxmox auth setup

# 2. Create API token (UI: Datacenter → Permissions → API Tokens → Add)
#     User:     xezpeleta@pve
#     Token ID: proxcli
#     ☐ Privilege Separation (unchecked — inherits user's roles)
#     Save the secret!

# 3. Write credentials.json with the new token secret
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
chmod 400 ~/.config/proxmox-cli/credentials.json

# Done — everything works
proxmox auth status
proxmox cluster status
proxmox vm list
```

## Recommended Roles

Split privileges by path so each ACL only carries what it needs:

```
Role name: proxcli-sys

  Sys.Audit                    ← cluster/nodes/status/tasks/logs (read-only)
  Sys.Modify                   ← cluster firewall


Role name: proxcli-storage

  Datastore.Allocate
  Datastore.AllocateSpace
  Datastore.AllocateTemplate
  Datastore.Audit


Role name: proxcli-vm

  VM.Allocate
  VM.Audit
  VM.Backup
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
  VM.Migrate
  VM.PowerMgmt
  VM.Snapshot
  VM.Snapshot.Rollback

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
| `/` | `proxcli-sys` | `cluster status`, `node show`, `task list`, `ceph status`, `cluster log`, `cluster firewall` |
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
| 3 | — | (reads imported image) | `Datastore.Allocate` |
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
pveum role add proxcli-storage  -privs "Datastore.Allocate,Datastore.AllocateSpace,Datastore.AllocateTemplate,Datastore.Audit"
pveum role add proxcli-vm       -privs "VM.Allocate,VM.Audit,VM.Backup,VM.Clone,VM.Config.CDROM,VM.Config.Cloudinit,VM.Config.CPU,VM.Config.Disk,VM.Config.HWType,VM.Config.Memory,VM.Config.Network,VM.Config.Options,VM.Console,VM.GuestAgent.Audit,VM.GuestAgent.FileRead,VM.Migrate,VM.PowerMgmt,VM.Snapshot,VM.Snapshot.Rollback"
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
