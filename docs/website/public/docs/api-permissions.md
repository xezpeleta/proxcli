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
```

```bash
# Assign each role to the token — use 'proxmox auth setup' (does this automatically):
proxmox auth setup

# Or manually via pvesh:
pvesh set /access/acl --path /        --roles proxcli-sys    --tokenid proxcli --users xezpeleta@pve
pvesh set /access/acl --path /storage --roles proxcli-storage --tokenid proxcli --users xezpeleta@pve
pvesh set /access/acl --path /vms     --roles proxcli-vm     --tokenid proxcli --users xezpeleta@pve
pvesh set /access/acl --path /nodes   --roles proxcli-node   --tokenid proxcli --users xezpeleta@pve
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
| 3 | — | (sets net0) | `VM.Config.Network` |
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
