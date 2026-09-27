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
    log.add_argument("--follow", "-f", action="store_true", help="Follow log output")
    log.set_defaults(func=_ceph_log, output_format="log")

    # --- ceph osd ---
    osd = ceph_sub.add_parser(
        "osd",
        help="List Ceph OSDs with disk health, wearout, and capacity utilization",
    )
    osd.add_argument("--node", help="Filter OSDs by node")
    osd.set_defaults(func=_ceph_osd)

    # --- ceph pool ---
    pool = ceph_sub.add_parser(
        "pool",
        help="List Ceph pools with capacity and PG stats",
    )
    pool.add_argument(
        "--node",
        help="Node to query (pools are cluster-wide; this selects which node to ask)",
    )
    pool.set_defaults(func=_ceph_pool)

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


def _ceph_log(args: argparse.Namespace, client: ProxmoxClient) -> list | None:
    """Fetch Ceph log entries."""
    if args.follow:
        # Follow only works with --node for ceph log (per-node endpoint)
        if not args.node:
            return {"error": "--follow requires --node for Ceph logs"}
        client.stream_log(
            f"/nodes/{args.node}/ceph/log", follow=True,
            params={"limit": args.limit},
        )
        return None

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

    return list(reversed([
        {
            "time": entry.get("t", ""),
            "node": entry.get("_node", ""),
        }
        for entry in entries
    ]))


def _flatten_crush_tree(root: dict) -> dict[str, dict]:
    """Flatten a Ceph CRUSH tree into ``{osd_id_str: osd_node_dict}``.

    The ``/nodes/{node}/ceph/osd`` endpoint returns a nested CRUSH tree
    (``root → host → osd``). This walks it recursively and indexes leaf OSD
    nodes by their numeric id (as a string, matching the ``osdid`` field on
    disk-inventory records so the two can be joined).
    """
    osds: dict[str, dict] = {}

    def walk(node: dict) -> None:
        if not isinstance(node, dict):
            return
        if node.get("type") == "osd":
            osd_id = node.get("id")
            if osd_id is not None:
                osds[str(osd_id)] = node
        for child in node.get("children", []) or []:
            walk(child)

    walk(root)
    return osds


def _ceph_osd(args: argparse.Namespace, client: ProxmoxClient) -> list:
    """List Ceph OSDs with disk health, wearout, and capacity utilization.

    Merges two endpoints:
      * ``/nodes/{node}/disks/list`` — physical disk inventory (health,
        wearout, model, device path).
      * ``/nodes/{node}/ceph/osd`` — the CRUSH tree carrying per-OSD
        utilization (``percent_used``, ``bytes_used``, ``reweight``,
        ``status``). The CRUSH tree is cluster-wide, so querying one node
        returns every OSD; disk inventory is still scanned per-node so each
        OSD is attributed to its host.

    The PVE API returns OSD ``percent_used`` on a 0–100 scale.
    """
    if args.node:
        health_nodes = [{"node": args.node}]
        crush_query_nodes = [args.node]
    else:
        all_nodes = client.get("/nodes")
        if not isinstance(all_nodes, list):
            all_nodes = []
        health_nodes = all_nodes
        crush_query_nodes = [
            n["node"] for n in all_nodes if isinstance(n, dict) and n.get("node")
        ]

    # The CRUSH tree is cluster-wide; query the first node that returns one.
    crush_osds: dict[str, dict] = {}
    for node_name in crush_query_nodes:
        try:
            data = client.get(f"/nodes/{node_name}/ceph/osd")
            root = data.get("root") if isinstance(data, dict) else None
            if root:
                crush_osds = _flatten_crush_tree(root)
                break
        except Exception:
            continue

    results = []
    for node in health_nodes:
        node_name = node["node"]
        try:
            disks_data = client.get(f"/nodes/{node_name}/disks/list")
            for disk in disks_data:
                osdid = disk.get("osdid")
                if osdid is None or str(osdid) in ("-1", ""):
                    continue
                crush = crush_osds.get(str(osdid), {})
                results.append(
                    {
                        "osd": osdid,
                        "node": node_name,
                        "device": disk.get("devpath", ""),
                        "model": disk.get("model", ""),
                        "size_gb": round(disk.get("size", 0) / (1024**3), 1),
                        "used_gb": round(crush["bytes_used"] / (1024**3), 1)
                        if crush.get("bytes_used") is not None
                        else None,
                        "used_pct": round(crush["percent_used"], 1)
                        if crush.get("percent_used") is not None
                        else None,
                        "reweight": crush.get("reweight"),
                        "status": crush.get("status"),
                        "in_cluster": bool(crush.get("in", 0)) if crush else None,
                        "type": disk.get("type", ""),
                        "health": disk.get("health", ""),
                        "wearout": f"{disk.get('wearout', '')}%" if disk.get("wearout") else "",
                    }
                )
        except Exception:
            pass

    return sorted(results, key=lambda r: r["osd"])


def _format_pool(p: dict) -> dict:
    """Normalize a raw Ceph pool record for display.

    The PVE API returns pool ``percent_used`` as a 0–1 ratio (unlike the OSD
    tree, which uses 0–100). Normalized here to a 0–100 number.
    """
    pct = p.get("percent_used")
    bytes_used = p.get("bytes_used") or 0
    return {
        "pool": p.get("pool"),
        "name": p.get("pool_name", p.get("name", "")),
        "type": p.get("type", "replicated"),
        "size": p.get("size"),
        "pgs": p.get("pg_num"),
        "bytes_used": bytes_used,
        "used_gb": round(bytes_used / (1024**3), 1),
        "percent_used": round(float(pct) * 100, 1) if pct is not None else None,
        "max_avail": p.get("max_avail"),
        "target_size_ratio": p.get("target_size_ratio"),
        "crush_rule": p.get("crush_rule_name"),
        "applications": ", ".join(sorted((p.get("application_metadata") or {}).keys())),
    }


def _ceph_pool(args: argparse.Namespace, client: ProxmoxClient) -> list | dict:
    """List Ceph pools with capacity and PG stats.

    Pools are cluster-wide: the ``/nodes/{node}/ceph/pool`` endpoint returns
    the full pool list regardless of which node is queried. If ``--node`` is
    given that node is queried directly; otherwise nodes are scanned until one
    returns a pool list (i.e. a node running the Ceph manager).
    """
    if args.node:
        query_nodes = [args.node]
    else:
        all_nodes = client.get("/nodes")
        if not isinstance(all_nodes, list):
            all_nodes = []
        query_nodes = [
            n["node"] for n in all_nodes if isinstance(n, dict) and n.get("node")
        ]

    for node_name in query_nodes:
        try:
            data = client.get(f"/nodes/{node_name}/ceph/pool")
            if isinstance(data, list):
                pools = [_format_pool(p) for p in data if isinstance(p, dict)]
                return sorted(
                    pools, key=lambda r: (r["pool"] if r["pool"] is not None else 0)
                )
        except Exception:
            continue

    return {"error": "No Ceph pool information available (is Ceph running on any node?)"}


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
