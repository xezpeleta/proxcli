# Agent Guidelines for proxmox CLI

## CLI Command Convention

All commands follow a strict **`<resource> <action> [positional_id] [--flags]`** pattern:

```
proxmox <resource> <action> [id_or_name] [--options]
```

### Resource-level (top-level subcommands)

Every resource is a noun: `vm`, `container`, `node`, `storage`, `cluster`, `task`, `auth`.

Each has actions as verbs: `list`, `show`, `create`, `start`, `stop`, `delete`, etc.

```
proxmox vm list
proxmox vm show 100
proxmox vm start 100
proxmox node show pve01
proxmox container list
```

### Nested resources (firewall, etc.)

When a resource has sub-resources, use the same **`<resource> <action> <subresource> [subaction]`** pattern:

```
proxmox cluster firewall rules                         # list (shorthand)
proxmox cluster firewall rules list                    # list (explicit)
proxmox cluster firewall rules add --action ACCEPT ...
proxmox cluster firewall rules show <pos>
proxmox cluster firewall rules delete <pos>
proxmox vm firewall rules list <vmid>
proxmox vm firewall rules add <vmid> --action ACCEPT ...
proxmox node firewall rules list <node_name>
proxmox node firewall rules add <node_name> --action ACCEPT ...
proxmox cluster firewall aliases                       # list (shorthand)
proxmox cluster firewall aliases add <name> --cidr ...
proxmox cluster firewall ipsets                        # list (shorthand)
proxmox cluster firewall ipsets add <name> ...
```

### Key rules

1. **Nouns before verbs** — `proxmox vm firewall rules list`, NOT `proxmox vm firewall list-rules`.
2. **Resource identifiers are positional arguments**, placed after the action verb:
   - `proxmox vm show 100` (vmid is positional)
   - `proxmox node show pve01` (node_name is positional)
   - `proxmox vm firewall rules show 100 3` (vmid then pos)
3. **`--node` is always an optional flag** for VM/container commands (auto-detected if omitted), except on `create` where it's required.
4. **No shorthand noun squeezing** — `proxmox vm fw` is NOT acceptable. Always use full resource names.
5. **Subcommands inherit `--flags` from parents** via `set_defaults(func=handler)`. Each handler function receives the merged `Namespace`.

## Parser Registration

Each CLI module has a `register_<resource>_parser(subparsers)` function that adds subparsers to the passed-in `_SubParsersAction`. Example:

```python
def register_vm_parser(subparsers: argparse._SubParsersAction) -> None:
    vm_parser = subparsers.add_parser("vm", help="Manage QEMU virtual machines")
    vm_sub = vm_parser.add_subparsers(dest="action", title="actions", required=True)

    vm_list = vm_sub.add_parser("list", help="List virtual machines")
    vm_list.add_argument("--node", help="Filter by node name")
    vm_list.set_defaults(func=_vm_list)
```

For nested resources (like firewall), use a second `dest` name to track the sub-resource:

```python
fw = vm_sub.add_parser("firewall", help="Manage VM firewall")
fw_sub = fw.add_subparsers(dest="fw_resource", title="resources", required=True)

rules = fw_sub.add_parser("rules", help="Manage VM firewall rules")
rules_sub = rules.add_subparsers(dest="fw_action", title="rule actions", required=False)
rules_list = rules_sub.add_parser("list", help="List rules")
rules_list.add_argument("vmid", type=vmid_type, help="VM ID")
rules_list.set_defaults(func=_vm_fw_rules)
```

## Handler Functions

Every handler has the signature:

```python
def _handler(args: argparse.Namespace, client: ProxmoxClient) -> dict | list:
```

- `args` contains all parsed arguments (global + resource-specific)
- `client` is the authenticated `ProxmoxClient` instance
- Returns a dict or list that will be formatted by the output system
- For errors, return `{"error": "message"}` dict

## Shared Helpers

Shared argument definitions go in helper modules (e.g., `firewall_helpers.py`). They export two functions:

```python
def add_firewall_rule_args(parser: argparse.ArgumentParser) -> None:
    """Add common rule-form arguments to a parser."""

def build_rule_data(args: argparse.Namespace) -> dict[str, Any]:
    """Convert parsed args into the POST/PUT body dict."""
```

## Testing

- Unit tests use `pytest-httpx` to mock API responses
- Integration tests use `subprocess.run` to invoke the CLI binary
- Dry-run tests verify the URL, method, and body without real network calls

## Versioning

The version string is read from `importlib.metadata.version('proxcli')` — never hardcoded in source.

## PyPI

- Package name: `proxcli`
- CLI binary: `proxmox`
- Publish via `uv publish --token $PYPI_TOKEN`
- CI auto-publishes on push to `main` (after lint + test + build)
