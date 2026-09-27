"""Shared helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from proxmox.client.client import ProxmoxClient


def vmid_type(value: str) -> int:
    """Argparse type for validating VMID (positive integer)."""
    try:
        v = int(value)
    except ValueError:
        raise ValueError(f"Invalid VMID '{value}': must be an integer")
    if v <= 0:
        raise ValueError(f"Invalid VMID '{value}': must be positive")
    return v


def attach_node(record: dict, node: str | None) -> None:
    """Inject the hosting node name into a result record in place.

    Sets **both** ``node`` and ``_node``:
    - ``node``  — the ergonomic key agents and humans look for first.
    - ``_node`` — the historical underscore-prefixed key (denotes a field
      proxcli injects rather than one returned by the Proxmox API), kept so
      existing scripts and tests keep working.

    Proxmox's per-node ``/qemu`` and ``/lxc`` listings omit the node name
    from each entry, so this is how the hosting node travels with a record.
    """
    if node and isinstance(record, dict):
        record["node"] = node
        record["_node"] = node


def resolve_vmid(client: ProxmoxClient, vmid: int | None) -> int:
    """Return *vmid* if provided, otherwise fetch the next free VMID from the cluster."""
    if vmid is not None and vmid > 0:
        return vmid
    result = client.get("/cluster/nextid")
    if isinstance(result, dict):
        # Proxmox returns {"data": "<nextid>"} or just "<nextid>" as string
        raw = result.get("data", result)
        if isinstance(raw, str):
            return int(raw)
    return int(result) if isinstance(result, (str, int)) else 0
