"""`proxmox ceph` subcommand — Ceph cluster and disk management."""

from __future__ import annotations

import argparse

from proxmox.client.client import ProxmoxClient


def register_ceph_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the `proxmox ceph` subcommand tree."""
    ceph_parser = subparsers.add_parser("ceph", help="Manage Ceph cluster")
    ceph_sub = ceph_parser.add_subparsers(dest="action", title="actions", required=True)

    # --- ceph status ---
    status = ceph_sub.add_parser("status", help="Show Ceph cluster health status")
    status.set_defaults(func=_ceph_status)

    # --- ceph log ---
    log = ceph_sub.add_parser("log", help="Show recent Ceph log entries")
    log.add_argument("--node", help="Show logs for a specific node (default: all nodes)")
    log.add_argument("--limit", type=int, default=50, help="Number of log entries (default: 50)")
    log.set_defaults(func=_ceph_log)

    # --- ceph osd ---
    osd = ceph_sub.add_parser("osd", help="List Ceph OSDs")
    osd.add_argument("--node", help="Filter OSDs by node")
    osd.set_defaults(func=_ceph_osd)

    # --- ceph disks ---
    disks = ceph_sub.add_parser("disks", help="List physical disks across nodes")
    disks.add_argument("--node", help="Filter disks by node")
    disks.set_defaults(func=_ceph_disks)


def _ceph_status(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    """Fetch Ceph cluster health status."""
    data = client.get("/cluster/ceph/status")

    health = data.get("health", {})
    osdmap = data.get("osdmap", {})
    pgmap = data.get("pgmap", {})
    monmap = data.get("monmap", {})

    # Format a human-readable summary
    issues = []
    checks = health.get("checks", {})
    for check_name, check_data in checks.items():
        summary = check_data.get("summary", {})
        msg = summary.get("message", "")
        if msg:
            severity = check_data.get("severity", "HEALTH_WARN")
            issues.append(f"[{severity}] {msg}")

    pgs_by_state = pgmap.get("pgs_by_state", [])
    pg_summary = ", ".join(
        f"{s.get('count', 0)} {s.get('state_name', '?')}" for s in pgs_by_state
    )

    return {
        "health": health.get("status", "unknown"),
        "issues": issues,
        "osds": {
            "total": osdmap.get("num_osds", 0),
            "up": osdmap.get("num_up_osds", 0),
            "in": osdmap.get("num_in_osds", 0),
        },
        "pgs": {
            "total": pgmap.get("num_pgs", 0),
            "summary": pg_summary,
        },
        "usage": {
            "data_bytes": pgmap.get("data_bytes", 0),
            "used_bytes": pgmap.get("bytes_used", 0),
            "total_bytes": pgmap.get("bytes_total", 0),
        },
        "monitors": len(monmap.get("mons", [])),
        "quorum": ", ".join(data.get("quorum_names", [])),
    }


def _ceph_log(args: argparse.Namespace, client: ProxmoxClient) -> list:
    """Fetch Ceph log entries."""
    if args.node:
        node_list = [args.node]
    else:
        node_list = [n["node"] for n in client.get("/nodes")]

    all_entries = []
    per_node_limit = max(10, args.limit // max(len(node_list), 1))
    for node_name in node_list:
        try:
            data = client.get(
                f"/nodes/{node_name}/ceph/log", params={"limit": per_node_limit}
            )
            for entry in data:
                entry["_node"] = node_name
                all_entries.append(entry)
        except Exception:
            pass

    all_entries.sort(key=lambda e: e.get("t", ""), reverse=True)
    entries = all_entries[: args.limit]

    return [
        {
            "time": entry.get("t", ""),
            "node": entry.get("_node", ""),
        }
        for entry in entries
    ]


def _ceph_osd(args: argparse.Namespace, client: ProxmoxClient) -> list:
    """List Ceph OSDs with health info."""
    if args.node:
        node_list = [{"node": args.node}]
    else:
        node_list = client.get("/nodes")

    results = []
    for node in node_list:
        node_name = node["node"]
        try:
            disks_data = client.get(f"/nodes/{node_name}/disks/list")
            for disk in disks_data:
                osdid = disk.get("osdid")
                if osdid is not None and osdid != -1 and str(osdid) != "-1":
                    results.append(
                        {
                            "osd": osdid,
                            "node": node_name,
                            "device": disk.get("devpath", ""),
                            "model": disk.get("model", ""),
                            "size_gb": round(disk.get("size", 0) / (1024**3), 1),
                            "type": disk.get("type", ""),
                            "health": disk.get("health", ""),
                            "wearout": f"{disk.get('wearout', '')}%" if disk.get("wearout") else "",
                        }
                    )
        except Exception:
            pass

    return sorted(results, key=lambda r: r["osd"])


def _ceph_disks(args: argparse.Namespace, client: ProxmoxClient) -> list:
    """List physical disks across all nodes or a specific node."""
    if args.node:
        node_list = [args.node]
    else:
        node_list = [n["node"] for n in client.get("/nodes")]

    results = []
    for node_name in node_list:
        try:
            disks_data = client.get(f"/nodes/{node_name}/disks/list")
            disks = disks_data if isinstance(disks_data, list) else []
            for disk in disks:
                results.append(
                    {
                        "node": node_name,
                        "device": disk.get("devpath", ""),
                        "model": disk.get("model", ""),
                        "serial": disk.get("serial", ""),
                        "size_gb": round(disk.get("size", 0) / (1024**3), 1),
                        "type": disk.get("type", ""),
                        "health": disk.get("health", ""),
                        "wearout": f"{disk.get('wearout', '')}%" if disk.get("wearout") else "",
                        "osd": disk.get("osdid", -1) if disk.get("osdid", -1) not in (-1, None) and str(disk.get("osdid", -1)) != "-1" else "",
                        "used": disk.get("used", ""),
                    }
                )
        except Exception:
            pass

    return results
