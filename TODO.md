# TODO

Planned improvements for future releases. Items are roughly ordered by priority.

Completed items are marked with a check. Implementation notes are preserved for context.

---

## ✅ Done

- [x] **Firewall management** — cluster, node, VM, and container. Options, enable/disable, policy, rules (CRUD), aliases (cluster), ipsets with CIDR mgmt (cluster), refs.
- [x] **Pool management** — `proxmox pool`: list, show, create, update, delete. Wraps `/pools`.
- [x] **Shell completions** — `proxmox completion bash|zsh|fish`. Dynamic, introspects the parser tree.
- [x] **VM snapshot management** — `proxmox vm snapshot`: list, create, show, rollback, delete. Wraps `/nodes/{node}/qemu/{vmid}/snapshot`.
- [x] **QEMU guest agent interfaces** — `proxmox vm agent interfaces <vmid>`. Wraps `/nodes/{node}/qemu/{vmid}/agent/network-get-interfaces`.
- [x] **Streaming task logs** — `proxmox task log <upid> [--follow]`. Polls `/nodes/{node}/tasks/{upid}/log`.
- [x] **Global flag hint** — If user places `--output` / `--dry-run` / etc. after the resource, a hint suggests the correct order.
- [x] **User & permission management** — `proxmox user` (list/show/create/update/delete), `proxmox role` (list/show/create/update/delete), `proxmox acl` (list/show/add/delete). Wraps `/access/users`, `/access/roles`, `/access/acl`. ACL write requires `Permissions.Modify` (Administrator).
- [x] **VM cloud-init support** — `vm create` flags for citype, ciuser, cipassword, sshkeys, nameserver, searchdomain, cicustom + auto cloud-init drive creation. `vm cloudinit generate` for regeneration.
- [x] **VM disk import** — `vm create --import-from <storage:path>` imports an existing disk image as VM boot disk.
- [x] **Docs** — `docs/cloud-init.md` (cloud-init VM workflow), `docs/api-permissions.md` (minimum API privileges).
- [x] **Network management** — `proxmox network` (list, show). Wraps `/nodes/{node}/network[/{iface}]`. Shows bridges, bonds, VLANs, physical NICs with config details. Type filtering support.
- [x] **Backup (vzdump) management** — `proxmox backup` (list/show/create/delete/tasks/defaults). Wraps `/nodes/{node}/vzdump` and storage content endpoints. Supports snapshot/suspend/stop modes, compression, PBS.
- [x] **Ceph & disk management** — `proxmox ceph` (status, osd, log, disks). Cluster health, OSD-to-disk mapping, wearout tracking, Ceph logs.
- [x] **Config loader made read-only** — `auth login`/`auth clear` removed. `PROXMOX_CONFIG_DIR` env var for custom config path.
- [x] **Node system info** — `proxmox node subscription/dns/time/services/pci/netstat/config`. Read-only node inspection.
- [x] **Cluster log & options** — `proxmox cluster log [--limit N]` and `proxmox cluster options`.
- [x] **Storage status** — `proxmox storage status <storage> [--node]` for usage stats.
- [x] **API coverage doc** — `docs/api-coverage.md` tracking all implemented and remaining endpoints.
- [x] **VM disk import from URL** — `vm disk import --url` downloads, uploads, and imports a disk image from a remote URL in one command. `--image` for local PVE node paths.
- [x] **Cloud-init auto serial console** — `vm create` with cloud-init flags now auto-adds `serial0=socket` and `vga=serial0`, required by Debian generic cloud images.
- [x] **Self-update** — `proxmox update` checks PyPI for newer versions and upgrades via `uv tool install --reinstall`. `--check` for dry-run, `--pre` for pre-releases.

## v1.1 — Polish & Usability

- [x] **`--output table` column selection**
  - ``proxmox --output table --columns vmid,name,status vm list`` picks which columns appear.

- [x] **Color support in table output**
  - Status/state values are styled: green for running/active/ok, red for stopped/error, yellow for paused/suspended.

---

## v1.2 — VM & Container Lifecycle Gaps

High-impact VM/container workflows that exist in the Proxmox API but are missing from the CLI. Ordered by user value.

### Priority: HIGH

- [x] **VM clone**
  - `proxmox vm clone <vmid> --newid <id> [--name <name>] [--target-node <node>] [--target-storage <storage>] [--full] [--description <text>]`
  - Wraps `POST /nodes/{node}/qemu/{vmid}/clone`
  - Cloning from templates or golden images is a core homelab/admin workflow.
  - From piclaw: `vm.clone` workflow covers full/linked clone, target node/storage, optional description.

- [x] **VM migrate**
  - `proxmox vm migrate <vmid> --target <node> [--target-storage <storage>] [--online] [--with-local-disks]`
  - Wraps `POST /nodes/{node}/qemu/{vmid}/migrate`
  - Moving VMs between nodes is essential for maintenance and load balancing.
  - From piclaw: `vm.migrate` workflow with online flag and local disk migration.

- [x] **Backup restore**
  - `proxmox backup restore <volid> --vmid <id> [--node <node>] [--storage <storage>] [--target-storage <storage>]`
  - Wraps `POST /nodes/{node}/storage/{storage}/content` with archive restore.
  - Currently proxcli can create/list/delete backups but not restore them — a glaring asymmetry.
  - From piclaw: `backup.restore` workflow.

### Priority: MEDIUM

- [x] **VM template (convert to template)**
  - `proxmox vm template <vmid> [--node <node>]`
  - Wraps `POST /nodes/{node}/qemu/{vmid}/template`
  - Small addition but unlocks the clone-from-template workflow.
  - From piclaw: `vm.template.create` workflow.

- [x] **VM ISO attach / detach**
  - `proxmox vm iso attach <vmid> --iso-volume <volid> [--slot ide2] [--node <node>]`
  - `proxmox vm iso detach <vmid> [--slot ide2] [--node <node>]`
  - Wraps `PUT /nodes/{node}/qemu/{vmid}/config` with cdrom slot changes.
  - Exposing this as first-class actions is much more intuitive than raw config editing.
  - From piclaw: `vm.iso.attach` and `vm.iso.detach` workflows.

- [x] **VM IP quick-lookup**
  - `proxmox vm ip <vmid> [--node <node>]`
  - Combines guest agent network-get-interfaces (already implemented) into a one-shot "give me the IPs" command. Filter out loopback/link-local.
  - From piclaw: `vm.ip` and `lxc.ip` workflows.

- [x] **LXC IP quick-lookup**
  - `proxmox container ip <vmid> [--node <node>]`
  - Wraps `GET /nodes/{node}/lxc/{vmid}/interfaces`, extracting IPv4/IPv6 addresses.
  - From piclaw: `lxc.ip` workflow.

### Priority: LOW

- [x] **VM disk resize**
  - `proxmox vm disk resize <vmid> --disk <disk> --size <+N or N> [--node <node>]`
  - Wraps `PUT /nodes/{node}/qemu/{vmid}/resize`.
  - From piclaw: `vm.disk.resize` workflow.

- [x] **VM disk detach / remove**
  - `proxmox vm disk detach <vmid> --disk <disk> [--node <node>]`
  - `proxmox vm disk remove <vmid> --disk <disk> [--force] [--node <node>]`
  - From piclaw: `vm.disk.detach` and `vm.disk.remove` workflows.

- [x] **VM guest agent exec**
  - `proxmox vm agent exec <vmid> --command <cmd> [--args ...] [--input-data ...] [--shell posix|powershell]`
  - Extend the existing `vm agent` subcommand with an `exec` sub-action.
  - Wraps `POST /nodes/{node}/qemu/{vmid}/agent/exec` + polling for result.
  - From piclaw: `vm.agent.exec` workflow. Bounded command execution with base64 I/O decoding.

- [x] **VM guest agent OS info / FS info / users**
  - `proxmox vm agent osinfo <vmid>` — `GET /nodes/{node}/qemu/{vmid}/agent/get-osinfo`
  - `proxmox vm agent fsinfo <vmid>` — `GET /nodes/{node}/qemu/{vmid}/agent/get-fsinfo`
  - `proxmox vm agent users <vmid>` — `GET /nodes/{node}/qemu/{vmid}/agent/get-users`
  - From piclaw: `vm.agent.osinfo`, `vm.agent.fsinfo`, `vm.agent.users` workflows.

- [x] **Task wait (blocking poll)**
  - `proxmox task wait <upid> [--timeout <ms>] [--poll <ms>]`
  - Polls task status until completion, useful in scripts. pixlaw has both `task.wait` and `vm.wait_state`.

---

## v1.3 — Metrics & Monitoring

The piclaw proxmox addon has a rich `metrics.*` workflow family. proxcli has zero metrics support. This would be a killer feature for a CLI.

- [ ] **`proxmox metrics` top-level subcommand**
  - Wraps the RRD data API endpoints (`/nodes/{node}/rrddata`, `/nodes/{node}/qemu/{vmid}/rrddata`, `/nodes/{node}/storage/{storage}/rrddata`).
  - Common flags: `--timeframe hour|day|week|month|year` (default: `hour`), `--cf AVERAGE|MAX` (default: `AVERAGE`).

- [ ] **`proxmox metrics node <node> [--metric <name>]`**
  - Pulls node-level RRD series: CPU, memory, disk, network, load, etc.

- [ ] **`proxmox metrics vm <vmid> [--node <node>] [--metric <name>]`**
  - Pulls VM-level RRD series for a specific guest.

- [ ] **`proxmox metrics storage <storage> --node <node> [--metric <name>]`**
  - Pulls storage usage metrics over time.

- [ ] **Metrics output: chart / CSV / JSON**
  - `--output chart` could render a simple ASCII/Unicode sparkline in the terminal.
  - `--output csv` for data export into external tools.
  - `--output json` for programmatic consumers.

- [ ] **Guest comparison chart** (inspired by piclaw skill `proxmox-guest-compare-chart`)
  - A `proxmox compare` or `proxmox metrics compare` subcommand that fetches RRD series for two guests and renders an SVG chart or terminal comparison table.
  - The piclaw skill uses a Bun script to render SVG/CSV/JSON from normalized input — we could do this purely in Python.

---

## v1.4 — Storage Gaps

- [ ] **Storage create**
  - `proxmox storage create <name> --type <type> [--config key=value ...]`
  - Wraps `POST /storage`. Supports dir, nfs, lvmthin, zfspool, etc.
  - From piclaw: `storage.create` workflow. Config fields passed as a flat dict for backend-specific options.

- [ ] **Storage download-url** (server-side pull)
  - `proxmox storage download-url --node <node> --storage <storage> --url <url> --filename <name> [--content iso|vztmpl|import] [--checksum <sha256:...>] [--verify-tls]`
  - Wraps `POST /nodes/{node}/storage/{storage}/download-url`.
  - Lets you pull ISOs/templates directly into storage without agent-side upload.
  - From piclaw: `storage.download_url` workflow with checksum verification.

---

## v1.5 — Resource Coverage (existing TODO)

- [ ] **SDN (Software-Defined Networking)**
  - `proxmox sdn` subcommand: `zones`, `vnets`, `subnets`. Wraps `/cluster/sdn/*` endpoints.

- [ ] **HA (High Availability)**
  - `proxmox ha` subcommand: `status`, `groups`, `resources`. Wraps `/cluster/ha/*` endpoints.

- [ ] **Node syslog**
  - `proxmox node log <node> [--limit N]`
  - Wraps `GET /nodes/{node}/syslog`. Read node-level syslog entries (currently only `ceph log` exists).

---

## v2.0 — Multi-Cluster & Advanced

- [ ] **Multi-profile / multi-cluster support**
  - Support `--profile <name>` global flag to switch between multiple saved Proxmox endpoints. Config file format extended from single endpoint to a profiles dict. `proxmox auth login --profile homelab` and `proxmox auth login --profile work` coexist.

- [ ] **Batch / bulk operations**
  - `proxmox vm start --all-on-node pve01` (start all VMs on a node). `proxmox vm snapshot --vmid 100,101,102` (apply to multiple IDs).

- [x] **Config file templating**
  - ``vm create --file spec.yaml`` for declarative VM specs.  File format
    mirrors the native Proxmox VM config (flat key-value: ``name``,
    ``memory``, ``cores``, ``net0``, ``scsi0``, ``ciuser``, etc.).
  - ``vm show <id> --output yaml`` exports existing VM config in the
    same flat format (strips internal fields like ``digest``, ``vmgenid``).
    Export → edit → recreate loop.

- [ ] **Plugin system for custom commands**
  - Allow users to extend the CLI with custom subcommands via a plugins directory.

- [ ] **Dry-run diff mode**
  - `--dry-run` that shows what *would change* on the Proxmox side (e.g., before/after VM config diff) rather than just the HTTP request.

---

## Ideas (not yet scheduled)

- [ ] **Interactive mode / TUI**
  - A `proxmox tui` command that opens a terminal UI (like `htop` but for Proxmox resources). Low priority — the CLI is designed for automation first.

- [ ] **Webhook / event listener**
  - Subscribe to Proxmox cluster events and pipe them to a webhook or stdout for external monitoring.

- [ ] **Proxmox Backup Server (PBS) integration**
  - Separate subcommand or a companion tool (`proxbackup`?) for managing PBS instances via their API.

- [ ] **Terraform / Pulumi bridge**
  - Export current Proxmox state as Terraform HCL or Pulumi Python/TypeScript, enabling import into IaC.
