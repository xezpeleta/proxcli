# Agent Guide

A concise reference for AI agents (and humans driving them) using **proxcli**.
The package installs two binaries — `proxmox` and `proxcli` — they are identical.

## Mental model

```
proxmox <resource> <action> [id] [--flags]
```

- Resources are nouns: `vm`, `container`, `node`, `storage`, `cluster`, `task`, `pool`, `network`, `ceph`, `backup`, `acl`, `user`, `role`, `auth`, `api`, `update`.
- Actions are verbs: `list`, `show`, `create`, `start`, `stop`, `delete`, …
- Identifiers (vmid, node name, snapshot name, …) are **positional** and come after the action.
- `--node` is optional for read commands — if you omit it, the CLI finds the node for you.
- Output is **JSON by default** on stdout; diagnostics go to stderr. Exit codes are Unix-conventional.

## Finding things

```bash
proxmox vm list --name unifi        # case-insensitive substring; returns vmid + node
proxmox container list --name dns   # same for LXC
proxmox vm list --node pve01        # scope to one node
proxmox node list                   # all nodes
proxmox storage list
```

Every VM/container record carries a **bare `node`** field (plus `_node` for backward compatibility). Use it for the next command's `--node`.

## Bootstrapping credentials (`auth setup`)

`proxmox auth setup` defaults to **manual** mode — it prints the flat
`pveum`/`pvesh` commands to run on a Proxmox node as `root`. No SSH access is
required. For an agent without node-shell access, request the JSON form and
hand the commands to the operator:

```bash
# Emit the pveum/pvesh commands + a credentials.json template (no prompts):
proxmox auth setup --non-interactive --json
```

The operator runs the commands on a node, captures the token secret from the
`pvesh` output, and writes `credentials.json` (or re-runs interactively to
paste the secret). For full automation when the agent **does** have SSH access
to a node as `root@pam`, use `--auto`:

```bash
proxmox auth setup --auto --host pve01.lan --non-interactive --json
```

Verify afterwards with `proxmox auth status --permissions`.

## The `node` field (important)

Read responses include **both** `node` and `_node`. Prefer `node`:

```json
{"vmid": 100, "name": "unifi", "status": "running", "node": "pve01", "_node": "pve01"}
```

If a record has no `node`, it's a cluster-scoped resource (storage, pool, …) that doesn't live on a single node.

## Global flags — placement

Global flags may appear **before OR after** the subcommand. Both work:

```bash
proxmox vm list --dry-run
proxmox --dry-run vm list
```

The CLI relocates them internally. The set: `--dry-run`, `--output`, `--columns`,
`--insecure`, `--verbose`, `--url`, `--username`, `--password`, `--api-token`,
`--password-stdin`, `--version`.

**Exception:** `--timeout` is **not** relocated, because `task wait` and
`vm agent exec` define their own `--timeout` with different units/meaning.
Put `--timeout` before the resource when you mean the HTTP request timeout.

## Output formats

| Format | When to use |
|---|---|
| `json` (default) | Structured parsing; safe to pipe to `jq`. |
| `yaml` | Line-oriented key:value — easiest to grep a single field. |
| `table` | Human reading. Pair with `--columns a,b,c` to pick columns. |
| `log` | One-line status summaries. |

`--columns` is **comma-separated** (not space): `--columns vmid,name,status`.
It works before or after the subcommand.

```bash
proxmox vm list --output yaml
proxmox vm list --output table --columns vmid,name,status
```

## Dry-run

`--dry-run` prints the HTTP method, full URL, headers, and request body, then
exits **without** calling the API. Use it to verify a write command before
running it for real.

```bash
proxmox --dry-run vm create --node pve01 --vmid 110 --memory 2048 --name app01
```

## Async tasks and snapshots

Proxmox write operations return a **UPID** (task tracker) and run asynchronously.

- **`vm snapshot create`** returns the UPID with a hint by default:

  ```json
  {"data": "UPID:pve01:…", "async": true, "hint": "Task is async. Poll with: proxmox task wait UPID:pve01:…"}
  ```

- Add **`--wait`** to block until the snapshot finishes (returns `result: ok`/`error`):

  ```bash
  proxmox vm snapshot create 100 pre-update --wait
  ```

- Add **`--if-not-exists`** to make snapshot create idempotent (no-op if it exists):

  ```bash
  proxmox vm snapshot create 100 pre-update --if-not-exists --wait
  ```

- Block on **any** UPID with `task wait`:

  ```bash
  proxmox task wait UPID:pve01:00000001:00000001:00000001:vzdump::root@pam:
  ```

## `vm agent exec` — running commands inside a VM

Pass `--` before the guest command so flags after it are positional, not parsed:

```bash
proxmox vm agent exec 100 --shell -- ls -la /etc
proxmox vm agent exec 100 --shell -- bash -c 'uptime; df -h'
```

(`--shell` runs via the guest agent's shell; `--` protects `-la` etc. from the CLI parser.)

## Common task recipes

```bash
# Lifecycle
proxmox vm start 100 && proxmox vm stop 100
proxmox vm reboot 100
proxmox vm show 100

# Snapshots
proxmox vm snapshot list 100
proxmox vm snapshot create 100 pre-update --wait --if-not-exists
proxmox vm snapshot rollback 100 pre-update
proxmox vm snapshot delete 100 pre-update

# Find a VM's IP (via guest agent)
proxmox vm ip 100
proxmox vm agent interfaces 100

# Containers
proxmox container list --name dns
proxmox container start 200
proxmox container show 200

# Nodes & cluster
proxmox node list
proxmox node show pve01
proxmox cluster status

# High Availability (read-only)
proxmox cluster ha status
proxmox cluster ha resources list
proxmox cluster ha resources show vm:100
proxmox cluster ha groups list

# SDN (read-only)
proxmox cluster sdn overview
proxmox cluster sdn zones list
proxmox cluster sdn vnets show vnet0
proxmox cluster sdn pending      # unapplied changes

# Storage
proxmox storage list
proxmox storage show local

# Tasks
proxmox task list
proxmox task wait UPID:pve01:…
```

## VM & container tags

Tags are safe inventory labels — they don't affect a running VM's runtime
behaviour, so they're safe to set on production machines.

```bash
# Add tags on create
proxmox vm create --node pve01 --memory 1024 --vmid 100 --tag web --tag prod
proxmox container create --node pve01 --vmid 200 --ostemplate ... --tag web

# Merge-add tags to an existing VM (preserves current tags, deduplicates)
proxmox vm set 100 --tag web --tag prod

# Remove all tags
proxmox vm set 100 --clear-tags
```

Tags appear in `vm show` / `container show` output under the `tags` key
(semicolon-separated, as Proxmox stores them).

## Read-only cluster inspection: HA & SDN

`cluster ha` and `cluster sdn` expose **read-only** views of High Availability
and Software-Defined Networking. Mutating operations (arm/disarm HA, apply SDN)
are intentionally omitted — they affect cluster fencing / live networking and
are unsafe for unattended use. Reach for `proxmox api POST …` with `--dry-run`
if you truly need them.

```bash
proxmox cluster ha status                 # current HA service status
proxmox cluster ha resources list         # HA-managed VMs/containers
proxmox cluster ha resources show vm:100  # detail (sid = vm:ID or ct:ID)
proxmox cluster ha groups list

proxmox cluster sdn overview
proxmox cluster sdn zones list
proxmox cluster sdn vnets show vnet0
proxmox cluster sdn pending               # unapplied changes
```

## Discovering the full API surface

- `proxmox --help` — top-level resources.
- `proxmox <resource> --help` — that resource's actions and flags.
- `proxmox <resource> <action> --help` — action-level flags (e.g. `proxmox vm create --help`).
- `proxmox api --help` — for endpoints not yet covered by a subcommand, make a raw call:
  `proxmox api get /nodes/pve01/status`.

## Zero-arg cheat sheet

Running `proxmox` with no arguments prints a short cheat sheet of the most
common patterns above (instead of the full `--help` dump).
