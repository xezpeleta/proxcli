"""Shared helpers."""

from __future__ import annotations


def vmid_type(value: str) -> int:
    """Argparse type for validating VMID (positive integer)."""
    try:
        v = int(value)
    except ValueError:
        raise ValueError(f"Invalid VMID '{value}': must be an integer")
    if v <= 0:
        raise ValueError(f"Invalid VMID '{value}': must be positive")
    return v
