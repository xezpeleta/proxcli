# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
