# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
