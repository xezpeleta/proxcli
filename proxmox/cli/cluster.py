"""`proxmox cluster` subcommand — cluster management."""

from __future__ import annotations

import argparse

from proxmox.client.client import ProxmoxClient


def register_cluster_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the `proxmox cluster` subcommand tree."""
    cl_parser = subparsers.add_parser("cluster", help="Manage Proxmox cluster")
    cl_sub = cl_parser.add_subparsers(dest="action", title="actions", required=True)

    # --- cluster status ---
    cl_status = cl_sub.add_parser("status", help="Show cluster status")
    cl_status.set_defaults(func=_cl_status)


def _cl_status(args: argparse.Namespace, client: ProxmoxClient) -> dict | list:
    return client.get("/cluster/status")
