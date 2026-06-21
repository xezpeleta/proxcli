# Quick Start

Get proxcli up and running in under 5 minutes. This guide covers
installation, authentication, and your first commands.

## Installation

```bash
pip install proxcli
```

Or with `uv`:

```bash
uv tool install proxcli
```

Verify:

```bash
proxmox --version
```

## Authentication

proxcli supports three auth methods. The recommended approach is an **API token**:

### API Token (recommended)

1.  In the Proxmox VE web UI, go to **Datacenter → Permissions → API Tokens**.
2.  Click **Add**, select a user (e.g. `root@pam`), and uncheck
    *Privilege Separation* to grant full access.
3.  Copy the **Token ID** and **Secret**.

Set them as environment variables:

```bash
export PROXMOX_URL=https://pve.example.com:8006
export PROXMOX_TOKEN_ID=root@pam!proxcli
export PROXMOX_TOKEN_SECRET=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

### Username + Password

```bash
export PROXMOX_URL=https://pve.example.com:8006
export PROXMOX_USERNAME=root@pam
# You will be prompted for a password, or:
echo $PASSWORD | proxmox --password-stdin vm list
```

### Credential overrides

All credentials can be passed as CLI flags, which take precedence over
environment variables:

```bash
proxmox --url https://pve.example.com:8006 \
  --api-token "root@pam!proxcli=xxxxxxxx" \
  vm list
```

## Your first commands

### List your nodes

```bash
proxmox node list
```

### List all VMs

```bash
proxmox vm list
```

### Show a VM

```bash
proxmox vm show 100
```

### List storage

```bash
proxmox storage list
```

### Check cluster status

```bash
proxmox cluster status
```

## Output formats

proxcli supports four output formats:

| Format  | Flag                    | Use case                          |
| ------  | ----------------------- | --------------------------------- |
| JSON    | `--output json`         | Default. Machine-readable output  |
| Table   | `--output table`        | Human-friendly terminal tables    |
| YAML    | `--output yaml`         | Declarative import/export         |
| Log     | `--output log`          | Real-time log streaming           |

```bash
proxmox vm list --output table
proxmox vm show 100 --output yaml
proxmox task log UPID:pve01:... --output log --follow
```

### Select columns

```bash
proxmox vm list --output table --columns vmid name status mem
```

## Next steps

-   [API Permissions & Least Privilege](#/docs/permissions) —
    Set up a restricted token for production use.
-   [Cloud-Init VMs](#/docs/cloud-init) — Create VMs with cloud-init from
    the CLI.
-   [Command Reference](#/docs/command-reference) — Full command listing.
-   [Coding Agents](#/docs/coding-agents) — Use proxcli as a sandbox
    for AI agents.
-   [Production Automation](#/docs/production) — Shell scripting,
    CI/CD, and monitoring patterns.
