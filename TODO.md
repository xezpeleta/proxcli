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

## v1.1 — Polish & Usability

- [ ] **`--output table` column selection**
  - Allow `proxmox vm list --output table --columns vmid,name,status,mem` to pick which columns appear in the table.

- [ ] **Color support in table output**
  - Use `rich` styling for status values (green= running, red= stopped, yellow= suspended).

---

## v1.2 — Resource Coverage

- [ ] **SDN (Software-Defined Networking)**
  - `proxmox sdn` subcommand: `zones`, `vnets`, `subnets`. Wraps `/cluster/sdn/*` endpoints.

- [ ] **HA (High Availability)**
  - `proxmox ha` subcommand: `status`, `groups`, `resources`. Wraps `/cluster/ha/*` endpoints.

---

## v2.0 — Multi-Cluster & Advanced

- [ ] **Multi-profile / multi-cluster support**
  - Support `--profile <name>` global flag to switch between multiple saved Proxmox endpoints. Config file format extended from single endpoint to a profiles dict. `proxmox auth login --profile homelab` and `proxmox auth login --profile work` coexist.

- [ ] **Batch / bulk operations**
  - `proxmox vm start --all-on-node pve01` (start all VMs on a node). `proxmox vm snapshot --vmid 100,101,102` (apply to multiple IDs).

- [ ] **Config file templating**
  - Ability to define VM/container specs in a YAML/JSON file and create from it: `proxmox vm create --file my-vm.yaml`.

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

- [ ] **VM migration wizard**
  - `proxmox vm migrate <vmid> --to <target-node>` with progress tracking and live migration support.

- [ ] **Proxmox Backup Server (PBS) integration**
  - Separate subcommand or a companion tool (`proxbackup`?) for managing PBS instances via their API.

- [ ] **Terraform / Pulumi bridge**
  - Export current Proxmox state as Terraform HCL or Pulumi Python/TypeScript, enabling import into IaC.
