# proxcli

A CLI tool to interact with [Proxmox VE](https://www.proxmox.com/) nodes and clusters via the REST API.

Designed to be easy for humans (table output, ergonomic flags) and AI agents (structured JSON, strict exit codes, `--dry-run`). Provides a higher-level abstraction over the raw Proxmox API.

## Installation

Requires Python 3.10+ and [uv](https://docs.astral.sh/uv/).

```bash
# From PyPI
uv tool install proxcli

# From Git
uv tool install git+https://github.com/xezpeleta/proxcli.git

# From local checkout
uv tool install .
```

## Quickstart

```bash
# Default (manual): print the pveum/pvesh commands to run on a node as root.
# No SSH access required — review the commands, run them on a Proxmox node,
# then paste the token secret back when prompted (writes credentials.json):
proxmox auth setup

# Automatic over SSH (needs SSH key or sshpass to a node as root@pam):
#    proxmox auth setup --auto --host pve01.lan
#    → creates the recommended proxcli roles, an API token, and ACLs on the node
#    → writes the token to ~/.config/proxmox-cli/credentials.json (mode 0600)
# Preview the SSH script without changing anything:
#    proxmox auth setup --auto --host pve01.lan --dry-run
# Password auth (needs sshpass installed):
#    proxmox auth setup --auto --host pve01.lan --ssh-password-stdin

# Check auth status
proxmox auth status

# List VMs
proxmox vm list

# Show a specific VM
proxmox vm show 100
```

Prefer to write the config file by hand? See [Manual config file](#manual-config-file) below.

```bash
# Enable shell completions
source <(proxmox completion bash)          # bash
source <(proxmox completion zsh)           # zsh
proxmox completion fish | source           # fish  (or save to ~/.config/fish/completions/proxmox.fish)

# Create a VM (CLI flags)
proxmox vm create --node pve01 --vmid 110 --memory 2048 --cores 2 --name webserver

# Create a VM from a YAML file (declarative, version-controlled)
proxmox vm create --file my-vm.yaml

# Export an existing VM config as a YAML template
proxmox --output yaml vm config 112 > my-vm.yaml

# Start / stop / reboot
proxmox vm start 110
proxmox vm stop 110
proxmox vm reboot 110

# Delete (with purge)
proxmox vm delete 110 --purge
```

## Authentication

Credentials are stored in `~/.config/proxmox-cli/credentials.json` with restrictive permissions (`0600`). A system-wide config at `/etc/proxmox-cli/credentials.json` is also supported (checked after the user-level path).

### Recommended: `auth setup`

`proxmox auth setup` has two modes:

- **`manual` (default)** — prints the flat `pveum`/`pvesh` commands to run on a Proxmox node as `root`. No SSH access is required: review the commands, paste them into a root shell on a node, copy the token secret from the `pvesh` output, then paste it back when proxcli prompts you (it writes `credentials.json` for you). Add `--non-interactive` (or `--no-write`) to instead get a `credentials.json` template with no prompt.
- **`ssh` (`--auto` or `--via ssh`)** — SSHes into a Proxmox node as `root@pam` and, in one idempotent pass, creates the `proxcli-*` roles, an API token, and the ACLs — then writes the token secret to `credentials.json` for you.

```bash
# Default (manual) — no SSH needed, review and run the commands on a node:
proxmox auth setup
# Non-interactive manual (agents/scripts): print commands + a credentials template
proxmox auth setup --non-interactive --json

# Automatic over SSH (key auth by default):
proxmox auth setup --auto --host pve01.lan
# Password auth (requires sshpass):
proxmox auth setup --auto --host pve01.lan --ssh-password-stdin
# Preview the SSH script without touching the node:
proxmox auth setup --auto --host pve01.lan --dry-run
```

Options: `--pve-user` (default `root@pam`), `--token-name` (default `proxcli`), `--privsep/--no-privsep` (default on — privilege separation), `--regenerate` (rotate the token secret), `--force` (overwrite an existing `credentials.json`), `--no-write`, `--api-url` (the URL written to `credentials.json`; derived from `--host` if omitted).

The legacy `--via api` path uses an existing Administrator token over the REST API to create roles + ACLs only (it cannot capture or write the token secret). Prefer the default `manual` mode or `--auto`.

### Manual config file

If you prefer to hand-edit credentials, create `~/.config/proxmox-cli/credentials.json` (chmod 600):

```json
{
  "url": "https://192.168.1.10:8006",
  "username": "root@pam",
  "auth_method": "api_token",
  "api_token_id": "my-token",
  "api_token_secret": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "verify_tls": false
}
```

For password auth, use `"auth_method": "password"` with a `"password"` field instead of `api_token_id` / `api_token_secret`.

### Override credentials per command

```bash
proxmox --url https://other-pve:8006 --username admin@pam --password pass123 vm list
```

### Environment variable

```bash
export PROXMOX_PASSWORD=mysecret
proxmox vm list --username root@pam --url https://pve:8006
```

### Self-signed certificates

```bash
proxmox --insecure vm list
```

## Command Reference

### Global flags

| Flag | Default | Description |
|---|---|---|
| `--url` | (config file) | Proxmox API URL |
| `--username` | (config file) | Username |
| `--password` | — | Password |
| `--password-stdin` | — | Read password from stdin |
| `--api-token` | — | API token (`user!tokenid=secret`) |
| `--output` | `json` | Output format: `json`, `table`, `yaml`, `log` |
| `--json` | off | Shorthand for `--output json` (accepted for ergonomics; default is already json) |
| `--columns` | all | Columns to display in table output (e.g. `--columns vmid,name,status`) |
| `--dry-run` | off | Print the API request without executing |
| `--insecure` | off | Skip TLS verification |
| `--timeout` | `30` | Request timeout in seconds |
| `--verbose` | off | Debug output to stderr |
| `--version` | — | Show version |

### Auth

```bash
proxmox auth status            # Show current auth context
proxmox auth status --permissions  # + effective permissions from API
proxmox auth setup             # Default: print pveum/pvesh commands to run on a node (no SSH needed)
proxmox auth setup --auto --host pve01  # Run automatically over SSH as root@pam (writes credentials.json)
proxmox auth setup --dry-run   # Preview the commands without changing anything
proxmox auth check             # Live permission test table (39 checks)
```

### Self-update

```bash
proxmox update              # Check for updates and install the latest version
proxmox update --check      # Only check (no install)
proxmox update --pre        # Include pre-release versions
```

### Completion

```bash
proxmox completion bash    # Emit bash completion script
proxmox completion zsh     # Emit zsh completion script
proxmox completion fish    # Emit fish completion script
```

Add to your shell's rc file:

```bash
# bash (~/.bashrc)
source <(proxmox completion bash)

# zsh (~/.zshrc)
source <(proxmox completion zsh)

# fish (~/.config/fish/completions/proxmox.fish)
proxmox completion fish > ~/.config/fish/completions/proxmox.fish
```

### VM (QEMU)

```bash
proxmox vm list [--node <node>]
proxmox vm show <vmid> [--node <node>]
proxmox vm config <vmid> [--node <node>]     # clean config, ready for --file import
proxmox vm create --node <node> --memory <mb> [--vmid <id>] [--cores <n>] \
    [--name <name>] [--cdrom <iso>] [--net <config>] [--disk <size>] \
    [--scsihw <type>] [--bios seabios|ovmf] [--machine <type>] [--boot <order>] \
    [--tag <tag>] [--file <spec.yaml>]     # --tag is repeatable; --file = declarative spec
proxmox vm set <vmid> [--node <node>] [--ciuser <user>] [--ipconfig0 <cfg>] \
    [--sshkeys <file|keys>] [--option key=value] [--tag <tag>] [--clear-tags]   # tags: merge-add or clear
proxmox vm start <vmid> [--node <node>]
proxmox vm stop <vmid> [--node <node>]
proxmox vm reboot <vmid> [--node <node>]
proxmox vm suspend <vmid> [--node <node>]
proxmox vm resume <vmid> [--node <node>]
proxmox vm delete <vmid> [--node <node>] [--force] [--purge]

# VM snapshots
proxmox vm snapshot list <vmid> [--node <node>]
proxmox vm snapshot create <vmid> <snapname> [--description <text>] [--vmstate 1]
proxmox vm snapshot show <vmid> <snapname> [--node <node>]
proxmox vm snapshot rollback <vmid> <snapname> [--start 1]
proxmox vm snapshot delete <vmid> <snapname> [--force 1]

# VM guest agent
proxmox vm agent interfaces <vmid> [--node <node>]

# VM firewall
proxmox vm firewall options <vmid> [--node <node>]
proxmox vm firewall enable <vmid> [--node <node>]
proxmox vm firewall disable <vmid> [--node <node>]
proxmox vm firewall policy <vmid> --in-policy ACCEPT --out-policy DROP [--node <node>]
proxmox vm firewall rules list <vmid> [--node <node>]
proxmox vm firewall rules add <vmid> --action ACCEPT --dport 22 --proto tcp [--source <cidr>] [--comment <text>]
proxmox vm firewall rules show <vmid> <pos>
proxmox vm firewall rules update <vmid> <pos> --action DROP
proxmox vm firewall rules delete <vmid> <pos>
proxmox vm firewall refs <vmid> [--type alias|ipset|group]

# VM disk management
proxmox vm disk import <vmid> --image /path/to/image.qcow2 [--disk scsi0] [--storage rbd_ssd]
proxmox vm disk import <vmid> --url https://.../image.qcow2 [--disk scsi0] [--storage rbd_ssd]
proxmox vm disk resize <vmid> --disk scsi0 --size +10G
proxmox vm disk detach <vmid> --disk scsi0
proxmox vm disk remove <vmid> --disk scsi0 [--force]
```

#### Declarative VM specs (`--file`)

Create VMs from YAML files using native Proxmox VM config keys.
CLI flags override file values — ideal for infrastructure-as-code:

```yaml
# webserver.yaml
name: webserver
node: sanmarko
memory: 4096
cores: 2
net0: "virtio,bridge=vmbr0,tag=99"
import_from: local:import/debian-12-genericcloud-amd64.qcow2
citype: nocloud
ciuser: debian
cipassword: ChangeMe123!
sshkeys: ~/.ssh/id_rsa.pub
```

```bash
# Create from file
proxmox vm create --file webserver.yaml

# Override specific values
proxmox vm create --file webserver.yaml --name staging --memory 8192

# Export existing VM as YAML template
proxmox --output yaml vm config 112 > template.yaml
```

See [docs/cloud-init.md](docs/cloud-init.md) for cloud-init specifics.

### Container (LXC)

```bash
proxmox container list [--node <node>]
proxmox container show <vmid> [--node <node>]
proxmox container create --node <node> --vmid <id> --ostemplate <tmpl> [--memory <mb>] [--cores <n>] [--storage <name>] [--tag <tag>]
proxmox container start <vmid> [--node <node>]
proxmox container stop <vmid> [--node <node>]
proxmox container delete <vmid> [--node <node>] [--force] [--purge]

# Container firewall
proxmox container firewall options <vmid> [--node <node>]
proxmox container firewall enable <vmid> [--node <node>]
proxmox container firewall disable <vmid> [--node <node>]
proxmox container firewall policy <vmid> --in-policy ACCEPT --out-policy DROP
proxmox container firewall rules list <vmid> [--node <node>]
proxmox container firewall rules add <vmid> --action ACCEPT --dport 22 --proto tcp
proxmox container firewall rules show <vmid> <pos>
proxmox container firewall rules update <vmid> <pos> --action DROP
proxmox container firewall rules delete <vmid> <pos>
proxmox container firewall refs <vmid> [--type alias|ipset|group]
```

### Node

```bash
proxmox node list
proxmox node show <node>
proxmox node status [<node>]

# Node firewall
proxmox node firewall options <node>
proxmox node firewall enable <node>
proxmox node firewall disable <node>
proxmox node firewall policy <node> --in-policy ACCEPT --out-policy DROP
proxmox node firewall rules list <node>
proxmox node firewall rules add <node> --action ACCEPT --dport 22 --proto tcp
proxmox node firewall rules show <node> <pos>
proxmox node firewall rules update <node> <pos> --action DROP
proxmox node firewall rules delete <node> <pos>
proxmox node firewall refs <node> [--type alias|ipset|group]

# Node system info
proxmox node subscription <node>    # subscription status
proxmox node dns <node>             # DNS configuration
proxmox node time <node>            # timezone and local time
proxmox node services <node>        # systemd service status
proxmox node pci <node>             # PCI device inventory
proxmox node netstat <node>         # network statistics
proxmox node config <node>          # node configuration
```

### Storage

```bash
proxmox storage list [--node <node>]
proxmox storage show <storage>
proxmox storage content <storage> [--node <node>]
proxmox storage status <storage> [--node <node>]   # usage stats
proxmox storage upload --node <node> --storage <storage> --file <path> [--content-type iso|vztmpl|import]
```

### Network

```bash
proxmox network list [--node <node>] [--type bridge|bond|eth|vlan|...]
proxmox network show <iface> [--node <node>]
```

List and inspect network interfaces (bridges, bonds, VLANs, physical NICs)
on any node.  Use ``--type`` to filter by interface type.

```
$ proxmox network list --node sanmarko --type vlan
vmbr0.10   cidr=192.168.10.14/24   gateway=192.168.10.1
vmbr0.11   cidr=192.168.11.47/24
```

### Pool

```bash
proxmox pool list
proxmox pool show <poolid>
proxmox pool create <poolid> [--comment <text>]
proxmox pool update <poolid> [--comment <text>] [--allow-delete]
proxmox pool delete <poolid>
```

### Cluster

```bash
proxmox cluster status
proxmox cluster log [--limit N]              # cluster-wide log
proxmox cluster options                      # migration, keyboard, mac_prefix, tags

# Ceph management
proxmox ceph status                          # cluster health: OSDs, PGs, usage, monitors
proxmox ceph osd [--node <node>]             # OSDs: disk health + wearout + capacity utilization (used%, reweight, status)
proxmox ceph pool [--node <node>]            # pools: used%, max_avail, target_size_ratio, PGs (nearfull signals)
proxmox ceph log [--node <node>] [--limit N] # recent Ceph log entries
proxmox ceph disks [--node <node>]           # physical disks: device, model, health, wearout, OSD

# Cluster firewall
proxmox cluster firewall options
proxmox cluster firewall enable
proxmox cluster firewall disable
proxmox cluster firewall policy --in-policy ACCEPT --out-policy DROP
proxmox cluster firewall rules                                      # list (shorthand)
proxmox cluster firewall rules list                                 # list (explicit)
proxmox cluster firewall rules add --action ACCEPT --dport 22 --source 10.0.0.0/8
proxmox cluster firewall rules show <pos>
proxmox cluster firewall rules update <pos> --action DROP
proxmox cluster firewall rules delete <pos>
proxmox cluster firewall aliases                                    # list (shorthand)
proxmox cluster firewall aliases add <name> --cidr 10.0.0.0/24 --comment "web tier"
proxmox cluster firewall aliases delete <name>
proxmox cluster firewall ipsets                                     # list (shorthand)
proxmox cluster firewall ipsets add <name> --comment "trusted hosts"
proxmox cluster firewall ipsets show <name>
proxmox cluster firewall ipsets delete <name>
proxmox cluster firewall ipsets add-cidr <name> --cidr 192.168.1.0/24
proxmox cluster firewall ipsets delete-cidr <name> --cidr 192.168.1.0/24
proxmox cluster firewall refs [--type alias|ipset|group]

# High Availability (read-only — mutating ops are intentionally omitted)
proxmox cluster ha status                     # current HA service status
proxmox cluster ha config                     # HA manager configuration
proxmox cluster ha resources list             # HA-managed VMs/containers
proxmox cluster ha resources show vm:100       # resource detail (sid = vm:ID or ct:ID)
proxmox cluster ha groups list                # HA node groups
proxmox cluster ha groups show <group>

# Software-Defined Networking (read-only — apply/create omitted for safety)
proxmox cluster sdn overview                  # SDN status
proxmox cluster sdn pending                   # unapplied SDN changes
proxmox cluster sdn zones list
proxmox cluster sdn zones show <zone>
proxmox cluster sdn vnets list
proxmox cluster sdn vnets show <vnet>
proxmox cluster sdn controllers list
proxmox cluster sdn controllers show <controller>
proxmox cluster sdn subnets list
proxmox cluster sdn subnets show <subnet>
proxmox cluster sdn ipams                     # IPAM plugins (list)
proxmox cluster sdn dns                       # DNS plugins (list)
```

### Task

```bash
proxmox task list [--node <node>]
proxmox task show <upid>
proxmox task log <upid> [--follow]
```

`proxmox task log --follow` polls the log endpoint every second
and streams new lines until the task completes (like `tail -f`).
`cluster log --follow` and `ceph log --follow <node>` work the same way.

### Backup (vzdump)

```bash
proxmox backup list [--node <node>] [--storage <storage>] [--vmid <id>]
proxmox backup show <volid> [--node <node>] [--vmid <id>]
proxmox backup create [--node <node>] --vmid <id> --storage <storage> \
    [--mode snapshot|suspend|stop] [--compress 0|1|zstd] \
    [--bwlimit <kbps>] [--ionice <0-8>] [--prune-backups <spec>]
proxmox backup delete <volid> [--node <node>]
proxmox backup tasks [--node <node>] [--limit <n>]
proxmox backup defaults [--node <node>] [--storage <storage>]
```

Use `--all` instead of `--vmid` to back up all guests on a node.
Backup tasks can be monitored with `proxmox task log <upid> --follow`.

> **Backups are read-only by default.** The default `proxcli` roles omit
> `Datastore.Allocate` and `VM.Backup`, so `backup create` and `backup delete`
> return 403 out of the box. `list`, `show`, `tasks`, and `defaults` work.
> To enable create/delete, add those privileges to a custom role — see
> [`docs/api-permissions.md`](docs/api-permissions.md#backups-are-read-only-by-default).

### User

```bash
proxmox user list
proxmox user show <userid>
proxmox user create <userid> [--password <pw>] [--email <email>] \
    [--firstname <name>] [--lastname <name>] [--group <group>] [--disable]
proxmox user update <userid> [--password <pw>] [--email <email>] [--enable|--disable]
proxmox user delete <userid>
```

### Role

```bash
proxmox role list
proxmox role show <roleid>
proxmox role create <roleid> [--privs <priv1,priv2,...>]
proxmox role update <roleid> [--privs <priv1,priv2,...>]
proxmox role delete <roleid>
```

### ACL

```bash
proxmox acl list
proxmox acl show <path>
proxmox acl add <path> --roles <role> [--users <users>] [--groups <groups>] [--tokens <tokens>]
proxmox acl delete <path> [--roles <role>] [--users <users>] [--groups <groups>]
```

ACL write operations require the `Permissions.Modify` privilege
(Administrator role).

## Output Formats

### JSON (default)

```json
[
  {
    "vmid": 100,
    "name": "webserver",
    "status": "running",
    "cpu": 0.05,
    "mem": 2048
  }
]
```

### Table

```
┌──────┬───────────┬─────────┬───────┬──────┐
│ vmid │ name      │ status  │ cpu   │ mem  │
├──────┼───────────┼─────────┼───────┼──────┤
│ 100  │ webserver │ running │ 0.05  │ 2048 │
└──────┴───────────┴─────────┴───────┴──────┘
```

### YAML

```yaml
- vmid: 100
  name: webserver
  status: running
  cpu: 0.05
  mem: 2048
```

## AI Agent Usage

Every command emits valid JSON by default (stdout) and diagnostic messages on stderr. Exit codes follow Unix conventions. The package installs **two** binaries — `proxmox` and `proxcli` — use either.

See [`docs/agent-guide.md`](docs/agent-guide.md) for the full reference. Highlights:

```bash
# Find a VM by hostname -> returns its vmid + node in one call
proxmox vm list --name unifi

# Show a VM (node is auto-detected from the vmid; no --node needed)
proxmox vm show 100

# Every record carries a bare `node` field (and `_node` for back-compat),
# so the node you need for the next command is always in the output.

# Global flags work BEFORE or AFTER the subcommand — write what reads naturally:
proxmox vm list --dry-run
proxmox vm list --output yaml --columns vmid,name,status

# Snapshots are async: --wait blocks until done, --if-not-exists makes it idempotent.
# Without --wait the UPID is returned with a hint telling you how to poll.
proxmox vm snapshot create 100 pre-update --wait
proxmox vm snapshot create 100 pre-update --if-not-exists

# Block on any async task by its UPID:
proxmox task wait UPID:pve01:00000001:00000001:00000001:vzdump::root@pam:

# Dry-run to preview the API call (prints method, URL, headers, body):
proxmox --dry-run vm create --node pve01 --vmid 110 --memory 1024

# YAML output is the easiest to parse line-by-line:
proxmox --output yaml vm list | grep 'name:'

# --json is a shorthand for --output json (default). Works before or after the subcommand:
proxmox vm list --json

# Raw API escape hatch — reach any endpoint not yet covered by a subcommand.
# Browse known endpoint patterns first, then call the one you need:
proxmox api --list-endpoints --output table
proxmox api GET /nodes/pve01/ceph/pool
proxmox api PUT /nodes/pve01/qemu/100/config -d '{"memory": 4096}'

# Check exit code
proxmox vm show 999 || echo "VM not found"
```

Running `proxmox` with no arguments prints a short cheat sheet of these patterns.

### Global flag placement

Global flags (`--dry-run`, `--output`, `--columns`, `--insecure`, `--verbose`, `--url`, `--username`, `--password`, `--api-token`, `--json`) may appear **before or after** the subcommand — the CLI relocates them internally. One exception: `--timeout` is **not** relocated, because `task wait` and `vm agent exec` define their own `--timeout` with different units. Put `--timeout` before the resource when you mean the request timeout.

## Development

```bash
# Clone
git clone https://github.com/xezpeleta/proxcli.git
cd proxcli

# Install dev dependencies
uv sync

# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=proxmox --cov-report=term-missing

# Lint
uv run ruff check .

# Build
uv build
```

## License

MIT

## Firewall Rule Options

Firewall rules share the same flags across cluster, node, VM, and container. The `--macro` flag can be used as a shortcut for common services (e.g., `--macro SSH` sets up port 22/tcp).

| Flag | Values | Description |
|---|---|---|
| `--action` | `ACCEPT`, `DENY`, `REJECT` | Rule action (required for `add`) |
| `--type` | `in`, `out` | Traffic direction (default: `in`) |
| `--iface` | e.g. `net0` | Network interface |
| `--source` | CIDR | Source IP/CIDR |
| `--dest` | CIDR | Destination IP/CIDR |
| `--dport` | e.g. `80` or `8000-9000` | Destination port |
| `--sport` | e.g. `1024-65535` | Source port |
| `--proto` | `tcp`, `udp`, `icmp`, `any` | Protocol |
| `--macro` | e.g. `SSH`, `HTTP`, `HTTPS`, `Ping` | Pre-defined service macro |
| `--comment` | text | Comment / description |
| `--enable` | `0`, `1` | Enable the rule (default: `1`) |
| `--log` | `emerg`..`debug`, `nolog` | Log level |

Example:

```bash
# Allow SSH from a specific subnet
proxmox vm firewall rules add 100 --action ACCEPT --dport 22 --proto tcp --source 192.168.1.0/24 --comment "Admin SSH"

# Or use a macro
proxmox vm firewall rules add 100 --action ACCEPT --macro SSH --source 192.168.1.0/24
```
