"""Helpers for reading YAML-based VM spec files."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def load_vm_spec(filepath: str) -> dict[str, Any]:
    """Load a VM specification from a YAML file.

    The file uses the native Proxmox VM config format — flat key-value
    pairs with keys like: name, memory, cores, net0, scsi0, ciuser, etc.

    Also supports YAML-specific convenience features:
    - ``sshkeys: ~/.ssh/id_rsa.pub`` → file path is read and URL-encoded
    - ``node: <name>`` → extracted for API URL path (not sent as body param)
    - Multi-line values for ``description``, ``sshkeys``, etc.

    Returns:
        dict with keys matching Proxmox VM config API parameters,
        plus ``_node`` if ``node:`` was specified in the file.
    """
    try:
        import yaml
    except ImportError:
        return {"error": "YAML support requires pyyaml. Install with: uv add pyyaml"}

    path = Path(filepath)
    if not path.exists():
        return {"error": f"File not found: {filepath}"}

    try:
        with open(path) as f:
            spec = yaml.safe_load(f)
    except yaml.YAMLError as e:
        return {"error": f"Invalid YAML in {filepath}: {e}"}

    if not isinstance(spec, dict):
        return {"error": f"VM spec file must contain a YAML mapping, got {type(spec).__name__}"}

    return _normalize_spec(spec, filepath)


# Keys that are proxcli-internal and should NOT be sent as API body params
_INTERNAL_KEYS = {"node", "vmid", "sshkeys_file"}

# Keys that are Proxmox-internal and should NOT appear in clean export
_CONFIG_CLEAN_STRIP = {
    "digest", "vmgenid", "smbios1", "meta", "parent",
    "hotplug", "tablet", "vga", "numa",
}


def _normalize_spec(spec: dict[str, Any], filepath: str) -> dict[str, Any]:
    """Post-process a YAML spec: read sshkeys files, normalize types."""
    result: dict[str, Any] = {}

    # Extract node separately
    if "node" in spec:
        result["_node"] = str(spec.pop("node"))

    for key, value in spec.items():
        if value is None:
            continue

        if key == "sshkeys":
            value = _resolve_sshkeys(value, filepath)
        elif isinstance(value, bool):
            value = 1 if value else 0
        elif isinstance(value, (int, float)):
            value = str(value)
        elif isinstance(value, str):
            value = str(value)

        result[key] = value

    return result


def _resolve_sshkeys(value: Any, filepath: str) -> str:
    """Resolve sshkeys value — it can be a file path, a list of paths, or inline content.

    Returns a URL-encoded string suitable for the Proxmox API form body.
    """
    if isinstance(value, list):
        # Multiple SSH keys or file paths
        keys_content = ""
        for entry in value:
            entry_str = str(entry)
            try:
                with open(entry_str) as f:
                    keys_content += f.read().strip() + "\n"
            except (OSError, FileNotFoundError):
                keys_content += entry_str.strip() + "\n"
        value = keys_content.strip()
    elif isinstance(value, str):
        # Single value: try as file path first, fall back to inline
        try:
            if not value.startswith("ssh-"):
                with open(value) as f:
                    value = f.read().strip()
        except (OSError, FileNotFoundError):
            # It's inline content, use as-is
            pass

    # URL-encode for form body
    return (value
            .replace("\n", "%0A")
            .replace("\r", "%0D")
            .replace("=", "%3D")
            .replace(",", "%2C")
            .replace(":", "%3A"))


def clean_vm_config(config: dict[str, Any]) -> dict[str, Any]:
    """Strip internal Proxmox fields from a VM config, producing a clean
    spec suitable for ``--file`` import.

    Removes: digest, vmgenid, smbios1, meta, parent, and similar fields
    that are auto-generated and shouldn't be reused across VMs.
    """
    return {k: v for k, v in config.items() if k not in _CONFIG_CLEAN_STRIP}
