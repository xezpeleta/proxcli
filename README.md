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
# Authenticate (password-based)
proxmox auth login --url https://192.168.1.10:8006 --username root@pam --password your_password

# Or with an API token
proxmox auth login --url https://192.168.1.10:8006 --username root@pam --api-token 'root@pam!my-token=deadbeef...'

# Enable shell completions
source <(proxmox completion bash)          # bash
source <(proxmox completion zsh)           # zsh
proxmox completion fish | source           # fish  (or save to ~/.config/fish/completions/proxmox.fish)

# Check auth status
proxmox auth status

# List VMs
proxmox vm list

# Show a specific VM
proxmox vm show 100

# Create a VM
proxmox vm create --node pve01 --vmid 110 --memory 2048 --cores 2 --name webserver

# Start / stop / reboot
proxmox vm start 110
proxmox vm stop 110
proxmox vm reboot 110

# Delete (with purge)
proxmox vm delete 110 --purge
```

## Authentication

Credentials are stored in `~/.config/proxmox-cli/credentials.json` with restrictive permissions (`0600`).

### Auth methods

| Method | Command |
|---|---|
| Password | `proxmox auth login --url ... --username ... --password ...` |
| Password (stdin) | `echo "$PASS" \| proxmox auth login --url ... --username ... --password-stdin` |
| API token | `proxmox auth login --url ... --username ... --api-token 'user!tokenid=secret'` |

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
| `--output` | `json` | Output format: `json`, `table`, `yaml` |
| `--dry-run` | off | Print the API request without executing |
| `--insecure` | off | Skip TLS verification |
| `--timeout` | `30` | Request timeout in seconds |
| `--verbose` | off | Debug output to stderr |
| `--version` | — | Show version |

### Auth

```bash
proxmox auth login   # Save credentials
proxmox auth status  # Show current auth context
proxmox auth clear   # Remove saved credentials
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
proxmox vm create --node <node> --vmid <id> --memory <mb> [--cores <n>] [--name <name>] [--storage <name>] [--net <config>]
proxmox vm start <vmid> [--node <node>]
proxmox vm stop <vmid> [--node <node>]
proxmox vm reboot <vmid> [--node <node>]
proxmox vm suspend <vmid> [--node <node>]
proxmox vm resume <vmid> [--node <node>]
proxmox vm delete <vmid> [--node <node>] [--force] [--purge]

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
```

### Container (LXC)

```bash
proxmox container list [--node <node>]
proxmox container show <vmid> [--node <node>]
proxmox container create --node <node> --vmid <id> --ostemplate <tmpl> [--memory <mb>] [--cores <n>] [--storage <name>]
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
```

### Storage

```bash
proxmox storage list [--node <node>]
proxmox storage show <storage>
proxmox storage content <storage> [--node <node>]
proxmox storage upload --node <node> --storage <storage> --file <path> [--content-type iso|vztmpl|import]
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
```

### Task

```bash
proxmox task list [--node <node>]
proxmox task show <upid>
```

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

Every command emits valid JSON by default (stdout) and diagnostic messages on stderr. Exit codes follow Unix conventions.

```bash
# Dry-run to preview the API call
proxmox --dry-run vm create --node pve01 --vmid 110 --memory 1024

# Machine-parseable JSON output
proxmox --output json vm list | jq '.[] | {vmid, status}'

# Check exit code
proxmox vm show 999 || echo "VM not found"
```

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
