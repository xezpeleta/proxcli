# Project: Proxmox CLI (`proxmox`)

## Original Intent

Build a command-line tool to interact with a Proxmox VE node or cluster via its REST API from any computer, supporting all API-exposed features. The CLI must be human-friendly and also usable by AI agents. It provides a higher-level abstraction over the raw API.

## Refined Prompt

Create a Python CLI tool called `proxmox` that wraps the Proxmox VE REST API (see [API Viewer](https://pve.proxmox.com/pve-docs/api-viewer/index.html)) with a high-level, ergonomic command structure. The CLI must be installable via `uv` (Astral) and work on any machine that reaches the Proxmox host. Commands must follow a consistent, discoverable subcommand hierarchy (e.g., `proxmox <resource> <action>`). Credentials are persisted in a JSON config file under `~/.config/proxmox-cli/` (or `/etc/proxmox-cli/` for system-wide) and can alternatively be supplied via an `auth` subcommand. Output must be structured (JSON by default) with an optional human-readable table mode.

## Scope

- Full CLI wrapper for the Proxmox VE REST API (PVE 7.x / 8.x).
- Single binary-style entry point (`proxmox`) installable via `uv tool install` or pipx.
- Covers at minimum: authentication & session management, VM (QEMU), container (LXC), storage, networking, cluster, node, tasks/logs, and backup resources.
- Does **not** include a GUI, a local daemon, or a TUI (unless later requested).

## Functional Requirements

### Authentication & Configuration
- `proxmox auth --url <url> --username <user> --password <pass>`: save credentials to `~/.config/proxmox-cli/credentials.json`.
- `proxmox auth --url <url> --username <user> --api-token <token>`: token-based auth as well.
- `proxmox auth status`: display current auth context (host, user, token-used?).
- `proxmox auth clear`: remove stored credentials.
- Credentials loaded from `~/.config/proxmox-cli/credentials.json` (preferred) or `/etc/proxmox-cli/credentials.json` (system-wide fallback).
- Support `--url`, `--username`, `--password`, `--api-token` as global CLI flags that override file config for a single invocation.

### CLI Structure
- Top-level subcommands mirror Proxmox API resources:
  - `node` / `vm` / `container` / `storage` / `cluster` / `network` / `task` / `backup` / `user` / `pool`
- Each resource supports CRUD-like actions where applicable:
  - `list` / `create` / `show` / `update` / `delete`
- Example: `proxmox vm create --node pve01 --type qemu --vmid 100 --memory 2048 --cores 2`
- `--type` discriminates QEMU vs LXC when needed (default per subcommand).
- `--output json|table|yaml` global flag (default `json`).

### Output
- JSON (default): raw API response, pretty-printed.
- Table: key fields in an ASCII table (for human consumption).
- YAML: YAML-formatted equivalent.
- Machine-friendly: JSON output is always valid, no decorative text in JSON mode.

### AI-Agent Friendly
- Every command prints a valid JSON response when `--output json` is set (default).
- `--help` and `--help <subcommand>` print structured help (argparse-style).
- Exit codes follow Unix conventions (0 = success, non-zero for errors).
- Dry-run flag (`--dry-run`): prints the HTTP request that would be made without executing it.

### Additional Commands (coherent with examples)
- `proxmox vm list [--node <node>]`: list VMs, optionally filtered by node.
- `proxmox vm show <vmid>`: show details of a specific VM.
- `proxmox vm start <vmid>` / `stop <vmid>` / `reboot <vmid>` / `suspend <vmid>` / `resume <vmid>`.
- `proxmox vm delete <vmid>`: with `--force` and `--purge` flags.
- `proxmox container …`: analogous to `vm` but for LXC containers.
- `proxmox node status [<node>]`: show node status.
- `proxmox storage list`: list storages.
- `proxmox task list [--node <node>]` / `proxmox task show <upid>`.
- `proxmox cluster status`: cluster health and nodes.

## Non-Functional Requirements

- **Language**: Python 3.10+.
- **Tooling**: `uv` for dependency management and project tooling (`pyproject.toml`, `uv.lock`). Installable via `uv tool install .` (local) or from Git.
- **Dependencies**: minimal — `requests` or `httpx` for HTTP, `pydantic` for config/response modelling. Consider `rich` for table output. No heavy frameworks.
- **Error handling**: meaningful error messages on HTTP errors (display Proxmox error detail from response body).
- **Rate-limiting / timeout**: configurable timeout per request (default 30 s), retry on 5xx with backoff.
- **Performance**: CLI startup time under 300 ms for `--help`.
- **Testing**: unit tests for core logic, integration tests against a real Proxmox instance (optional, flagged).

## Constraints & Assumptions

### Assumptions Made
1. The primary config path is `~/.config/proxmox-cli/credentials.json` (XDG-style), consistent with modern CLI tools. Fallback `/etc/proxmox-cli/` for system-wide needs.
2. Users will interact with a single Proxmox endpoint at a time (no multi-cluster profiles in v1, but the config file format should not preclude adding profiles later).
3. The `vm` subcommand handles QEMU VMs; `container` handles LXC. The `--type` flag on `vm create` allows future expansion (e.g., LXC creation via `vm` subcommand), but for v1 we separate them.
4. TLS verification: default is `on`; add `--insecure` / `--tls-no-verify` flag for self-signed certificates common in homelab.
5. SSH tunneling or unix-socket connections are out of scope — HTTP/HTTPS only.
6. The tool exposes the most common API endpoints first; full coverage is a continuous goal, not a v1 requirement.
7. No interactive prompt for passwords — use `--password-stdin` or environment variable for scripting safety.
8. The CLI name `proxmox` is confirmed free on PyPI (verified; `proxmox-cli` is taken).

## Success Criteria

- A user can `uv tool install` the package from a Git repo or local path and immediately run `proxmox --help`.
- `proxmox auth --url … --username … --password …` persists credentials and subsequent commands work without re-authentication.
- `proxmox vm list --output table` returns a readable table of VMs.
- `proxmox vm create --node pve01 --vmid 110 --memory 1024 --cores 1` creates a VM and returns the UPID / success confirmation.
- All commands emit valid JSON by default; `--output table` provides a clean human-readable format.
- Invalid commands or API errors produce descriptive messages with non-zero exit codes.
- `--dry-run` mode works for any command, printing the exact HTTP method, URL, headers, and body.

## Open Questions

1. **API coverage**: Which resources to prioritize for v1? (node, vm, container, storage, cluster seems reasonable; defer SDN, HA, firewall, backup-server for later.)
2. **Profiles**: Should v1 support `--profile <name>` to switch between multiple Proxmox hosts? Or keep it single-endpoint and defer to v2?
3. **Password handling**: Accept `PROXMOX_PASSWORD` env var for CI/CD usage? Yes, as fallback if no config file and no `--password` flag.
4. **Output streaming**: Task output (`proxmox task log <upid>`) — stream-follow (`--follow`) vs one-shot?
5. **Shell completion**: Generate completions for bash/zsh/fish via e.g., `proxmox completion <shell>`? Nice-to-have for v1.
6. **Package name**: Confirmed: `proxmox` is free on PyPI. `proxmox-cli` was taken.
7. **HTTP library**: `requests` (blocking, simpler) vs `httpx` (async-capable, better for future streaming)? Recommend `httpx` for future-proofing.