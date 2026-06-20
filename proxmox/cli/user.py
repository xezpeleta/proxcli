"""CLI subcommand for user management (`proxmox user`)."""

from __future__ import annotations

import argparse

from ..client.client import ProxmoxClient

# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------

def _user_list(args: argparse.Namespace, client: ProxmoxClient) -> list | dict:
    result = client.get("/access/users")
    if isinstance(result, list):
        return result
    if isinstance(result, dict) and "data" in result:
        return result["data"]
    return result


def _user_show(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    return client.get(f"/access/users/{args.userid}")


def _user_create(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    data: dict = {"userid": args.userid}
    if args.password:
        data["password"] = args.password
    if args.email:
        data["email"] = args.email
    if args.firstname:
        data["firstname"] = args.firstname
    if args.lastname:
        data["lastname"] = args.lastname
    if args.enable is False:
        data["enable"] = 0
    if args.expire is not None:
        data["expire"] = args.expire
    if args.group:
        data["groups"] = ",".join(args.group)
    return client.post("/access/users", data=data)


def _user_update(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    data: dict = {}
    if args.password:
        data["password"] = args.password
    if args.email:
        data["email"] = args.email
    if args.firstname:
        data["firstname"] = args.firstname
    if args.lastname:
        data["lastname"] = args.lastname
    if args.enable is not False:
        data["enable"] = 0
    if args.expire is not None:
        data["expire"] = args.expire
    if args.group:
        data["groups"] = ",".join(args.group)
    if not data:
        return {"error": "No fields to update"}
    return client.put(f"/access/users/{args.userid}", data=data)


def _user_delete(args: argparse.Namespace, client: ProxmoxClient) -> dict:
    return client.delete(f"/access/users/{args.userid}")


# ---------------------------------------------------------------------------
# Parser registration
# ---------------------------------------------------------------------------

def register_user_parser(subparsers: argparse._SubParsersAction) -> None:
    user_parser = subparsers.add_parser("user", help="Manage users")
    user_sub = user_parser.add_subparsers(dest="action", title="actions", required=True)

    # user list
    user_list = user_sub.add_parser("list", help="List users")
    user_list.set_defaults(func=_user_list)

    # user show
    user_show = user_sub.add_parser("show", help="Show user details")
    user_show.add_argument("userid", help="User ID (e.g. xezpeleta@pve)")
    user_show.set_defaults(func=_user_show)

    # user create
    user_create = user_sub.add_parser("create", help="Create user")
    user_create.add_argument("userid", help="User ID (e.g. newuser@pve)")
    user_create.add_argument("--password", help="User password")
    user_create.add_argument("--enable", action="store_true", default=True,
                             help="Enable user (default)")
    user_create.add_argument("--disable", dest="enable", action="store_false",
                             help="Disable user account")
    user_create.add_argument("--firstname", help="First name")
    user_create.add_argument("--lastname", help="Last name")
    user_create.add_argument("--email", help="Email address")
    user_create.add_argument("--expire", type=int, default=0,
                             help="Account expiration (Unix timestamp, 0 = never)")
    user_create.add_argument("--group", action="append",
                             help="Group to add user to (repeatable)")
    user_create.set_defaults(func=_user_create)

    # user update
    user_update = user_sub.add_parser("update", help="Update user")
    user_update.add_argument("userid", help="User ID (e.g. xezpeleta@pve)")
    user_update.add_argument("--password", help="New password")
    user_update.add_argument("--enable", action="store_true", default=None,
                             help="Enable user")
    user_update.add_argument("--disable", dest="enable", action="store_false",
                             help="Disable user account")
    user_update.add_argument("--firstname", help="First name")
    user_update.add_argument("--lastname", help="Last name")
    user_update.add_argument("--email", help="Email address")
    user_update.add_argument("--expire", type=int, default=None,
                             help="Account expiration (Unix timestamp, 0 = never)")
    user_update.add_argument("--group", action="append",
                             help="Group to add user to (repeatable)")
    user_update.set_defaults(func=_user_update)

    # user delete
    user_delete = user_sub.add_parser("delete", help="Delete user")
    user_delete.add_argument("userid", help="User ID (e.g. newuser@pve)")
    user_delete.set_defaults(func=_user_delete)
