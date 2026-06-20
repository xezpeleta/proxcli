# proxmox

A CLI tool to interact with [Proxmox VE](https://www.proxmox.com/) nodes and clusters via the REST API.

Designed to be easy for humans (table output, ergonomic flags) and AI agents (structured JSON, strict exit codes, `--dry-run`). Provides a higher-level abstraction over the raw Proxmox API.

## Installation

Requires Python 3.10+ and [uv](https://docs.astral.sh/uv/).

```bash
# From PyPI
uv tool install proxmox

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
```

### Container (LXC)

```bash
proxmox container list [--node <node>]
proxmox container show <vmid> [--node <node>]
proxmox container create --node <node> --vmid <id> --ostemplate <tmpl> [--memory <mb>] [--cores <n>] [--storage <name>]
proxmox container start <vmid> [--node <node>]
proxmox container stop <vmid> [--node <node>]
proxmox container delete <vmid> [--node <node>] [--force] [--purge]
```

### Node

```bash
proxmox node list
proxmox node show <node>
proxmox node status [<node>]
```

### Storage

```bash
proxmox storage list [--node <node>]
proxmox storage show <storage>
proxmox storage content <storage> [--node <node>]
```

### Cluster

```bash
proxmox cluster status
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
