# Coding Agents with proxcli

proxcli is designed from the ground up to be **agent-native**. Its strict
CLI contract — JSON by default, predictable exit codes, and `--dry-run` mode —
makes it a reliable tool for AI coding agents working in Proxmox VE
environments.

## Why proxcli works for agents

AI coding agents (Claude Code, Codex CLI, Cursor Agent, Aider, etc.) need
tools they can trust. proxcli provides exactly that:

| Property | How proxcli delivers it |
|---|---|
| **Predictable output** | JSON is the default format — every command returns structured data. Agents never need to parse human-formatted tables. |
| **Reliable exit codes** | `0` on success, non-zero on failure. No ambiguous returns. |
| **Dry-run mode** | `--dry-run` prints the HTTP request without executing it. Agents can plan before acting. |
| **Least-privilege auth** | API tokens with scoped roles mean agents only get the permissions they need — never full root. |
| **Single binary** | `proxmox` is all an agent needs. No plugins, no shell pipelines, no dependencies to install at runtime. |
| **Self-documenting** | `proxmox --help` generates the full command tree from the parser. Agents can discover capabilities. |

## Sandbox setup

Create a dedicated Proxmox user and API token with **only the permissions
your agent needs**. Never give an agent a `root@pam` token.

### 1. Create a dedicated user

```bash
# In Proxmox UI: Datacenter → Permissions → Users → Add
# User: agent@pve
# Realm: Proxmox VE authentication server
```

### 2. Create a scoped role

Create a role with the minimum privileges your agent workflow requires:

```bash
proxmox role create proxcli-agent
```

In the UI, grant these privileges to `proxcli-agent`:

| Privilege | Why the agent needs it |
|---|---|
| `Sys.Audit` | List nodes, check cluster status, read tasks |
| `VM.Audit` | List VMs, show VM status and config |
| `VM.Allocate` | Create new VMs |
| `VM.PowerMgmt` | Start and stop VMs |
| `VM.Clone` | Clone existing VMs |
| `VM.Config.Disk` | Attach and resize disks |
| `VM.Config.Network` | Configure VM networking |
| `VM.Config.Cloudinit` | Set up cloud-init for new VMs |
| `VM.Config.CPU` | Set CPU count |
| `VM.Config.Memory` | Set memory |
| `VM.Snapshot` | Create and manage snapshots |
| `Datastore.Allocate` | Read and use storage |
| `Datastore.AllocateSpace` | Allocate disk space |
| `Pool.Audit` | View resource pools |

> **Principle**: Start with the absolute minimum. Add permissions only when
> the agent hits a 403. Use `proxmox auth check` to verify.

### 3. Create an API token

```bash
# In Proxmox UI: Datacenter → Permissions → API Tokens → Add
# User: agent@pve
# Token ID: agent-token
# ☑ Privilege Separation
```

Then assign `proxcli-agent` role to the token at the appropriate path:

```bash
proxmox acl add / --roles proxcli-agent --tokenid agent-token --users agent@pve
```

### 4. Write the credentials file

```bash
mkdir -p ~/.config/proxmox-cli && chmod 700 ~/.config/proxmox-cli

cat > ~/.config/proxmox-cli/credentials.json <<'EOF'
{
  "url": "https://your-pve.example.com:8006",
  "username": "agent@pve",
  "auth_method": "api_token",
  "api_token_id": "agent-token",
  "api_token_secret": "deadbeef-dead-beef-dead-beefdeadbeef",
  "verify_tls": false
}
EOF

chmod 600 ~/.config/proxmox-cli/credentials.json
```

Verify:

```bash
proxmox auth status
proxmox auth check
```

## Agent workflow examples

### Deploy a test VM

```bash
# Agent plans first
proxmox --dry-run vm create \
  --node pve01 --memory 1024 --cores 1 --name test-env

# Agent executes
proxmox --output json vm create \
  --node pve01 --memory 1024 --cores 1 --name test-env
```

### Snapshot before risky change

```bash
proxmox --output json vm snapshot create 100 pre-change
# {"data": "UPID:pve01:000A1B2C:..."}

# ... make changes ...

# Rollback if needed:
proxmox --output json vm snapshot rollback 100 pre-change
```

### Clean up old test VMs

```bash
# List all VMs
vms=$(proxmox --output json vm list)

# Filter by name pattern (agent-side logic)
# For each test VM:
proxmox vm stop <vmid>
proxmox vm delete <vmid>
```

## Dry-run mode in detail

`--dry-run` prints the exact HTTP request proxcli would make, without
sending it to the server:

```bash
$ proxmox --dry-run vm start 100
POST https://192.168.1.10:8006/api2/json/nodes/pve01/qemu/100/status/start
Headers:
  Authorization: PVEAPIToken=agent@pve!agent-token=...
  Accept: application/json
Body: (none)
```

This is invaluable for agents because:
- They can **verify** what they're about to do before doing it
- They can **debug** permission issues (dry-run shows the exact endpoint)
- They can present the plan to a human for approval

## Prompt engineering for agents

Here's a recommended system prompt snippet for agents using proxcli:

```
You have access to `proxmox` — a CLI tool for Proxmox VE management.

Rules:
- Always use `--output json` to get machine-readable output.
- Use `--dry-run` first for any destructive action (create, start, stop, delete, snapshot).
- Exit code 0 means success. Non-zero means failure — read stderr for details.
- Never run `proxmox auth setup` — it requires Administrator privileges.
- API tokens have scoped permissions. If you get 403, don't escalate — report the missing permission.
- VM IDs are integers. Node names are hostnames. Both are positional arguments after the action.
- Use `--file` for declarative VM specs. Export existing configs with `proxmox --output yaml vm config <vmid>`.
```

## Guardrails

| Safeguard | Description |
|---|---|
| **No root token** | Create a dedicated token with `proxcli-agent` role, not `root@pam` |
| **Privilege Separation** | Check the box when creating the token. Assign roles directly to the token, not inherited from the user. |
| **Dry-run first** | Every destructive command should go through `--dry-run` before execution |
| **JSON output** | Always `--output json` — agents should never scrape human-formatted tables |
| **Credentials file permissions** | `chmod 600` on the credentials file. Never commit it to version control. |
| **Audit trail** | All agent actions go through Proxmox's task log. If something breaks, `proxmox task list` tells you exactly what happened. |

## Testing agent permissions

Verify your agent's effective permissions:

```bash
proxmox auth check
```

Test a specific action:

```bash
proxmox --dry-run vm create --node pve01 --memory 512 --cores 1
```

If any privilege is missing, Proxmox returns a **403 Forbidden**.
