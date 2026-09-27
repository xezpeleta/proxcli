# Quick Start

Get proxcli up and running in under 5 minutes. This guide covers
installation, authentication, and your first commands.

## Installation

```bash
uv tool install proxcli
```

Or with `pip`:

```bash
pip install proxcli
```

Verify:

```bash
proxmox --version
```

## Authentication

proxcli supports three auth methods. The recommended approach is
**`auth setup`**, which creates a least-privilege API token for you.

### `auth setup` (recommended)

By default, `auth setup` prints the exact `pveum`/`pvesh` commands to run
on a Proxmox node as `root` — **no SSH access required**. Review the
commands, paste them into a root shell on a node, copy the token secret
from the `pvesh` output, and paste it back when proxcli prompts you
(it writes `credentials.json` for you):

```bash
proxmox auth setup --host pve.example.com
```

Add `--auto` to instead run the commands over SSH in one idempotent pass:

```bash
proxmox auth setup --host pve.example.com --auto
```

See [API Permissions & Least Privilege](#/docs/permissions) for what the
`proxcli-*` roles grant.

### API token (manual)

If you prefer to create the token by hand in the web UI:

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
proxmox vm list --output table --columns vmid,name,status,mem
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

## Raw API calls

For Proxmox endpoints not yet covered by dedicated subcommands, use
`proxmox api` to make authenticated direct API calls:

```bash
# GET
proxmox api GET /nodes/pve01/status

# PUT with JSON body
proxmox api PUT /nodes/pve01/qemu/100/config -d '{"memory": 4096}'

# POST from file
proxmox api POST /nodes/pve01/qemu -f vm-spec.json

# Pipe from stdin
echo '{"memory": 4096}' | proxmox api PUT /nodes/pve01/qemu/100/config
```

This reuses the same authentication as the rest of proxcli — no need to manage
API tokens manually with `curl`.
