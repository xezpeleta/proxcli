"""CLI subcommand for ACL management (`proxmox acl`)."""

from __future__ import annotations

import argparse

from ..client.client import ProxmoxClient

# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------

def _acl_list(args: argparse.Namespace, client: ProxmoxClient) -> list | dict:
    result = client.get("/access/acl")
    if isinstance(result, list):
        return result
    if isinstance(result, dict) and "data" in result:
        return result["data"]
    return result


def _acl_show(args: argparse.Namespace, client: ProxmoxClient) -> dict | list:
    params = {"path": args.path}
    result = client.get("/access/acl", params=params)
    if isinstance(result, dict) and "data" in result:
        return result["data"]
    return result


def _acl_create(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    data: dict = {
        "path": args.path,
        "roles": args.roles,
    }
    if args.users:
        data["users"] = args.users
    if args.groups:
        data["groups"] = args.groups
    if args.tokens:
        data["tokens"] = args.tokens
    if args.propagate is False:
        data["propagate"] = 0
    return client.put("/access/acl", data=data)


def _acl_delete(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    data: dict = {"path": args.path}
    if args.roles:
        data["roles"] = args.roles
    if args.users:
        data["users"] = args.users
    if args.groups:
        data["groups"] = args.groups
    if args.tokens:
        data["tokens"] = args.tokens
    return client.put("/access/acl", data={"delete": 1, **data})


# ---------------------------------------------------------------------------
# Parser registration
# ---------------------------------------------------------------------------

def register_acl_parser(subparsers: argparse._SubParsersAction) -> None:
    acl_parser = subparsers.add_parser("acl", help="Manage ACLs")
    acl_sub = acl_parser.add_subparsers(dest="action", title="actions", required=True)

    # acl list
    acl_list = acl_sub.add_parser("list", help="List all ACLs")
    acl_list.set_defaults(func=_acl_list)

    # acl show
    acl_show = acl_sub.add_parser("show", help="Show ACLs for a path")
    acl_show.add_argument("path", help="ACL path (e.g. /vms/100)")
    acl_show.set_defaults(func=_acl_show)

    # acl create
    acl_create = acl_sub.add_parser("add", help="Add ACL entry")
    acl_create.add_argument("path", help="ACL path (e.g. /vms)")
    acl_create.add_argument("--roles", help="Comma-separated role IDs")
    acl_create.add_argument("--users", help="Comma-separated user IDs")
    acl_create.add_argument("--groups", help="Comma-separated group IDs")
    acl_create.add_argument("--tokens", help="Comma-separated token IDs")
    acl_create.add_argument("--no-propagate", dest="propagate", action="store_false",
                            default=True,
                            help="Disable permission propagation to children")
    acl_create.set_defaults(func=_acl_create)

    # acl delete
    acl_delete = acl_sub.add_parser("delete", help="Remove ACL entry")
    acl_delete.add_argument("path", help="ACL path (e.g. /vms)")
    acl_delete.add_argument("--roles", help="Comma-separated role IDs")
    acl_delete.add_argument("--users", help="Comma-separated user IDs")
    acl_delete.add_argument("--groups", help="Comma-separated group IDs")
    acl_delete.add_argument("--tokens", help="Comma-separated token IDs")
    acl_delete.set_defaults(func=_acl_delete)
