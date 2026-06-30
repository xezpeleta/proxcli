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

Two approaches are available:

**Approach A: CLI flags only** (best for scripting and one-liners):

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

**Approach B: `--file` YAML spec** (best for declarative, version-controlled configs):

```bash
# 1. Export an existing VM config as a starting point (optional)
proxmox --output yaml vm config 112 > my-vm.yaml

# 2. Edit the YAML with your desired config
```

```yaml
# my-vm.yaml — native Proxmox VM config keys
name: my-cloud-vm
node: sanmarko
memory: 4096
cores: 2
import_from: local:import/debian-12-genericcloud-amd64.qcow2
citype: nocloud
ciuser: debian
cipassword: SecurePassword123!
sshkeys: ~/.ssh/id_rsa.pub
nameserver: 1.1.1.1
searchdomain: mydomain.lan
net0: "virtio,bridge=vmbr0"
```

```bash
# 3. Create the VM from file (CLI flags override file values)
proxmox vm create --file my-vm.yaml

# Override specific values on the fly:
proxmox vm create --file my-vm.yaml --name staging-vm --memory 8192
```

The YAML format uses **native Proxmox VM config keys** — the same fields
returned by `vm config` and accepted by the Proxmox API.  Any key in the
file that isn't overridden by a CLI flag is passed directly as a body
parameter to the API.

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

After the VM is created, use `vm set` to update cloud-init parameters:

```bash
proxmox vm set <vmid> --node <node> \
  --ciuser debian \
  --sshkeys ~/.ssh/new_key.pub \
  --ipconfig0 "ip=192.168.1.100/24,gw=192.168.1.1"
```

Any Proxmox config key can be set via `--option key=value`:

```bash
proxmox vm set <vmid> --node <node> \
  --option memory=4096 \
  --option description="Updated via proxcli"
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

### CLI flags approach

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

### --file approach (declarative)

```bash
# 1. Create the spec file
cat > webserver.yaml << 'EOF'
name: webserver
node: sanmarko
memory: 4096
cores: 2
import_from: local:import/debian-12-genericcloud-amd64.qcow2
citype: nocloud
ciuser: debian
cipassword: ChangeMe123!
sshkeys: ~/.ssh/id_rsa.pub
nameserver: 1.1.1.1
searchdomain: tknika.net
net0: "virtio,bridge=vmbr0"
EOF

# 2. Create from file
proxmox vm create --file webserver.yaml

# 3. Start and SSH (same as above)
proxmox vm start <vmid>
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

## Raw API fallback

For Proxmox endpoints not covered by dedicated subcommands (e.g., bulk
operations, advanced config keys), use `proxmox api` to make authenticated
direct API calls:

```bash
# Read VM config
proxmox api GET /nodes/pve01/qemu/100/config

# Update any config key
proxmox api PUT /nodes/pve01/qemu/100/config -d '{"description": "web server"}'

# Create resources
proxmox api POST /nodes/pve01/qemu -f vm-spec.json
```

The `api` subcommand reuses the same authentication and TLS settings as the
rest of proxcli — no need to manage API tokens with `curl`.

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

---

## Creating a Reusable Cloud-Init Template

Instead of creating VMs one-by-one from a cloud image, you can build a
**template** — a preconfigured, stopped VM marked as a template — and then
clone it repeatedly.  Each clone gets its own cloud-init drive, so you can
set per-VM hostnames, IPs, and SSH keys at clone time.

### The workflow at a glance

```
upload image  →  vm create (cloud-init, stopped)  →  vm template  →  vm clone (×N)
```

### Step 1: Download and upload the cloud image

Pick the Debian `generic` variant — it includes full hardware driver support
and works with any cloud-init environment, including Proxmox.

| Variant | Use case | Size (qcow2) |
|---------|----------|--------------|
| `generic` | Proxmox, OpenStack, bare metal. Full driver support. | ~415 MiB |
| `genericcloud` | Same as generic, but fewer kernel drivers. Smaller image. | ~325 MiB |

Stable release URLs follow the pattern:
`https://cloud.debian.org/images/cloud/<release>/latest/debian-<version>-generic-amd64.qcow2`

The `/latest/` symlink always points to the most recent weekly build.

```bash
# Download (run on a Proxmox node or any machine with proxcli)
curl -LO https://cloud.debian.org/images/cloud/trixie/latest/debian-13-generic-amd64.qcow2

# Upload as an import volume
proxmox storage upload \
  --node <node> \
  --storage local \
  --content-type import \
  --file debian-13-generic-amd64.qcow2

# Verify it's there
proxmox storage content local --node <node>
# Look for: local:import/debian-13-generic-amd64.qcow2
```

### Step 2: Create the VM with cloud-init (stopped)

```bash
proxmox vm create \
  --node <node> \
  --vmid <template-vmid> \
  --name debian-trixie-cloudinit-template \
  --memory 2048 \
  --cores 2 \
  --net 'virtio,bridge=vmbr0' \
  --scsihw virtio-scsi-pci \
  --boot order=scsi0 \
  --citype nocloud \
  --ciuser debian \
  --sshkeys ~/.ssh/id_rsa.pub \
  --import-from local:import/debian-13-generic-amd64.qcow2
```

> **Important**: Do **not** start the VM before converting to a template.
> The VM stays stopped after `vm create` unless you pass `--start`
> (not yet implemented in proxcli).

Key points:
- `--vmid`: pick a dedicated ID range for templates (e.g., 9000–9999).
- `--ciuser debian`: the default user on Debian cloud images is `debian`.
- `--sshkeys`: SSH keys set here become the **default** keys for clones.
  Each clone can override them.

### Step 3: Convert to template

```bash
proxmox vm template <template-vmid> --node <node>
```

This marks the VM as a template.  It can no longer be started directly —
only cloned.

### Step 4: Clone from the template

```bash
proxmox vm clone <template-vmid> \
  --newid <new-vmid> \
  --name my-new-debian-vm \
  --full 1
```

- `--full 1`: always use full clones (independent disks).  Linked clones
  (`--full 0`) require the template disk to remain untouched.
- `--target-node`: clone to a different node if needed.
- `--target-storage`: place the clone's disk on a specific storage.

### Step 5: Customize the clone before first boot

After cloning, set per-VM cloud-init parameters with `vm set`:

```bash
# Set a static IP (optional — DHCP is the default)
proxmox vm set <new-vmid> --node <node> --ipconfig0 "ip=192.168.1.50/24,gw=192.168.1.1"

# Add a VM-specific SSH key
proxmox vm set <new-vmid> --node <node> --sshkeys ~/.ssh/id_rsa.pub

# Regenerate the cloud-init ISO with the new settings
proxmox vm cloudinit generate <new-vmid> --node <node>
```

Then start it:

```bash
proxmox vm start <new-vmid>
```

On first boot, cloud-init applies the VM-specific settings (hostname, IP,
SSH keys).

### Example: Debian 13 template + two clones

```bash
# --- One-time setup ---
curl -LO https://cloud.debian.org/images/cloud/trixie/latest/debian-13-generic-amd64.qcow2

proxmox storage upload \
  --node pve01 --storage local --content-type import \
  --file debian-13-generic-amd64.qcow2

proxmox vm create \
  --node pve01 --vmid 9003 \
  --name debian13-cloud-template \
  --memory 2048 --cores 2 \
  --net 'virtio,bridge=vmbr0' \
  --scsihw virtio-scsi-pci --boot order=scsi0 \
  --citype nocloud --ciuser debian \
  --sshkeys ~/.ssh/id_rsa.pub \
  --import-from local:import/debian-13-generic-amd64.qcow2

proxmox vm template 9003 --node pve01

# --- Clone for each new VM (repeat as needed) ---

# Web server
proxmox vm clone 9003 --newid 201 --name web01 --full 1
proxmox vm set 201 --node pve01 --ipconfig0 "ip=10.0.0.51/24,gw=10.0.0.1"
proxmox vm cloudinit generate 201
proxmox vm start 201

# Database server
proxmox vm clone 9003 --newid 202 --name db01 --full 1
proxmox vm set 202 --node pve01 --ipconfig0 "ip=10.0.0.52/24,gw=10.0.0.1"
proxmox vm cloudinit generate 202
proxmox vm start 202
```

### Updating the template

To refresh the template with a newer Debian build:

```bash
# 1. Download and upload the new image
curl -LO https://cloud.debian.org/images/cloud/trixie/latest/debian-13-generic-amd64.qcow2
proxmox storage upload --node pve01 --storage local --content-type import \
  --file debian-13-generic-amd64.qcow2

# 2. Delete the old template
proxmox vm delete 9003 --node pve01

# 3. Recreate with the new image (same vmid, same name)
#    ... repeat step 2 above ...
```

Existing clones are unaffected — full clones have independent disks.
