"""SSH-based helpers for bootstrapping Proxmox credentials.

Used by `proxmox auth setup --via ssh` to run an idempotent bash script on a
PVE node (as root@pam) that creates the recommended proxcli roles, an API
token, and the ACLs binding them together.
"""
