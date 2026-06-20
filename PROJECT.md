# Project: Proxmox CLI (`proxmox`)

## Executive Summary

A Python CLI tool that wraps the Proxmox VE REST API with a high-level, discoverable subcommand structure (`proxmox <resource> <action>`). Designed to be equally usable by human operators (table output, ergonomic flags) and AI agents (structured JSON, strict exit codes, `--dry-run`). Installed via `uv tool install` and configured with a single `auth` command.

## Objective

Provide a single binary (`proxmox`) that can manage every aspect of a Proxmox VE node or cluster from any machine with network access — without requiring users to memorize API paths, craft curl commands, or manage session cookies manually.

## Target Users / Stakeholders

| Role | Need |
|---|---|
| **Homelab admins** | Quick VM/container lifecycle from terminal; replace clicking in the web UI. |
| **Sysadmins / SREs** | Scriptable provisioning, health checks, and automation via JSON output. |
| **AI coding agents** | Structured, predictable interface for autonomous infrastructure management. |
| **CI/CD pipelines** | Provision/destroy test VMs via non-interactive, env-var-based auth. |

## Scope

### In Scope (v1)
- Authentication: password and API token, persisted to XDG config.
- Resources: `vm` (QEMU), `container` (LXC), `node`, `storage`, `cluster`, `task`.
- Actions per resource: `list`, `create`, `show`, `update`, `delete`, plus resource-specific actions (`start`, `stop`, `reboot`, `suspend`, `resume`).
- Output formats: `json` (default), `table`, `yaml`.
- Global flags: `--output`, `--dry-run`, `--insecure` (skip TLS verify), `--timeout`.
- Auth override via CLI flags (`--url`, `--username`, `--password`, `--api-token`) and `PROXMOX_PASSWORD` env var.
- Token-based session management (Proxmox CSRF/`PVEAuthCookie`).
- `--help` for every command and subcommand.

### Out of Scope (v1)
- GUI, TUI, or web interface.
- SSH tunneling or Unix-socket transport.
- Multi-profile / multi-cluster switching.
- SDN, HA, firewall, backup-server API resources.
- Streaming task logs (`--follow` deferred).
- Shell completions (deferred to v1.1).

## Proposed Tech Stack

| Component | Choice | Rationale |
|---|---|---|
| **Language** | Python 3.10+ | User-specified; broad ecosystem for CLI and HTTP. |
| **Build / packaging** | `uv` + `pyproject.toml` | User-specified; fast resolver, installs as a standalone tool. |
| **HTTP client** | `httpx` | Modern, async-capable (future streaming), connection pooling, timeout control. |
| **CLI framework** | `argparse` (stdlib) | No extra dependency; sufficient for the subcommand hierarchy. |
| **Config model** | `pydantic` v2 | Strict validation of credentials file and API responses; type-safe. |
| **Output formatting** | `rich` | Beautiful tables and colored output for human mode; optional but recommended. |
| **PyYAML** | `pyyaml` | YAML output format support. |
| **Testing** | `pytest` + `pytest-httpx` | Unit tests with mocked HTTP; integration suite flagged via pytest marker. |

**Total runtime dependencies:** `httpx`, `pydantic`, `rich`, `pyyaml` (4 packages).

## Architecture Overview

```
proxmox (entry point)
│
├─ cli/                          # argparse setup
│   ├─ main.py                   # Root parser + global flags
│   ├─ vm.py                     # `proxmox vm` subparser
│   ├─ container.py
│   ├─ node.py
│   ├─ storage.py
│   ├─ cluster.py
│   ├─ task.py
│   └─ auth.py
│
├─ client/
│   ├─ client.py                 # ProxmoxClient: session, auth, request dispatch
│   ├─ auth.py                   # Ticket/token acquisition, CSRF header injection
│   └─ exceptions.py             # ProxmoxAPIError, AuthError, Timeout
│
├─ config/
│   ├─ config.py                 # ConfigLoader: read/write credentials.json
│   └─ models.py                 # Pydantic models: Credentials, ConnectionProfile
│
├─ output/
│   ├─ formatter.py              # Dispatch: json | table | yaml
│   ├─ json_fmt.py
│   ├─ table_fmt.py
│   └─ yaml_fmt.py
│
└─ utils/
    ├─ helpers.py                # Validators, URL builders
    └─ logging.py                # Structured stderr logging (--verbose)
```

### Data Flow

```
User command
  → argparse parses (global + resource + action + flags)
  → ConfigLoader loads credentials (file → env → CLI flags)
  → ProxmoxClient acquires ticket/token, stores cookie
  → ProxmoxClient dispatches HTTP request (method, path, params, body)
  → Response parsed into dict/list
  → OutputFormatter renders in requested format → stdout
  → Exit code 0 on success, non-zero on failure
```

### Auth Flow

```
1. If API token provided → base64 encode, set Authorization header directly.
2. If password provided → POST /api2/json/access/ticket → extract ticket + CSRF token.
3. Subsequent requests: include Cookie header (PVEAuthCookie) and CSRFPreventionToken.
4. Token/ticket cached in memory for process lifetime; not re-acquired per command.
```

## Milestones / Phases

### Phase 1: Skeleton & Auth (Week 1)
- Project scaffolding with `uv` (`uv init`, `pyproject.toml`, dev deps).
- `ProxmoxClient` with ticket-based auth.
- `ConfigLoader` read/write for `credentials.json`.
- `proxmox auth` subcommand (login, status, clear).
- Global flags: `--url`, `--username`, `--password`, `--api-token`, `--output`, `--dry-run`, `--insecure`.

### Phase 2: Core Resources (Week 2)
- `vm` subcommand: `list`, `show`, `create`, `start`, `stop`, `reboot`, `suspend`, `resume`, `delete`.
- `node` subcommand: `list`, `show`, `status`.
- `cluster status`.

### Phase 3: Remaining Resources & Output (Week 3)
- `container`: `list`, `show`, `create`, `start`, `stop`, `delete`.
- `storage`: `list`, `show`, `content`.
- `task`: `list`, `show`.
- All three output formatters (JSON, table, YAML).
- Error formatting with Proxmox error body extraction.

### Phase 4: Polish & Release (Week 4)
- Retry with exponential backoff on 5xx.
- `--timeout` flag implementation.
- Man page or README with full usage examples.
- Tests: ≥80% coverage on client, config, and output modules.
- PyPI release (or Git-based install docs).

## Deliverables

| # | Artifact | Description |
|---|---|---|
| 1 | `proxmox` Python package | Installable via `uv tool install` from Git or PyPI. |
| 2 | `README.md` | Installation, quickstart, full command reference, auth setup. |
| 3 | `pyproject.toml` | Build config, dependency list, entry point definition. |
| 4 | Unit test suite | `tests/` directory, runnable with `pytest`. |
| 5 | `CHANGELOG.md` | Versioned release notes. |

## Risks & Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| **Package name conflict on PyPI** | Already resolved | `proxmox` is free on PyPI (`proxmox-cli` is taken). No risk. |
| **Proxmox API changes across versions** | Breakage on PVE upgrade | Pin tested versions (7.x, 8.x); version-detect header in future. |
| **CSRF token expiry mid-session** | Commands suddenly fail with 401 | Auto-retry once with fresh ticket; transparent to user. |
| **Self-signed cert confusion** | New users can't connect | Clear error message pointing to `--insecure` flag; document prominently. |
| **Slow startup time** | Poor UX | Lazy-load subcommand modules; profile startup ≥ 0.3 target. |
| **Scope creep** | Never ships v1 | Strict milestone enforcement; defer all non-core resources to v1.1+. |

## Success Metrics

- **Install-to-first-command time**: under 60 seconds (install + auth + `vm list`).
- **Startup latency**: `proxmox --help` ≤ 300 ms.
- **API coverage (v1)**: 6 resources (vm, container, node, storage, cluster, task) with full CRUD + lifecycle actions.
- **Test coverage**: ≥ 80% on `client/`, `config/`, and `output/` modules.
- **Error clarity**: Every HTTP error produces a message containing the Proxmox API error body, not just a status code.
- **Agent success path**: an AI agent can run `proxmox vm create ...` and parse the JSON response without additional tooling.