# TODO

Planned improvements for future releases. Items are roughly ordered by priority.

---

## v1.1 — Polish & Usability

- [ ] **Shell completions**
  - Add `proxmox completion bash|zsh|fish` subcommand that emits a completion script. Use argparse's built-in completion or a lightweight generator. Makes tab-completion work for all subcommands and flags.

- [ ] **Streaming task logs (`--follow`)**
  - `proxmox task log <upid>` that streams task output in real time (like `tail -f`). Requires httpx streaming support (already viable — httpx is the chosen HTTP client).

- [ ] **Startup time optimization**
  - Current `proxmox --help` takes ~350ms. Lazy-load subcommand modules so only the requested resource's code is imported. Move `import rich`, `import yaml` inside formatter functions. Target: <200ms.

- [ ] **`--output table` column selection**
  - Allow `proxmox vm list --output table --columns vmid,name,status,mem` to pick which columns appear in the table.

- [ ] **Color support in table output**
  - Use `rich` styling for status values (green= running, red= stopped, yellow= suspended).

---

## v1.2 — Resource Coverage

- [ ] **Backup (`vzdump`) management**
  - `proxmox backup` subcommand: `list`, `create`, `show`, `delete`. Wrap `/nodes/{node}/vzdump` and `/nodes/{node}/storage/{storage}/content` for backup files.

- [ ] **User & permission management**
  - `proxmox user` subcommand: `list`, `show`, `create`, `update`, `delete`. Wraps `/access/users`, `/access/acl`, `/access/roles`.

- [ ] **Pool management**
  - `proxmox pool` subcommand: `list`, `show`, `create`, `update`, `delete`. Wraps `/pools`.

- [ ] **Network management**
  - `proxmox network` subcommand: `list`, `show`, `update` for bridges, bonds, VLANs. Wraps `/nodes/{node}/network`.

- [ ] **Firewall management**
  - `proxmox firewall` subcommand: `list`, `show`, `enable`, `disable`, `create rule`, `delete rule`. Wraps `/nodes/{node}/firewall`, `/cluster/firewall`.

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
