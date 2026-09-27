# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.20.0] - 2026-09-27

### Changed
- **`auth setup` is now manual by default.** Running `proxmox auth setup` with
  no flags prints the flat `pveum`/`pvesh` commands to run on a Proxmox node as
  `root` — no SSH access required. The user reviews the commands, pastes them
  into a root shell on a node, copies the token secret from the `pvesh` output,
  and pastes it back when proxcli prompts (which writes `credentials.json`).
  This makes SSH key/password access a non-requirement for the default flow:
  the user stays in control and can review every command before it runs.

  - The previous automatic-over-SSH behaviour is now opt-in via `--auto`
    (shorthand for `--via ssh`). Scripts that relied on `proxmox auth setup
    --host <node>` doing SSH should add `--auto` (or `--via ssh`).
  - `--via` now accepts `manual` (default), `ssh`, and `api`.
  - `--non-interactive` / `--no-write` manual mode prints a `credentials.json`
    template instead of prompting; `--json` returns the commands + template as
    structured output for agents.

### Added
- **`generate_manual_commands(spec)`** in `proxmox.ssh.script` — produces the
  flat, idempotent (`pveum role add ... || pveum role modify ...`) command list
  that manual mode prints. Unit-tested alongside the existing script generator.

## [0.19.0] - 2026-09-27

### Added
- **Agent-friendly ergonomics pass.** A round of changes that make the CLI
  easier for automated callers (AI agents, scripts) to drive correctly on the
  first try:
  - **`proxcli` binary alias.** The package now installs both `proxmox` and
    `proxcli` entry points — use whichever the task description names.
  - **Bare `node` field on read output.** VM, container, task, and VM-IP
    records now carry a top-level `node` (alongside the historical `_node`),
    so the node needed for the next command is always at the obvious key.
  - **`--name` filter on `vm list` and `container list`.** Case-insensitive
    substring match across all nodes; collapses the hostname→vmid+node lookup
    to a single command (`proxmox vm list --name unifi`).
  - **`--columns` is comma-separated and position-flexible.** Fixed the
    `nargs="+"` footgun that broke `vm list --columns vmid name`; columns are
    now `--columns vmid,name,status` and work before or after the subcommand.
  - **Global flags work after the subcommand.** `proxmox vm list --dry-run` and
    `proxmox vm list --output yaml` now parse correctly — global flags are
    internally relocated before the resource. (`--timeout` is deliberately
    excluded because `task wait` / `vm agent exec` shadow it.)
  - **Zero-argument cheat sheet.** Running `proxmox` with no args prints a
    concise quick-start instead of the full `--help` dump.
  - **Snapshot create: `--wait`, `--if-not-exists`, UPID hint.** `vm snapshot
    create` returns the UPID with a `task wait` hint by default; `--wait`
    blocks until completion; `--if-not-exists` makes it idempotent.
  - **`ProxmoxClient.wait_for_task(upid)`** — a reusable, dry-run-aware helper
    that polls `/nodes/{node}/tasks/{upid}/status` to a terminal state.
  - **`docs/agent-guide.md`** — a focused reference for automated callers,
    linked from the README.

## [0.18.1] - 2026-09-25

### Added
- **`proxmox auth setup --allow-guest-exec`** grants `VM.GuestAgent.Unrestricted`
  on the `proxcli-vm` role so that `proxmox vm agent exec` works. The
  privilege is off by default — alone it grants all guest-agent operations
  (exec + file-write). Re-running setup with the flag syncs the role in place
  (`pveum role modify` / `PUT /access/roles/{id}` replace privs), so an
  **existing token gains exec immediately — no `--regenerate`, no rotation**;
  drop the flag and re-run to revoke it again.

### Fixed
- **`--via api` setup path now syncs existing roles.** Previously it only
  created missing roles and skipped existing ones, so re-running with a changed
  spec (e.g. `--allow-guest-exec`) had no effect on clusters that already had
  the roles. It now updates out-of-sync roles in place via
  `PUT /access/roles/{id}`, mirroring the SSH path's self-healing behaviour.
  The summary reports a new `roles_synced` list.
- **`auth status --permissions` now probes guest-agent exec**
  (`POST .../agent/exec`, requiring `VM.GuestAgent.Unrestricted`), so a missing
  exec privilege is reported as a FAIL instead of going unnoticed.
- **`docs/api-permissions.md`** listed `proxcli-vm` without the
  `VM.GuestAgent.Audit` / `VM.GuestAgent.FileRead` privileges the code actually
  grants; the doc is corrected and the optional `VM.GuestAgent.Unrestricted`
  is documented.

## [0.18.0] - 2026-09-25

### Fixed
- **`proxmox vm agent exec` now correctly targets the PVE 8+ API.** The
  previous implementation base64-encoded the command into a single string and
  split `--args` on whitespace, which (a) no longer matches the Proxmox 8+
  `agent/exec` schema that expects `command` as an array of `[program, arg,
  ...]`, and (b) could not preserve arguments containing spaces.

### Changed
- **`vm agent exec` argument syntax redesigned.** The command is now taken
  from variadic positional args, each becoming one argv element passed
  directly to the guest agent (no shell runs in the guest, so shell quoting
  preserves spaces exactly). Use a leading `--` to separate flag-like
  arguments: `proxmox vm agent exec 100 -- ls -la /etc`. The old `--command`
  / `--args` flags are removed. New `--shell` wraps the joined command as
  `/bin/sh -c` for pipes, `&&` and globbing. New `--timeout` makes the poll
  window configurable (default 30s). The legacy base64 command encoding is
  dropped in favour of the array form that httpx form-encodes as repeated
  `command=` keys, matching `pvesh -command`.

## [0.17.0] - 2026-09-25

### Added
- **`proxmox auth setup` rewritten as an SSH-based interactive configurator.**
  `proxmox auth setup --host <node>` SSHes into a Proxmox node as `root@pam`
  and, in one idempotent pass, creates the recommended `proxcli-*` roles, an
  API token, and the ACLs that bind them — then writes the resulting token
  secret to `credentials.json` (mode `0600`, with a `.bak` on overwrite). No
  UI, no manual `pveum`, no hand-editing JSON. The generated bash script uses
  `pveum` (roles/ACLs) and `pvesh ... --output-format json` (token
  create/regenerate with secret capture) and is safe to re-run. Key-based SSH
  auth is the default; password auth is supported when `sshpass` is installed.
  New flags: `--via {ssh,api}`, `--host`, `--ssh-user`, `--port`,
  `-i/--identity`, `--ssh-password`, `--ssh-password-stdin`, `--pve-user`,
  `--token-name`, `--privsep/--no-privsep`, `--regenerate`, `--non-interactive`,
  `--force`, `--no-write`, `--dry-run`, `--json`. `--dry-run` previews the
  script without contacting the node; `--json` returns it structured for
  agents. The token is created with **privilege separation ON** and roles
  assigned directly via ACLs (least-privilege). The legacy REST path is kept
  as `--via api` (roles + ACLs only; cannot capture the secret).
- **`proxcli-network` role**: new recommended role (`SDN.Audit,SDN.Use`)
  granted at `/sdn`. Attaching a VM NIC to an **SDN-managed bridge** (e.g.
  `vmbr0`) requires `SDN.Use` on top of `VM.Config.Network`; without it, VM
  creation fails at the `net0` step with HTTP 403
  `Permission check failed (/sdn, SDN.Use)`. `proxmox auth setup` now creates
  the role + ACL automatically, `proxmox auth status` checks SDN read access,
  and the stray-role allow-list includes it. `SDN.Allocate` (fabric
  create/modify) is intentionally excluded — proxcli only consumes existing
  SDN networks. See `docs/api-permissions.md`.

## [0.16.2] - 2026-06-30

### Added
- **``proxmox update``**: self-upgrade proxcli from PyPI. Queries the PyPI JSON
  API to check for new versions and uses ``uv tool install proxcli --reinstall``
  to upgrade in-place. ``--check`` flag reports available updates without
  installing. ``--pre`` includes pre-release versions.

## [0.16.1] - 2026-06-30

### Added
- **``proxmox vm disk import``**: import a disk image into an existing VM.
  Supports two sources:
  - ``--image <path>``: a disk image already on the PVE node filesystem
    (e.g. ``/var/lib/vz/import/deb13.qcow2``).
  - ``--url <url>``: downloads the image locally, uploads it to Proxmox
    storage via the API, then imports it into the VM — all in one command.
    The temp file is cleaned up automatically.  Wraps
    ``PUT /nodes/{node}/qemu/{vmid}/config`` with `import-from`.
- **Cloud-init auto-config**: ``vm create`` now automatically adds
  ``serial0=socket`` and ``vga=serial0`` when any cloud-init flags
  (``--citype``, ``--ciuser``, etc.) are present.  This matches the
  official Proxmox documentation and is required by Debian generic
  cloud images.

### Changed
- **Docs**: added ``vm disk import`` to README command reference;
  updated ``docs/cloud-init.md`` with ``--url`` import workflow;
  updated ``docs/production-automation.md`` with the new commands.

## [0.16.0] - 2026-06-30

### Added
- **``proxmox vm set``**: update VM configuration keys. Wraps
  ``PUT /nodes/{node}/qemu/{vmid}/config``. Supports ``--ipconfig0``–``--ipconfig3``,
  ``--ciuser``, ``--cipassword``, ``--sshkeys``, ``--nameserver``,
  ``--searchdomain``, ``--cicustom``, and arbitrary ``--option key=value`` pairs.
  Complements ``vm clone`` and ``vm template`` for full cloud-init template workflows.
- **``proxmox api``**: make raw authenticated API calls for endpoints not yet
  covered by dedicated subcommands. Supports ``GET``, ``POST``, ``PUT``, ``DELETE``
  with ``--data`` (inline JSON), ``--data-file`` (JSON file), or stdin piping.
  Reuses the same authentication as the rest of proxcli — no more ``curl`` with
  manual tokens.

### Changed
- **Docs deduplication**: ``docs/*.md`` is now the single source of truth.
  Removed ``docs/website/public/docs/`` (stale duplicate) and the ``copyDocsPlugin``
  from ``vite.config.js``. Added ``serveDocsPlugin`` middleware for dev mode.
- **``docs/cloud-init.md``**: added "Reusable Cloud-Init Template" guide covering
  the full workflow (upload → create → template → clone → customize) entirely
  with proxcli commands.
- **``docs/production-automation.md``**: replaced curl-based template conversion
  with ``proxmox vm template``.
- **``docs/quickstart.md``**: added "Raw API calls" section.

## [0.14.0] - 2026-06-22

### Added
- **``proxmox vm clone``**: clone a QEMU VM to a new VMID. Supports ``--newid``
  (required), ``--node``, ``--name``, ``--target-node``, ``--target-storage``,
  ``--full`` (1=full, 0=linked), ``--description``, and ``--pool``.
- **``proxmox vm migrate``**: migrate a QEMU VM to another node. Supports
  ``--target`` (required), ``--node``, ``--online`` (live migration),
  ``--with-local-disks``, and ``--target-storage``.
- **``proxmox backup restore``**: restore a backup to a new VM or container.
  Supports ``--vmid`` (required), ``--node``, ``--storage``, ``--unique``
  (unique MACs/IDs), ``--pool``, and ``--start``. Auto-detects guest type
  (qemu vs lxc) from the backup volume ID.
- **``proxmox vm template``**: convert a VM into a template. Wraps
  ``POST /nodes/{node}/qemu/{vmid}/template``.
- **``proxmox vm iso attach/detach``**: attach or eject an ISO image from
  a VM's virtual CD/DVD drive. ``attach --iso-volume`` accepts a full volid
  or a bare filename (auto-resolved across node storages).
- **``proxmox vm ip <vmid>``**: quick IP address lookup via guest agent.
  Returns interface name, IP, and prefix; filters out loopback and
  link-local addresses.
- **``proxmox container ip <vmid>``**: IP address lookup for LXC containers.
  Wraps ``GET /nodes/{node}/lxc/{vmid}/interfaces``, extracting inet/inet6
  addresses; filters loopback and link-local.
- **``proxmox vm disk resize``**: resize a VM disk. Wraps
  ``PUT /nodes/{node}/qemu/{vmid}/resize`` with ``--disk`` and ``--size``.
- **``proxmox vm agent`` new subcommands**: ``osinfo`` (guest OS details),
  ``fsinfo`` (filesystem info), ``users`` (user accounts), and ``exec``
  (execute a command inside the guest with base64 I/O decoding and result
  polling).
- **``proxmox vm disk detach/remove``**: detach (keep data) or remove
  (delete image) a disk from a VM. Wraps ``PUT /nodes/{node}/qemu/{vmid}/config``.
- **``proxmox task wait <upid>``**: block until a task completes. Polls
  task status at configurable ``--poll`` intervals with ``--timeout``.

### Fixed
- **Test suite**: all 102 tests now pass reliably. Root cause was the `.venv`
  referencing the old project path (`proxmox-cli` -> `proxcli`), causing
  `pytest-httpx` plugin not to load and subprocess tests to fail with
  `PackageNotFoundError`. Fixed by reinstalling dev dependencies into the
  current `.venv` and re-registering the editable install.

## [0.13.1] - 2026-06-21

### Fixed
- **``proxmox auth setup``**: now uses the correct ``tokens`` (plural) form
  parameter for token ACLs instead of ``tokenid``, which Proxmox's REST API
  doesn't accept.  Token-scoped ACLs are now created fully automatically.
- **Role permissions**: ``Pool.Allocate`` and ``Pool.Audit`` moved to
  ``proxcli-sys`` (pool operations check against ``/``, not ``/vms``).
  ``VM.GuestAgent.Audit`` added to ``proxcli-vm`` (guest agent checks
  against ``/vms/{id}``, not ``/nodes/{node}``).

### Added
- **``proxmox auth check``**: now prints each check inline with colored
  PASS (green) / FAIL (red) as it runs instead of only at the end.
  Also scans the token for leftover Administrator/PVEAdmin roles and
  warns to remove them after the proxcli roles are confirmed working.

## [0.13.0] - 2026-06-21

### Added
- **``--output log`` format**: plain-text log lines with timestamps.
  ``cluster log`` and ``ceph log`` default to this format.
- **``--follow`` / ``-f``** for ``cluster log`` and ``ceph log``:
  polls every second and prints new entries until Ctrl+C.
- **``proxmox auth setup``**: creates the four recommended
  ``proxcli-*`` roles and ACLs in one command (requires Administrator).
- **``proxmox auth check``**: live permission test — hits each proxcli
  endpoint and reports PASS/FAIL in a table.  39 checks across cluster,
  storage, VMs, snapshots, backups, containers, firewall, pools, and
  admin operations.
- **``proxmox auth status --permissions`` / ``-p``**: fetches effective
  permissions from the API.

### Changed
- **Cluster/ceph log output** is now oldest-first (reversed from API order).
- ``--help`` no longer triggers misplaced-global-flag hint.
- ``docs/api-permissions.md`` restructured around four path-scoped roles
  and a 3-step quickstart.

### Fixed
- Ctrl+C / broken pipe in ``--follow`` mode exits cleanly (no error).
- ``auth check`` defaults to table output.

## [0.12.0] - 2026-06-20

### Added
- **Node system info**: ``proxmox node subscription``, ``dns``, ``time``,
  ``services``, ``pci``, ``netstat``, ``config`` — read-only node inspection
  (subscription status, DNS config, timezone, systemd services, PCI devices,
  network statistics, node configuration).
- **Cluster log & options**: ``proxmox cluster log [--limit N]`` (cluster-wide
  log entries) and ``proxmox cluster options`` (migration network, keyboard,
  MAC prefix, allowed tags).
- **Storage status**: ``proxmox storage status <storage> [--node]`` shows
  usage stats per storage backend (total, used, available, content types).
- **Ceph & disk management**: ``proxmox ceph status`` (cluster health:
  OSDs, PGs, usage, monitors, warnings), ``proxmox ceph osd [--node]``
  (OSD list mapped to physical disks with model/size/wearout),
  ``proxmox ceph log [--node] [--limit N]`` (Ceph log entries),
  ``proxmox ceph disks [--node]`` (all physical disks with health,
  wearout, SMART status, OSD mapping).
- **``--output log`` format**: plain text log lines with timestamps.
  ``cluster log`` and ``ceph log`` default to this format.  Override with
  ``--output json``, ``--output table``, or ``--output yaml`.
- **API coverage doc**: ``docs/api-coverage.md`` tracks all implemented
  and remaining Proxmox VE REST API endpoints.

### Changed
- **ConfigLoader is now read-only**.  ``proxmox auth login`` and
  ``proxmox auth clear`` have been removed — proxcli never creates,
  modifies, or deletes ``credentials.json``.  Users must create this
  file manually.  Added ``PROXMOX_CONFIG_DIR`` env var for overriding
  the user config directory.
- **``--version`` outputs ``proxcli 0.11.0``** instead of
  ``proxmox 0.11.0`` to match the PyPI package name.

## [0.11.0] - 2026-06-20

### Added
- **VM config file (export/import)**: ``vm create --file spec.yaml`` reads
  a YAML spec in native Proxmox VM config format (flat key-value:
  ``name``, ``memory``, ``cores``, ``net0``, ``scsi0``, ``ciuser``, etc.).
  CLI flags override file values.  ``node:`` in the file acts as
  ``--node``.  ``vm config <vmid>`` exports a clean VM config (strips
  internal fields like ``digest``, ``vmgenid``), ready for ``--file``.
  Enable export → edit → recreate workflow.

## [0.10.0] - 2026-06-20

### Added
- **Network management**: ``proxmox network`` (list, show).  Wraps
  ``/nodes/{node}/network[/{iface}]``.  List all network interfaces on a
  node with optional ``--type`` filtering (bridge, bond, vlan, eth, etc.).
  Show detailed configuration for a single interface.
- **Backup (vzdump) management**: ``proxmox backup`` (list, show, create,
  delete, tasks, defaults).  Wraps ``/nodes/{node}/vzdump`` for creating
  backups and ``/nodes/{node}/storage/{storage}/content`` for listing
  and deleting backup files.  Supports snapshot/suspend/stop modes,
  compression (lzo/zstd), bandwidth limits, prune settings, and PBS
  Proxmox Backup Server integration.  Backup tasks can be monitored
  with ``proxmox task log <upid> --follow``.

## [0.9.1] - 2026-06-20

### Added
- **user, role, and ACL management**: ``proxmox user`` (list, show, create,
  update, delete), ``proxmox role`` (list, show, create, update, delete),
  ``proxmox acl`` (list, show, add, delete).  Wraps ``/access/users``,
  ``/access/roles``, and ``/access/acl`` endpoints.  ACL write operations
  require ``Permissions.Modify`` (Administrator role).

## [0.9.0] - 2026-06-20

### Added
- **vm create cloud-init support**: ``--citype``, ``--ciuser``,
  ``--cipassword``, ``--sshkeys`` (file path or inline),
  ``--nameserver``, ``--searchdomain``, ``--cicustom``.
- **vm create --import-from**: import an existing disk image from storage
  as the VM's boot disk (e.g. ``--import-from local:import/deb12.qcow2``).
  Requires a Proxmox storage with ``images`` or ``import`` content types.
- **vm cloud-init drive auto-creation**: when cloud-init flags are used
  on ``vm create``, an ``ide2`` cloud-init drive is automatically attached.
  Proxmox VE 9 regenerates the ISO on config change — no separate generate step.
- **vm cloudinit generate**: re-submits the current ``citype`` to trigger
  regeneration.  Adapted for Proxmox VE 9 which removed the
  ``POST /cloudinit`` endpoint.
- **docs/cloud-init.md**: complete guide on creating and managing
  cloud-init VMs with proxcli, including prerequisites, examples,
  custom user-data, and troubleshooting.
- **docs/api-permissions.md**: minimum API privilege reference for the
  cloud-init VM workflow and other proxcli operations.

## [0.8.2] - 2026-06-20

### Added
- **vm agent interfaces** — query QEMU guest agent for network interface
  and IP information via ``proxmox vm agent interfaces <vmid>``.
  Requires ``qemu-guest-agent`` in the VM.

### Fixed
- CI publish job now uses ``uv publish --check-url https://pypi.org/simple``
  to skip already-published versions instead of failing with "File already
  exists".

## [0.8.1] - 2026-06-20

### Added
- **vm snapshot** management: ``list``, ``create``, ``show``, ``rollback``,
  ``delete``.  Wraps ``/nodes/{node}/qemu/{vmid}/snapshot`` endpoints.

## [0.8.0] - 2026-06-20

### Fixed
- **vm create** now works against real Proxmox 9.x clusters.  The `--ostemplate`
  flag has been renamed to `--cdrom` (``ostemplate`` is an LXC parameter, not
  QEMU).  The handler now builds a raw form-encoded body to avoid httpx
  double-encoding ``%`` characters in IDE and network configuration strings.

### Changed
- **vm create** ``--net`` now uses ``action="append"`` so you can repeat it
  for multiple NICs (net0, net1, …).

### Added
- **vm create** gains new optional flags: ``--scsihw``, ``--bios``,
  ``--machine``, ``--boot``, ``--disk``.
- ``ProxmoxClient.request()`` now accepts a ``content`` keyword argument
  for sending a pre-encoded raw body instead of ``data``.

## [0.7.2] - 2026-06-20

### Added
- Helpful hint when global flags are placed after the resource subcommand.
  Running `proxmox vm list --output table` now shows:
  `Error: Global flag '--output' must come before the resource. Try: proxmox --output vm list ...`

## [0.7.1] - 2026-06-20

### Fixed
- API token authentication: Removed incorrect base64 encoding.
  Proxmox expects `PVEAPIToken=user@realm!tokenid=secret` as plain text
  in the Authorization header, not base64-encoded.
- Dry-run mode now always sets API token headers so that
  `--dry-run` output accurately reflects the Authorization header
  that would be sent. (Password auth is still skipped in dry-run
  since it requires a network call.)

## [0.7.0] - 2026-06-20

### Added
- Task log streaming: `proxmox task log <upid> [--follow]`.
  Without `--follow`, prints available log lines. With `--follow`,
  polls every second until the task exits (like `tail -f`).
  Also added `ProxmoxClient._extract_node_from_upid()` as a static helper.

## [0.6.0] - 2026-06-20

### Added
- Shell completion support: `proxmox completion bash|zsh|fish`.
  Generated scripts introspect the parser tree and stay in sync
  with all registered resources and actions.

## [0.5.0] - 2026-06-20

### Added
- Pool management (`proxmox pool`): list, show, create, update, delete.
  Wraps `/pools` endpoints.

## [0.4.0] - 2026-06-20

### Added
- Container firewall management: options, enable/disable, policy, rules (CRUD), refs.
  Uses `/nodes/{node}/lxc/{vmid}/firewall/*` endpoints.

## [0.3.0] - 2026-06-20

### Added
- Cluster firewall management: options, enable/disable, policy, rules (CRUD), aliases, ipsets (with CIDR management), refs.
- Node firewall management: options, enable/disable, policy, rules (CRUD), refs.
- VM firewall management: options, enable/disable, policy, rules (CRUD), refs.
- Shared `firewall_helpers.py` for consistent rule argument building across all levels.
- CI `publish` job: auto-publishes to PyPI on push to main (uses `PYPI_TOKEN` repo secret with `environment: pypi`).
- `AGENTS.md` with CLI convention and contribution guidelines.

### Changed
- Removed `.env` file with PyPI token; now uses GitHub Actions secrets.
- Firewall subcommands refactored to consistent `<resource> <action> <subresource> [subaction]` pattern.

## [0.2.1] - 2026-06-20

### Fixed
- `--version` now reads from installed package metadata (`importlib.metadata`) instead of a hardcoded string.

## [0.2.0] - 2026-06-20

### Added
- `proxmox storage upload` command for uploading ISO, vztmpl, and import files to storage via multipart/form-data.
- `ProxmoxClient.upload()` method supporting file uploads with content type selection.

### Changed
- `proxmox vm create --vmid` and `proxmox container create --vmid` are now optional.
  The next free VMID is auto-assigned via the `/cluster/nextid` API when omitted.

## [0.1.0] - 2026-06-20

### Added
- Initial release.
- `proxmox auth login|status|clear` — credential management (password + API token).
- `proxmox vm` subcommand: `list`, `show`, `create`, `start`, `stop`, `reboot`, `suspend`, `resume`, `delete`.
- `proxmox container` subcommand: `list`, `show`, `create`, `start`, `stop`, `delete`.
- `proxmox node` subcommand: `list`, `show`, `status`.
- `proxmox storage` subcommand: `list`, `show`, `content`.
- `proxmox cluster` subcommand: `status`.
- `proxmox task` subcommand: `list`, `show`.
- Output formats: `json` (default), `table` (rich), `yaml`.
- Global flags: `--dry-run`, `--insecure`, `--timeout`, `--verbose`, `--output`, `--password-stdin`.
- `PROXMOX_PASSWORD` environment variable support.
- Credential persistence in XDG config (`~/.config/proxmox-cli/credentials.json`, `0600`).
- Retry with exponential backoff on 5xx responses.
- CSRF ticket auto-refresh on 401.
- AI-agent-friendly: default JSON output, strict exit codes, `--dry-run` mode.

[Unreleased]: https://github.com/xezpeleta/proxcli/compare/v0.17.0...HEAD
[0.17.0]: https://github.com/xezpeleta/proxcli/releases/tag/v0.17.0
[0.16.2]: https://github.com/xezpeleta/proxcli/releases/tag/v0.16.2
[0.16.1]: https://github.com/xezpeleta/proxcli/releases/tag/v0.16.1
[0.16.0]: https://github.com/xezpeleta/proxcli/releases/tag/v0.16.0
[0.15.0]: https://github.com/xezpeleta/proxcli/releases/tag/v0.15.0
[0.14.0]: https://github.com/xezpeleta/proxcli/releases/tag/v0.14.0
[0.13.1]: https://github.com/xezpeleta/proxcli/releases/tag/v0.13.1
[0.13.0]: https://github.com/xezpeleta/proxcli/releases/tag/v0.13.0
[0.12.0]: https://github.com/xezpeleta/proxcli/releases/tag/v0.12.0
[0.11.0]: https://github.com/xezpeleta/proxcli/releases/tag/v0.11.0
[0.10.0]: https://github.com/xezpeleta/proxcli/releases/tag/v0.10.0
[0.9.1]: https://github.com/xezpeleta/proxcli/releases/tag/v0.9.1
[0.9.0]: https://github.com/xezpeleta/proxcli/releases/tag/v0.9.0
[0.8.2]: https://github.com/xezpeleta/proxcli/releases/tag/v0.8.2
[0.8.1]: https://github.com/xezpeleta/proxcli/releases/tag/v0.8.1
[0.8.0]: https://github.com/xezpeleta/proxcli/releases/tag/v0.8.0
[0.7.2]: https://github.com/xezpeleta/proxcli/releases/tag/v0.7.2
[0.7.1]: https://github.com/xezpeleta/proxcli/releases/tag/v0.7.1
[0.7.0]: https://github.com/xezpeleta/proxcli/releases/tag/v0.7.0
[0.6.0]: https://github.com/xezpeleta/proxcli/releases/tag/v0.6.0
[0.5.0]: https://github.com/xezpeleta/proxcli/releases/tag/v0.5.0
[0.4.0]: https://github.com/xezpeleta/proxcli/releases/tag/v0.4.0
[0.3.0]: https://github.com/xezpeleta/proxcli/releases/tag/v0.3.0
[0.2.1]: https://github.com/xezpeleta/proxcli/releases/tag/v0.2.1
[0.2.0]: https://github.com/xezpeleta/proxcli/releases/tag/v0.2.0
[0.1.1]: https://github.com/xezpeleta/proxcli/releases/tag/v0.1.1
[0.1.0]: https://github.com/xezpeleta/proxcli/releases/tag/v0.1.0
