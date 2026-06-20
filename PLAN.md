# Implementation Plan: Proxmox CLI (`proxmox`)

## Plan Overview

Build a Python CLI (`proxmox`) that wraps the Proxmox VE REST API. The tool follows a `<resource> <action>` subcommand hierarchy, persists credentials in an XDG config file, and emits structured output (JSON/table/YAML). This plan covers v1 (6 resources, 4 phases, ~4 weeks) as defined in `PROJECT.md`.

**Entry point:** `proxmox <resource> <action> [--flags]`  
**Install:** `uv tool install .` or `uv tool install git+https://...`  
**Target Python:** 3.10+

## Assumptions

1. Developer has `uv` installed and a Python 3.10+ runtime available.
2. Development done against a Proxmox VE 8.x instance (tested; 7.x compatibility is a goal but not gated).
3. `proxmox` is confirmed free on PyPI — no naming conflict.
4. Single-endpoint config in v1; profile support deferred.
5. `httpx` chosen over `requests` for future async/streaming capabilities.
6. Config directory is `~/.config/proxmox-cli/` (XDG-compliant, project-scoped name to avoid potential clashes).
7. No interactive password prompts — only `--password`, `--password-stdin`, or `PROXMOX_PASSWORD` env var.

---

## Work Breakdown Structure

### Epic 1: Project Scaffolding & Client Core

**Goal:** Bootable project, installable entry point, HTTP client that can authenticate and make requests.

| Task ID | Task | Owner | Est. |
|---|---|---|---|
| 1.1 | Initialize project with `uv` | — | 30m |
| 1.2 | Define package structure & entry point | — | 30m |
| 1.3 | Implement `ProxmoxClient` (HTTP dispatch) | — | 3h |
| 1.4 | Implement auth (ticket + API token) | — | 2h |
| 1.5 | Implement `ConfigLoader` (read/write credentials) | — | 2h |
| 1.6 | Root CLI parser with global flags | — | 2h |
| 1.7 | Implement `auth` subcommand | — | 1.5h |
| 1.8 | Write unit tests for client, auth, config | — | 2h |

**Epic 1 total:** ~13h

### Epic 2: Core Resource Subcommands (VM, Node, Cluster)

**Goal:** `vm`, `node`, and `cluster` subcommands fully functional.

| Task ID | Task | Owner | Est. |
|---|---|---|---|
| 2.1 | `proxmox node` subcommand (`list`, `show`, `status`) | — | 2h |
| 2.2 | `proxmox vm` subcommand (`list`, `show`) | — | 2h |
| 2.3 | `proxmox vm` lifecycle (`create`, `start`, `stop`, `reboot`, `suspend`, `resume`, `delete`) | — | 4h |
| 2.4 | `proxmox cluster status` | — | 1h |
| 2.5 | Shared CLI helper: `--node` flag, VMID validation, pagination | — | 1.5h |
| 2.6 | Unit + integration tests for VM, node, cluster commands | — | 3h |

**Epic 2 total:** ~13.5h

### Epic 3: Remaining Resources & Output Formatting

**Goal:** All v1 resources covered; all three output formatters working.

| Task ID | Task | Owner | Est. |
|---|---|---|---|
| 3.1 | `proxmox container` subcommand (`list`, `show`, `create`, `start`, `stop`, `delete`) | — | 3h |
| 3.2 | `proxmox storage` subcommand (`list`, `show`, `content`) | — | 2h |
| 3.3 | `proxmox task` subcommand (`list`, `show`) | — | 1.5h |
| 3.4 | JSON output formatter | — | 1h |
| 3.5 | Table output formatter (via `rich`) | — | 2h |
| 3.6 | YAML output formatter | — | 1h |
| 3.7 | `--dry-run` flag implementation | — | 1.5h |
| 3.8 | Error formatting (extract Proxmox error body) | — | 1h |
| 3.9 | Tests for output formatters and remaining resources | — | 2h |

**Epic 3 total:** ~15h

### Epic 4: Polish, Resilience & Release

**Goal:** Production-ready: retries, timeouts, full test coverage, docs, PyPI release.

| Task ID | Task | Owner | Est. |
|---|---|---|---|
| 4.1 | Retry with exponential backoff on 5xx | — | 2h |
| 4.2 | `--timeout` flag wired through to httpx | — | 1h |
| 4.3 | `--insecure` / TLS verification skip | — | 1h |
| 4.4 | Verbose logging (`--verbose`) to stderr | — | 1h |
| 4.5 | Lazy-load subcommands (startup perf) | — | 1.5h |
| 4.6 | `--password-stdin` support | — | 0.5h |
| 4.7 | Full README with examples | — | 2h |
| 4.8 | `CHANGELOG.md` | — | 0.5h |
| 4.9 | CI pipeline (GitHub Actions: lint, test, build) | — | 2h |
| 4.10 | Test coverage ≥80% across client/, config/, output/ | — | 2h |
| 4.11 | PyPI release (or Git-based install verified) | — | 1h |

**Epic 4 total:** ~14.5h

**Grand total:** ~56h (approx. 2 weeks full-time; ~4 weeks part-time)

---

## Task Dependencies

```
Epic 1 ──────────────┐
  ├─ 1.1 → 1.2 → 1.3 ┤
  ├─ 1.3 → 1.4 ──────┤
  ├─ 1.2 → 1.5 ──────┤
  ├─ 1.2 → 1.6 ──────┤
  ├─ 1.4 + 1.5 + 1.6 → 1.7
  └─ 1.3 + 1.4 + 1.5 → 1.8

Epic 2 (depends on Epic 1 complete)
  ├─ 2.5 → 2.1, 2.2, 2.3, 2.4
  └─ 2.1...2.4 → 2.6

Epic 3 (depends on Epic 2 complete)
  ├─ 3.1, 3.2, 3.3 (can be parallel)
  ├─ 3.4, 3.5, 3.6 (can be parallel)
  ├─ 3.7 (depends on output formatters)
  ├─ 3.8 (depends on client)
  └─ 3.1...3.8 → 3.9

Epic 4 (depends on Epics 1-3 complete)
  ├─ 4.1, 4.2, 4.3, 4.4, 4.6 (can be parallel)
  ├─ 4.5 (profiling first, then lazy-load)
  ├─ 4.7, 4.8 (last, before release)
  ├─ 4.9 (CI, can start after 4.1)
  ├─ 4.10 (throughout, gated at end)
  └─ 4.11 (final step, after 4.7, 4.9, 4.10)
```

---

## Step-by-Step Implementation Sequence

### Phase 1 — Skeleton & Auth

#### Task 1.1: Initialize project with `uv`

**Objective:** Create a standard Python package with `uv`, ready for development.

**Actions:**
1. Run `uv init --lib proxmox` in the repo root.
2. Add runtime deps: `uv add httpx pydantic rich pyyaml`.
3. Add dev deps: `uv add --dev pytest pytest-httpx pytest-cov`.
4. Ensure `python_requires = ">=3.10"` in `pyproject.toml`.
5. Edit `[project.scripts]` to add: `proxmox = "proxmox.cli.main:main"`.

**Expected output:** `pyproject.toml` with correct deps, `uv.lock`, empty `src/proxmox/` (or flat-layout `proxmox/`).

**Validation:**
```bash
uv run proxmox --help   # should fail cleanly (no parser yet) but import succeeds
uv run python -c "import httpx, pydantic, rich, yaml; print('OK')"
```

#### Task 1.2: Define package structure & entry point

**Objective:** Create all module directories and a minimal importable `main()`.

**Actions:**
1. Create the directory tree:
   ```
   proxmox/
   ├── __init__.py
   ├── cli/
   │   ├── __init__.py
   │   ├── main.py          # root parser, `main()`, global flags
   │   ├── auth.py          # `proxmox auth` subcommand
   │   ├── vm.py
   │   ├── container.py
   │   ├── node.py
   │   ├── storage.py
   │   ├── cluster.py
   │   └── task.py
   ├── client/
   │   ├── __init__.py
   │   ├── client.py        # ProxmoxClient
   │   ├── auth.py          # AuthManager
   │   └── exceptions.py
   ├── config/
   │   ├── __init__.py
   │   ├── config.py        # ConfigLoader
   │   └── models.py        # Pydantic models
   ├── output/
   │   ├── __init__.py
   │   ├── formatter.py     # dispatch
   │   ├── json_fmt.py
   │   ├── table_fmt.py
   │   └── yaml_fmt.py
   └── utils/
       ├── __init__.py
       ├── helpers.py
       └── logging.py
   ```
2. `cli/main.py`: `def main(): pass` and `if __name__ == "__main__": main()`.
3. Verify: `uv run proxmox` exits cleanly (no output, no error).

**Validation:** `uv run proxmox` returns exit code 0.

#### Task 1.3: Implement `ProxmoxClient` (HTTP dispatch)

**Objective:** An HTTP client that sends requests to the Proxmox API base URL with auth headers, timeout, and TLS control.

**Actions:**
1. In `client/client.py`, create class `ProxmoxClient`:
   ```python
   class ProxmoxClient:
       def __init__(self, base_url: str, auth_manager: AuthManager,
                    timeout: int = 30, verify_tls: bool = True):
           ...
   ```
2. Methods:
   - `request(method: str, path: str, params=None, data=None) -> dict`
   - `get(path, params=None) -> dict`
   - `post(path, data=None) -> dict`
   - `put(path, data=None) -> dict`
   - `delete(path, params=None) -> dict`
3. Inside `request`:
   - Build full URL: `f"{base_url}/api2/json{path}"`
   - Inject auth headers from `AuthManager.get_headers()`
   - Send via `httpx.Client` with timeout
   - Handle non-2xx: raise `ProxmoxAPIError(status_code, response_body)`
   - Return `response.json()["data"]` (unwrap Proxmox envelope)
4. In `client/exceptions.py`:
   ```python
   class ProxmoxError(Exception): ...
   class ProxmoxAPIError(ProxmoxError):
       def __init__(self, status_code: int, body: dict): ...
   class AuthError(ProxmoxError): ...
   class ConfigError(ProxmoxError): ...
   ```

**Validation:**
```python
# Unit test with pytest-httpx
def test_client_get(mock_httpx):
    client = ProxmoxClient("https://pve:8006", mock_auth)
    mock_httpx.get("https://pve:8006/api2/json/nodes").respond(
        json={"data": [{"node": "pve01"}]}
    )
    result = client.get("/nodes")
    assert result == [{"node": "pve01"}]
```

#### Task 1.4: Implement auth (ticket + API token)

**Objective:** `AuthManager` that acquires and caches authentication credentials for a single process lifetime.

**Actions:**
1. In `client/auth.py`:
   ```python
   class AuthMethod(Enum):
       PASSWORD = "password"
       API_TOKEN = "api_token"

   class AuthManager:
       def __init__(self, client: httpx.Client):
           self._client = client
           self._ticket: str | None = None
           self._csrf_token: str | None = None

       def authenticate_password(self, base_url, username, password) -> None:
           # POST /api2/json/access/ticket
           # Extract ticket and CSRFPreventionToken

       def set_api_token(self, user, token_id, secret) -> None:
           # Store base64-encoded Authorization header

       def get_headers(self) -> dict:
           # Return Cookie + CSRFPreventionToken OR Authorization
   ```
2. Password auth flow:
   - `POST {base_url}/api2/json/access/ticket` with `username` + `password` in form data.
   - Response: `{"data": {"ticket": "...", "CSRFPreventionToken": "..."}}`.
   - Store both.
   - Subsequent requests get `Cookie: PVEAuthCookie={ticket}` + `CSRFPreventionToken: {token}`.
3. Token auth flow:
   - `Authorization: PVEAPIToken={user}!{token_id}={base64(secret)}`
   - No ticket acquisition needed; valid on every request.

**Validation:**
```python
def test_password_auth(mock_httpx):
    mgr = AuthManager(mock_httpx.Client())
    mock_httpx.post(".../access/ticket").respond(json={
        "data": {"ticket": "TICKET", "CSRFPreventionToken": "CSRF"}
    })
    mgr.authenticate_password("https://pve:8006", "root@pam", "secret")
    headers = mgr.get_headers()
    assert headers["Cookie"] == "PVEAuthCookie=TICKET"
    assert headers["CSRFPreventionToken"] == "CSRF"
```

#### Task 1.5: Implement `ConfigLoader` (read/write credentials)

**Objective:** Load credentials from `~/.config/proxmox-cli/credentials.json` or `/etc/proxmox-cli/credentials.json`, with override support.

**Actions:**
1. In `config/models.py`, define Pydantic models:
   ```python
   class Credentials(BaseModel):
       url: str
       username: str
       auth_method: AuthMethod
       # For password auth:
       password: str | None = None
       # For token auth:
       api_token_id: str | None = None
       api_token_secret: str | None = None
       verify_tls: bool = True
   ```
2. In `config/config.py`:
   ```python
   class ConfigLoader:
       USER_CONFIG_DIR = Path.home() / ".config" / "proxmox-cli"
       SYSTEM_CONFIG_DIR = Path("/etc/proxmox-cli")
       
       @classmethod
       def load(cls) -> Credentials: ...
       @classmethod
       def save(cls, creds: Credentials) -> None: ...
       @classmethod
       def clear(cls) -> None: ...
   ```
3. `load()`: try user config → system config → raise `ConfigError`.
4. `save()`: write to user config dir, create dirs if needed (`mkdir -p`).
5. `clear()`: delete user config file.
6. File permissions: `credentials.json` set to `0o600` on write.

**Validation:**
```python
def test_save_and_load(tmp_path):
    # Use monkeypatched USER_CONFIG_DIR
    loader.save(Credentials(url="https://pve:8006", ...))
    loaded = loader.load()
    assert loaded.url == "https://pve:8006"
```

#### Task 1.6: Root CLI parser with global flags

**Objective:** The root `argparse` parser that handles global flags and dispatches to subcommands.

**Actions:**
1. In `cli/main.py`:
   ```python
   def build_root_parser() -> argparse.ArgumentParser:
       parser = argparse.ArgumentParser(prog="proxmox", ...)
       parser.add_argument("--url", help="Proxmox API URL")
       parser.add_argument("--username", help="Username (e.g., root@pam)")
       parser.add_argument("--password", help="Password")
       parser.add_argument("--api-token", help="API token (user!tokenid=secret)")
       parser.add_argument("--output", choices=["json", "table", "yaml"], default="json")
       parser.add_argument("--dry-run", action="store_true")
       parser.add_argument("--insecure", action="store_true", help="Skip TLS verification")
       parser.add_argument("--timeout", type=int, default=30)
       parser.add_argument("--verbose", action="store_true")
       subparsers = parser.add_subparsers(dest="resource", required=True)
       return parser, subparsers
   ```
2. Each subcommand module (`cli/vm.py`, etc.) exposes a `register(subparsers)` function.
3. `main()`:
   - Parse args
   - Merge config file + env var + CLI flags (CLI wins)
   - Build `ProxmoxClient` + `AuthManager`
   - Dispatch to `args.func(args, client)`
   - Catch exceptions → format error → exit non-zero

**Validation:** `uv run proxmox --help` prints usage. `uv run proxmox vm --help` (after registration) prints VM help.

#### Task 1.7: Implement `auth` subcommand

**Objective:** `proxmox auth` with `login`, `status`, and `clear` actions.

**Actions:**
1. In `cli/auth.py`:
   - `proxmox auth login --url ... --username ... --password ...`: authenticate, save `Credentials`.
   - `proxmox auth login --url ... --username ... --api-token ...`: save token-based credentials.
   - `proxmox auth status`: load config, display URL, username, auth method (mask password/secret).
   - `proxmox auth clear`: delete config file, print confirmation.
2. On `login`, optionally validate credentials with a real API call (e.g., `GET /api2/json/version`) before saving.

**Validation:**
```bash
uv run proxmox auth login --url https://pve:8006 --username root@pam --password secret
uv run proxmox auth status
# Expected: URL https://pve:8006, user root@pam, method password
uv run proxmox auth clear
uv run proxmox auth status
# Expected: error "No credentials found"
```

#### Task 1.8: Unit tests for client, auth, config

**Objective:** Foundation test suite for Epic 1.

**Actions:**
1. Create `tests/` directory with `__init__.py`, `conftest.py`.
2. `conftest.py`: fixtures for `mock_httpx_client`, sample credentials dict, tmp config dir.
3. Write tests for:
   - `ProxmoxClient.request` — GET, POST, error response (401, 500).
   - `AuthManager` — password auth, token auth, header generation.
   - `ConfigLoader` — save, load, clear, missing file, permission check.
4. Run: `uv run pytest --cov=proxmox.client --cov=proxmox.config -v`

**Expected output:** ≥90% coverage on client/ and config/ modules. All tests green.

---

### Phase 2 — Core Resources

#### Task 2.1: `proxmox node` subcommand

**Actions:**
1. `proxmox node list` → `GET /nodes` → list all nodes.
2. `proxmox node show <node>` → `GET /nodes/{node}/status`.
3. `proxmox node status [<node>]` → if node given, `GET /nodes/{node}/status`; else `GET /nodes` with status summary.

**Validator function:** `node_exists(client, node_name)`.

#### Task 2.2: `proxmox vm list/show`

**Actions:**
1. `proxmox vm list [--node <node>]`:
   - If `--node` given: `GET /nodes/{node}/qemu`
   - Else: iterate all nodes via `GET /nodes` then `GET /nodes/{node}/qemu` per node.
2. `proxmox vm show <vmid>`:
   - Need node context: first try `GET /cluster/resources?type=vm` to find node, then `GET /nodes/{node}/qemu/{vmid}/status/current`.
   - Alternative: `GET /cluster/resources?type=vm` only (simpler, covers vmid lookup).

**VMID validation:** positive integer or `--vmid` flag.

#### Task 2.3: `proxmox vm` lifecycle commands

**Actions:**
1. `proxmox vm create --node <node> --vmid <id> --memory <mb> --cores <n> [--ostemplate <tmpl>] [--storage <name>] [--net0 <model=...,bridge=...>]`:
   - `POST /nodes/{node}/qemu` with `vmid`, `memory`, `cores`, etc. as form data.
   - Return UPID or VMID on success.
2. `proxmox vm start <vmid> [--node <node>]` → `POST /nodes/{node}/qemu/{vmid}/status/start`
3. `proxmox vm stop <vmid> [--node <node>]` → `POST .../status/stop`
4. `proxmox vm reboot <vmid>` → `POST .../status/reboot`
5. `proxmox vm suspend <vmid>` → `POST .../status/suspend`
6. `proxmox vm resume <vmid>` → `POST .../status/resume`
7. `proxmox vm delete <vmid> [--node <node>] [--force] [--purge]` → `DELETE /nodes/{node}/qemu/{vmid}` with params.

**Node resolution for VMID:** implement a shared helper `resolve_node_for_vmid(client, vmid)` that queries `/cluster/resources?type=vm`.

#### Task 2.4: `proxmox cluster status`

**Actions:**
1. `proxmox cluster status` → `GET /cluster/status`.
2. Display quorum info, node list with online/offline status.

#### Task 2.5: Shared CLI helpers

**Actions:**
1. `--node` flag: common across node, vm, container, storage, task. Add to root parser via `add_argument` on the root (or a shared `add_common_flags(parser)`).
2. VMID validator: `def vmid_type(value: str) -> int` → raises `argparse.ArgumentTypeError`.
3. Pagination helper (future): not needed for v1, but add `--limit` / `--offset` to root flags so the signature is ready.

#### Task 2.6: Tests for VM, node, cluster

**Actions:**
1. Mock `httpx` responses for each endpoint.
2. Integration-style tests: call the real `main()` with `sys.argv` patched, capture stdout, parse JSON, assert.
3. Test edge cases: missing node, invalid VMID, 404 VMID, 403 permission.

---

### Phase 3 — Remaining Resources & Output

#### Task 3.1: `proxmox container` subcommand

**Actions:**
1. `proxmox container list [--node <node>]` → `GET /nodes/{node}/lxc`
2. `proxmox container show <vmid>` → `GET /nodes/{node}/lxc/{vmid}/status/current`
3. `proxmox container create --node <node> --vmid <id> --ostemplate <tmpl> --storage <name> --memory <mb> --cores <n>` → `POST /nodes/{node}/lxc`
4. `start`, `stop`, `delete` analogous to VM but with `/lxc/` path prefix.

#### Task 3.2: `proxmox storage` subcommand

**Actions:**
1. `proxmox storage list [--node <node>]` → `GET /storage` or `GET /nodes/{node}/storage`
2. `proxmox storage show <storage>` → `GET /storage/{storage}/status`
3. `proxmox storage content <storage>` → `GET /nodes/{node}/storage/{storage}/content`

#### Task 3.3: `proxmox task` subcommand

**Actions:**
1. `proxmox task list [--node <node>]` → `GET /nodes/{node}/tasks`
2. `proxmox task show <upid>` → `GET /nodes/{node}/tasks/{upid}/status`
   - UPID parsing: extract node from UPID string `UPID:{node}:...`

#### Task 3.4: JSON output formatter

**Actions:**
1. In `output/json_fmt.py`:
   ```python
   def format_json(data: dict | list, indent: int = 2) -> str:
       return json.dumps(data, indent=indent, ensure_ascii=False)
   ```
2. Always valid JSON. Errors go to stderr as JSON too: `{"error": "...", "status_code": 401}`.

#### Task 3.5: Table output formatter

**Actions:**
1. In `output/table_fmt.py`:
   ```python
   def format_table(data: list[dict], columns: list[str] | None = None) -> str:
       # Use rich.table.Table
       # Auto-detect columns from first dict keys if not specified
   ```
2. For single-object responses (`show`), display as key-value table.
3. For list responses, display as columnar table.

#### Task 3.6: YAML output formatter

**Actions:**
1. In `output/yaml_fmt.py`:
   ```python
   def format_yaml(data: Any) -> str:
       return yaml.dump(data, default_flow_style=False, sort_keys=False)
   ```

#### Task 3.7: `--dry-run` flag

**Actions:**
1. In `ProxmoxClient.request`, if `dry_run=True` passed:
   - Do not execute the HTTP call.
   - Format and print: `{method} {full_url}\nHeaders: {headers}\nBody: {body}`
   - Return `None` (or empty dict for caller compatibility).
2. Pass `dry_run` from global args → client constructor → each request.

#### Task 3.8: Error formatting

**Actions:**
1. Catch `ProxmoxAPIError` in `main()`.
2. Extract `errors` or `message` field from Proxmox response body.
3. Format for stderr:
   - JSON mode: `{"error": "Permission check failed (403)", "detail": {...}}`
   - Table/text mode: `Error (403): Permission check failed\n  - /path: insufficient permissions`
4. Exit code = HTTP status code (or 1 for non-HTTP errors).

#### Task 3.9: Tests for output and remaining resources

**Actions:**
1. Test each formatter with sample data.
2. Test `--dry-run` produces expected output without HTTP calls.
3. Test error formatting with mock error responses.
4. Test container, storage, task commands with mocked responses.

---

### Phase 4 — Polish, Resilience & Release

#### Task 4.1: Retry with exponential backoff

**Actions:**
1. In `ProxmoxClient.request`, wrap HTTP call:
   ```python
   max_retries = 3
   for attempt in range(max_retries):
       try:
           response = self._client.request(...)
           if response.status_code < 500:
               break
       except httpx.TimeoutException:
           if attempt == max_retries - 1: raise
       sleep(2 ** attempt)
   ```
2. Log retries to stderr when `--verbose`.

#### Task 4.2: `--timeout` flag

**Actions:**
1. Already wired in `ProxmoxClient.__init__`. Ensure `--timeout` from CLI flows through to client.

#### Task 4.3: `--insecure` flag

**Actions:**
1. `ProxmoxClient.__init__` accepts `verify_tls: bool`.
2. If `verify_tls=False`, pass `verify=False` to `httpx.Client`.
3. When `--insecure` is used and TLS fails with `--insecure` not set: print helpful message.

#### Task 4.4: Verbose logging

**Actions:**
1. `utils/logging.py`: configure Python `logging` to stderr.
2. When `--verbose`: set level to `DEBUG`, log each request/response summary.
3. Normal mode: no logging output on stderr (only errors).

#### Task 4.5: Lazy-load subcommands

**Actions:**
1. Profile startup: `time uv run proxmox --help`.
2. If over 300ms, refactor `register_*` calls to use lazy imports or deferred registration.
3. Strategy: each CLI module's `register(subparsers)` is only imported once the subparser is needed. Since argparse builds all parsers at startup anyway, this is mainly about avoiding heavy imports (e.g., `rich`, `yaml`) until needed.
4. Move `import rich`, `import yaml` inside formatter functions rather than module-level.

#### Task 4.6: `--password-stdin` support

**Actions:**
1. Add `--password-stdin` flag to root parser.
2. If set, read password from stdin (first line, strip newline).
3. Works only for password auth, not token auth.

#### Task 4.7: Full README

**Actions:**
1. Sections: Installation, Quickstart, Authentication, Command Reference, Output Formats, AI Agent Usage, Development, License.
2. Include copy-pasteable examples for every command.
3. Document `PROXMOX_PASSWORD` env var and `--password-stdin`.

#### Task 4.8: CHANGELOG

**Actions:**
1. Create `CHANGELOG.md` with v1.0.0 entry.
2. Follow [Keep a Changelog](https://keepachangelog.com/) format.

#### Task 4.9: CI pipeline

**Actions:**
1. Create `.github/workflows/ci.yml`:
   ```yaml
   on: [push, pull_request]
   jobs:
     test:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
         - uses: astral-sh/setup-uv@v3
         - run: uv sync
         - run: uv run ruff check .
         - run: uv run pytest --cov --cov-report=xml
   ```
2. Add `ruff` as dev dependency: `uv add --dev ruff`.

#### Task 4.10: Test coverage ≥80%

**Actions:**
1. Run `uv run pytest --cov=proxmox.client --cov=proxmox.config --cov=proxmox.output --cov-report=term-missing`.
2. Identify uncovered lines, add tests.
3. Gate: ≥80% line coverage on those three packages.

#### Task 4.11: PyPI release

**Actions:**
1. Verify `pyproject.toml` metadata: `name`, `version`, `description`, `authors`, `license`, `classifiers`.
2. `uv build` → produces `.tar.gz` and `.whl` in `dist/`.
3. `uv publish` or `twine upload dist/*`.
4. Post-release: verify `uv tool install proxmox` works from PyPI.

---

## Testing Strategy

| Layer | Scope | Tool | When |
|---|---|---|---|
| **Unit** | `client/`, `config/`, `output/`, `utils/` — pure logic, no network | `pytest` + `pytest-httpx` | Every task, continuously |
| **Integration** | CLI commands end-to-end with mocked HTTP | `pytest` + `pytest-httpx` (mocked transport) | After each resource task |
| **Integration (real)** | Against a live Proxmox instance | `pytest` with `--integration` marker | Phase 4, manually/CI-optional |
| **Smoke** | `uv run proxmox --help`, install from dist | bash script | Final release gate |

### Test Structure

```
tests/
├── conftest.py                   # shared fixtures
├── test_client.py                # ProxmoxClient unit tests
├── test_auth.py                  # AuthManager unit tests
├── test_config.py                # ConfigLoader unit tests
├── test_cli/
│   ├── test_auth.py              # `proxmox auth` integration
│   ├── test_vm.py                # `proxmox vm` integration
│   ├── test_node.py
│   ├── test_container.py
│   ├── test_storage.py
│   ├── test_cluster.py
│   └── test_task.py
├── test_output/
│   ├── test_json_fmt.py
│   ├── test_table_fmt.py
│   └── test_yaml_fmt.py
└── test_integration/
    └── test_real.py              # Real Proxmox (flagged)
```

### Test Patterns

- **Mock fixture for httpx:**
  ```python
  @pytest.fixture
  def client(mock_httpx):
      auth = AuthManager(...)
      client = ProxmoxClient("https://pve:8006", auth)
      return client
  ```
- **CLI test helper:**
  ```python
  def run_cli(*args) -> subprocess.CompletedProcess:
      return subprocess.run(
          ["uv", "run", "proxmox", *args],
          capture_output=True, text=True
      )
  ```

---

## Rollout Strategy

| Stage | Audience | Channel |
|---|---|---|
| **Alpha** | Developer only | `uv tool install git+https://...` from main branch |
| **Beta** | Early testers | PyPI pre-release (`--pre` flag) |
| **v1.0.0** | Public | PyPI stable, GitHub Releases, `uv tool install proxmox` |

### Pre-release checklist
- [ ] All tests green (unit + CLI integration).
- [ ] Manual smoke test against real Proxmox (auth, vm list, vm create, vm delete).
- [ ] README reviewed for accuracy (every command copy-paste tested).
- [ ] `uv build` succeeds.
- [ ] `uv tool install .` succeeds and `proxmox --help` works.
- [ ] CI pipeline green on GitHub.

---

## Monitoring & Observability

For a CLI tool, "observability" means:

1. **Exit codes:** always set correctly (0 = success, non-zero = error). This is how scripts/agents detect failures.
2. **Stderr for diagnostics:** errors, retry notices, verbose logs go to stderr. Stdout is reserved for command output (JSON/table/YAML).
3. **`--verbose` flag:** enables debug-level HTTP logging (method, URL, status, timing).
4. **Version endpoint:** `proxmox --version` prints package version (from `importlib.metadata`).
5. **Future:** optional telemetry? Not in v1 — too invasive for a homelab tool.

---

## Risks, Unknowns, and Fallbacks

| Risk | Likelihood | Impact | Mitigation | Fallback |
|---|---|---|---|---|
| **Proxmox API changes break parsing** | Medium | High (commands fail) | Pin to tested PVE versions in docs; add `proxmox --api-version-check` | Wrap breaking endpoints with version-detection; raise clear error |
| **`uv tool install` path issues** | Low | Medium (cant run) | Test on macOS, Linux, WSL | Fall back to `pipx install` instruction in README |
| **Lazy-loading makes first subcommand slow** | Low | Low (UX degrades) | Profile and pre-load critical path | Revert to eager imports |
| **CSRF ticket expires mid-session** | Low | Medium (401 mid-command) | Auto-retry once with fresh ticket | User re-runs command |
| **Self-signed cert not accepted by default** | High | Medium (blocked new users) | Clear error message; `--insecure` documented first in README | N/A — `--insecure` is the escape hatch |
| **`proxmox` package name taken on PyPI between now and release** | Very low | High (can't release) | Reserve early; we know it's free now | Fallback: `proxmox-pve` |

---

## Definition of Done

A task/epic is **done** when:

1. Code passes `ruff check` with no errors.
2. All unit and integration tests pass.
3. New code has corresponding tests (no drop in coverage %).
4. `uv run proxmox <command>` works for the implemented feature.
5. `--help` text is accurate for the implemented commands.
6. Code reviewed (self-review acceptable for solo dev; PR for team).

### v1.0.0 Definition of Done
- [ ] All Epics 1-4 tasks complete.
- [ ] ≥80% test coverage on `client/`, `config/`, `output/`.
- [ ] `proxmox --version` reports v1.0.0.
- [ ] `uv tool install .` → `proxmox --help` works.
- [ ] Smoke test against real PVE 8.x: auth, `vm list`, `vm create`, `vm delete`, `node status`, `cluster status`.
- [ ] README complete with all examples tested.
- [ ] CHANGELOG published.
- [ ] Package published to PyPI.
