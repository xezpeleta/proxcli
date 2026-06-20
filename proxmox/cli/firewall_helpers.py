"""Firewall helpers shared across cluster, node, and VM subcommands."""

from __future__ import annotations

import argparse
from typing import Any

# ---------------------------------------------------------------------------
# Rule argument builder — shared across all firewall levels
# ---------------------------------------------------------------------------


def add_firewall_rule_args(parser: argparse.ArgumentParser) -> None:
    """Add common rule-form arguments to a parser."""
    parser.add_argument("--action", required=True, choices=["ACCEPT", "DENY", "REJECT"],
                        help="Rule action")
    parser.add_argument("--type", default="in", choices=["in", "out"],
                        help="Traffic direction (default: in)")
    parser.add_argument("--iface", default=None, help="Network interface (e.g. net0)")
    parser.add_argument("--source", default=None, help="Source IP/CIDR")
    parser.add_argument("--dest", default=None, help="Destination IP/CIDR")
    parser.add_argument("--dport", default=None, help="Destination port")
    parser.add_argument("--sport", default=None, help="Source port")
    parser.add_argument("--proto", default=None, choices=["tcp", "udp", "icmp", "any"],
                        help="Protocol")
    parser.add_argument("--comment", default=None, help="Comment / description")
    parser.add_argument("--enable", type=int, default=1, choices=[0, 1],
                        help="Enable the rule (default: 1)")
    parser.add_argument("--macro", default=None, help="Pre-defined macro (e.g. SSH, HTTP)")
    parser.add_argument("--log", default=None, choices=["emerg", "alert", "crit", "err",
                          "warning", "notice", "info", "debug", "nolog"],
                        help="Log level")


def build_rule_data(args: argparse.Namespace) -> dict[str, Any]:
    """Convert parsed firewall rule args into the POST body dict."""
    data: dict[str, Any] = {
        "action": args.action,
        "type": args.type,
        "enable": args.enable,
    }
    if args.macro:
        data["macro"] = args.macro
    if args.iface:
        data["iface"] = args.iface
    if args.source:
        data["source"] = args.source
    if args.dest:
        data["dest"] = args.dest
    if args.dport:
        data["dport"] = args.dport
    if args.sport:
        data["sport"] = args.sport
    if args.proto and not args.macro:
        data["proto"] = args.proto
    if args.comment:
        data["comment"] = args.comment
    if args.log:
        data["log"] = args.log
    return data
