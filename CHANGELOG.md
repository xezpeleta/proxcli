# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **`--columns` global flag**: select which columns appear in table output.
  Example: ``proxmox --output table --columns vmid,name,status vm list``.
- **Colorized table output**: status/state values are styled with colors
  (green for running/active/ok, red for stopped/error, yellow for paused).

## [Unreleased]

### Added
- **VM config file (export/import)**: ``vm create --file spec.yaml`` reads
  a YAML spec in native Proxmox VM config format (flat key-value:
  ``name``, ``memory``, ``cores``, ``net0``, ``scsi0``, ``ciuser``, etc.).
  CLI flags override file values.  ``node:`` in the file acts as
  ``--node``.  ``vm config <vmid>`` exports a clean VM config (strips
  internal fields like ``digest``, ``vmgenid``), ready for ``--file``.
  Enable export → edit → recreate workflow.
- **`--columns` global flag**: select which columns appear in table output.
  Example: ``proxmox --output table --columns vmid,name,status vm list``.
- **Colorized table output**: status/state values are styled with colors
  (green for running/active/ok, red for stopped/error, yellow for paused).

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
