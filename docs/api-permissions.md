# API Token Permissions

proxcli uses the Proxmox VE REST API.  This document describes how to create
a minimal-permission API token for common workflows.

## Creating an API Token

In the Proxmox VE UI: **Datacenter → Permissions → API Tokens → Add**

1. Select **User**
2. Enter **Token ID** (e.g. `proxcli`)
3. Uncheck **Privilege Separation** (for simplicity) or leave it checked
   if you want to limit the token's permissions

The **Secret** is shown only once — save it immediately.

## Permission Model

Proxmox permissions follow the pattern:

```
/path/to/resource    PrivilegeName[,PrivilegeName...]
```

- Paths can be broad (`/`) or specific (`/vms/100`)
- Privileges are inherited — permissions on `/` propagate to all sub-paths
- An API token's effective permissions are the **intersection** of:
  1. The token's own ACLs
  2. The user's ACLs (if privilege separation is enabled)

## Step-by-Step: Cloud-Init VM Workflow

The complete workflow of uploading a cloud image, creating a VM with
cloud-init, and starting it uses these endpoints:

| Step | Method | Endpoint | Privilege |
|------|--------|----------|-----------|
| 1 | GET | `/cluster/nextid` | `Sys.Audit` |
| 2 | POST | `/nodes/{node}/storage/{storage}/upload` | `Datastore.AllocateTemplate` |
| 3 | POST | `/nodes/{node}/qemu` | `VM.Allocate` |
| 3 | — | (reads imported image from source storage) | `Datastore.Allocate` |
| 3 | — | (allocates disk on target storage) | `Datastore.AllocateSpace` |
| 3 | — | (attaches scsi0 disk) | `VM.Config.Disk` |
| 3 | — | (sets net0) | `VM.Config.Network` |
| 3 | — | (sets cloud-init: citype, ciuser, sshkeys, etc.) | `VM.Config.Cloudinit` |
| 3 | — | (sets bios, machine, boot order) | `VM.Config.Options` |
| 4 | POST | `/nodes/{node}/qemu/{vmid}/status/start` | `VM.PowerMgmt` |
| 5 | GET | `/nodes/{node}/qemu/{vmid}/status/current` | `VM.Audit` |
| 5 | GET | `/cluster/resources` | `Sys.Audit` |

## Minimal Role: PVECloudInitAdmin

Create a role with only the 11 required privileges:

```
Role name: PVECloudInitAdmin

Privileges:
  Sys.Audit
  Datastore.Allocate
  Datastore.AllocateSpace
  Datastore.AllocateTemplate
  VM.Allocate
  VM.Audit
  VM.Config.Cloudinit
  VM.Config.Disk
  VM.Config.Network
  VM.Config.Options
  VM.PowerMgmt
```

### ACLs (broad — covers all storages and VMs)

```
Add → Path: /
Add → Path: /storage
Add → Path: /vms
```

Assign the `PVECloudInitAdmin` role to all three paths for your user or
token.  Since permissions inherit, `/vms` covers all VMs and
`/storage` covers all storages.

### ACLs (narrow — single storage, single node)

If you know exactly which storages you'll use, lock it down further:

```
Path: /                          Role: PVECloudInitAdmin (only for Sys.Audit)
Path: /storage/local            Role: PVECloudInitAdmin (for upload + import)
Path: /storage/rbd_ssd           Role: PVECloudInitAdmin (for disk allocation)
Path: /vms                       Role: PVECloudInitAdmin (for VM operations)
```

Or even narrower per-VM:

```
Path: /vms/100-199              Role: PVECloudInitAdmin
```

## Additional Privileges for Other Workflows

| Feature | Extra Privileges |
|---------|-----------------|
| Snapshots | `VM.Snapshot`, `VM.Snapshot.Rollback` |
| Clone VM | `VM.Clone` |
| Change memory/CPU | `VM.Config.Memory`, `VM.Config.CPU` |
| Attach ISOs | `VM.Config.CDROM` |
| Migrate VM | `VM.Migrate` |
| Backup VM | `VM.Backup` |
| Delete VM | `VM.Allocate` (already included), `Datastore.AllocateSpace` |
| QEMU guest agent | `VM.GuestAgent.Audit`, `VM.GuestAgent.FileRead` |
| Containers | `VM.Allocate` (LXC creation), `VM.Audit`, `VM.PowerMgmt` |
| Pools | `Pool.Allocate`, `Pool.Audit` |
| Cluster firewall | `Sys.Modify`, `Sys.Audit` |
| Node firewall | `Sys.Modify` |
| VM firewall | `VM.Allocate` (already included) |

## Full Admin Role (for comparison)

The built-in **PVEVMAdmin** role includes:

```
VM.Allocate, VM.Audit, VM.Backup, VM.Clone, VM.Config.CDROM,
VM.Config.Cloudinit, VM.Config.CPU, VM.Config.Disk, VM.Config.HWType,
VM.Config.Memory, VM.Config.Network, VM.Config.Options, VM.Console,
VM.Migrate, VM.Monitor, VM.PowerMgmt, VM.Snapshot, VM.Snapshot.Rollback
```

The built-in **PVEDatastoreAdmin** adds:

```
Datastore.Allocate, Datastore.AllocateSpace, Datastore.AllocateTemplate,
Datastore.Audit, Datastore.Copy
```

## Verifying Permissions

Check your current effective permissions:

```bash
proxmox auth permissions
```

Or test a specific action with dry-run:

```bash
proxmox --dry-run vm create --node <node> --memory 512 --cores 1
```

The dry-run output shows the exact endpoint and HTTP method — if any
privilege is missing, Proxmox will return a **403 Forbidden**.
