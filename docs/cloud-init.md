# Cloud-Init VM Management with proxcli

Cloud-init allows you to create and fully configure VMs declaratively — users,
SSH keys, networking, and packages are defined via `proxcli` flags rather than
manual post-install steps.

## Prerequisites

### 1. Storage with `images` and `import` content types

You need a Proxmox storage that supports both `images` (for VM disks) and
`import` (for uploading disk images).  On Proxmox VE, edit the storage in
**Datacenter → Storage → Edit** and add the content types:

- `Disk image` — to store VM disks
- `ISO image` — optional, if you also want to store ISOs there

Example: a `dir` type storage with path `/var/lib/vz` that has `images`, `iso`,
and `import` enabled.

Verify with:
```bash
proxmox storage list
```

Look for a storage where `content` includes `images` and (for uploads) `import`.

### 2. Download a cloud-init image

Cloud images are pre-built OS images with cloud-init installed.  You can find
them at:

- **Debian**: https://cloud.debian.org/images/cloud/bookworm/latest/
  - File: `debian-12-genericcloud-amd64.qcow2` (333 MB)
- **Ubuntu**: https://cloud-images.ubuntu.com/releases/24.04/release/
  - File: `ubuntu-24.04-server-cloudimg-amd64.img` (593 MB)

```bash
# Download examples
curl -LO https://cloud.debian.org/images/cloud/bookworm/latest/debian-12-genericcloud-amd64.qcow2
curl -LO https://cloud-images.ubuntu.com/releases/noble/release/ubuntu-24.04-server-cloudimg-amd64.img
```

### 3. Upload the image to Proxmox storage

```bash
proxmox storage upload \
  --node <node> \
  --storage <storage> \
  --content-type import \
  --file debian-12-genericcloud-amd64.qcow2
```

After upload, the image will be available as `<storage>:import/<filename>`.
You can verify with:

```bash
proxmox storage content <storage> --node <node>
```

---

## Creating a Cloud-Init VM

The complete workflow is a **single `vm create` command** — Proxmox handles
disk import, cloud-init drive creation, and ISO generation automatically:

```bash
proxmox vm create \
  --node sanmarko \
  --memory 4096 \
  --cores 2 \
  --name my-cloud-vm \
  --import-from local:import/debian-12-genericcloud-amd64.qcow2 \
  --citype nocloud \
  --ciuser debian \
  --cipassword 'SecurePassword123!' \
  --sshkeys ~/.ssh/id_rsa.pub \
  --nameserver 1.1.1.1 \
  --searchdomain mydomain.lan \
  --net 'virtio,bridge=vmbr0'
```

### Flag reference

| Flag | Description |
|------|-------------|
| `--import-from <storage:path>` | Import the boot disk from an existing volume |
| `--citype nocloud\|configdrive2` | Cloud-init data source type |
| `--ciuser <username>` | Default user (e.g. `debian`, `ubuntu`) |
| `--cipassword <password>` | User password (hashed by cloud-init) |
| `--sshkeys <file\|inline>` | SSH public keys (reads file if it exists, otherwise uses inline) |
| `--nameserver <ip>` | DNS server |
| `--searchdomain <domain>` | DNS search domain |
| `--cicustom <config>` | Custom cloud-init config (`user=...,vendor=...`) |
| `--storage <name>` | Target storage for the imported disk (defaults to `rbd_ssd`) |

### What happens

1. Proxmox assigns a VM ID (or use `--vmid` to specify)
2. The cloud image is **streamed from the import storage to the target storage**
   and attached as `scsi0`
3. A cloud-init drive is created (`ide2`) with the configured user, password,
   SSH keys, and network settings
4. The VM is created in *stopped* state, ready to start

### Verify the configuration

```bash
proxmox vm show <vmid>
```

The output includes:
- `scsi0` pointing to the imported disk on the target storage
- `citype`, `ciuser`, `cipassword`, `nameserver`, etc.
- `ide2` with the cloud-init ISO

---

## Managing Cloud-Init VMs

### Updating cloud-init configuration

After the VM is created, you can update cloud-init parameters using
`PUT /nodes/{node}/qemu/{vmid}/config` (no dedicated proxcli command yet):

```bash
# Currently via curl; a proxcli vm update command is planned
# This triggers automatic cloud-init ISO regeneration in Proxmox VE 9
```

In Proxmox VE 9+, the cloud-init ISO is **regenerated automatically** whenever
cloud-init config parameters change.  There is no separate "generate" step.

### Dumping current cloud-init config

```bash
proxmox vm cloudinit generate <vmid>
```

This reads the current `citype` from the VM config and re-submits it to
trigger regeneration.  (In Proxmox VE 9, config changes auto-regenerate,
but this command is provided for environments where explicit generation
is needed.)

### Starting the VM

```bash
proxmox vm start <vmid>
```

On first boot, cloud-init will:
1. Set the hostname
2. Create the specified user with the given password
3. Install the SSH keys
4. Configure networking
5. Run any `#cloud-config` directives (if using `--cicustom`)

---

## Complete Example: Debian 12 Cloud VM

```bash
# 1. Upload the cloud image (one-time)
proxmox storage upload \
  --node sanmarko --storage local --content-type import \
  --file debian-12-genericcloud-amd64.qcow2

# 2. Create the VM
proxmox vm create \
  --node sanmarko \
  --name webserver \
  --memory 4096 --cores 2 \
  --import-from local:import/debian-12-genericcloud-amd64.qcow2 \
  --citype nocloud \
  --ciuser debian \
  --cipassword 'ChangeMe123!' \
  --sshkeys ~/.ssh/id_rsa.pub \
  --nameserver 1.1.1.1 \
  --searchdomain tknika.net \
  --net 'virtio,bridge=vmbr0'

# 3. Start it
proxmox vm start <vmid>

# 4. SSH in (after boot completes)
ssh debian@<ip>
```

---

## Custom Cloud-Init Config

For advanced customization (packages, runcmd, write_files), use `--cicustom`
with a user-data YAML file:

```bash
proxmox vm create \
  ... \
  --cicustom 'user=local:snippets/user-data.yaml'
```

Upload the snippet first:
```bash
proxmox storage upload \
  --node sanmarko --storage local --content-type snippets \
  --file user-data.yaml
```

Example `user-data.yaml`:
```yaml
#cloud-config
packages:
  - nginx
  - htop
  - curl

package_update: true
package_upgrade: true

runcmd:
  - systemctl enable --now nginx
  - echo "Hello from cloud-init" > /etc/motd
```

---

## Troubleshooting

### "storage does not support 'import' content"

Your storage only has `iso` or `images` enabled.  Go to **Datacenter → Storage**
in the Proxmox UI and add `Disk image` and `Import` content types to the storage.

### "has wrong type 'iso' - needs to be 'images' or 'import'"

You uploaded the image with `--content-type iso` instead of `--content-type import`.
Re-upload with the correct content type, or change the storage's content types.

### "Only root can pass arbitrary filesystem paths"

The `import-from` parameter uses a **volume ID** (`local:import/file.qcow2`),
not a filesystem path (`/var/lib/vz/...`).  Make sure the image is uploaded to
Proxmox storage first via `storage upload`.

### Cloud-init not running on boot

Check that the cloud-init drive is attached:
```bash
proxmox vm show <vmid>
# Look for: ide2: local:XXX/vm-XXX-cloudinit.qcow2,media=cdrom
```

If missing, the cloud-init drive wasn't created.  This happens when no
cloud-init flags (`--ciuser`, `--citype`, etc.) are passed to `vm create`.
