# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[0.2.0]: https://github.com/xezpeleta/proxcli/releases/tag/v0.2.0
[0.1.1]: https://github.com/xezpeleta/proxcli/releases/tag/v0.1.1
[0.1.0]: https://github.com/xezpeleta/proxcli/releases/tag/v0.1.0
