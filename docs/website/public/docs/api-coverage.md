# proxcli API Coverage

Last updated: 2026-06-20

This document tracks which Proxmox VE REST API endpoints are wrapped by proxcli.

## Implemented

| Resource | Actions | API endpoints |
|---|---|---|
| `vm` | list, show, create, start, stop, reboot, suspend, resume, delete, config | `/nodes/{node}/qemu[/{vmid}]` / `/nodes/{node}/qemu/{vmid}/status/{action}` |
| `vm config` | export clean YAML | `/nodes/{node}/qemu/{vmid}/config` |
| `vm snapshot` | list, create, show, rollback, delete | `/nodes/{node}/qemu/{vmid}/snapshot[/{snapname}]` |
| `vm cloudinit` | generate | `/nodes/{node}/qemu/{vmid}/config` (PUT) |
| `vm agent` | interfaces | `/nodes/{node}/qemu/{vmid}/agent/network-get-interfaces` |
| `vm firewall` | options, enable, disable, policy, rules (CRUD), refs | `/nodes/{node}/qemu/{vmid}/firewall/*` |
| `container` | list, show, create, start, stop, delete | `/nodes/{node}/lxc[/{vmid}]` / `/nodes/{node}/lxc/{vmid}/status/{action}` |
| `container firewall` | options, enable, disable, policy, rules (CRUD), refs | `/nodes/{node}/lxc/{vmid}/firewall/*` |
| `node` | list, show, status, subscription, dns, time, services, pci, netstat, config | `/nodes[/{node}]` / `/nodes/{node}/status` / `/nodes/{node}/subscription` / `/nodes/{node}/dns` / `/nodes/{node}/time` / `/nodes/{node}/services` / `/nodes/{node}/hardware/pci` / `/nodes/{node}/netstat` / `/nodes/{node}/config` |
| `node firewall` | options, enable, disable, policy, rules (CRUD), refs | `/nodes/{node}/firewall/*` |
| `storage` | list, show, content, status, upload | `/storage[/{storage}]` / `/nodes/{node}/storage/{storage}/content` / `/nodes/{node}/storage/{storage}/status` / `/nodes/{node}/storage/{storage}/upload` |
| `cluster` | status, log, options | `/cluster/status` / `/cluster/log` / `/cluster/options` |
| `cluster firewall` | options, enable, disable, policy, rules (CRUD), aliases, ipsets, refs | `/cluster/firewall/*` |
| `task` | list, show, log | `/nodes/{node}/tasks[/{upid}]` / `/nodes/{node}/tasks/{upid}/log` |
| `auth` | status | config file read-only |
| `pool` | list, show, create, update, delete | `/pools[/{poolid}]` |
| `user` | list, show, create, update, delete | `/access/users[/{userid}]` |
| `role` | list, show, create, update, delete | `/access/roles[/{roleid}]` |
| `acl` | list, show, add, delete | `/access/acl` |
| `backup` | list, show, create, delete, tasks, defaults | `/nodes/{node}/vzdump` / `/nodes/{node}/storage/{storage}/content` |
| `network` | list, show (read-only) | `/nodes/{node}/network[/{iface}]` |
| `ceph` | status, osd, log, disks | `/cluster/ceph/status` / `/nodes/{node}/ceph/log` / `/nodes/{node}/disks/list` |
| `completion` | bash, zsh, fish | local only |

## Not yet implemented

### Cluster-level

| Area | Endpoints | Read/Write | Effort | Notes |
|---|---|---|---|---|
| HA | `/cluster/ha/{status,resources,groups}` | R+W | Medium | HA status (4 nodes), 2 resource groups defined |
| SDN | `/cluster/sdn/{zones,vnets,subnets,controllers}` | R+W | Large | Not configured on reference cluster |
| Replication | `/cluster/replication` | R+W | Medium | 0 jobs currently |
| ACME certs | `/cluster/acme/{account,plugins,challenge-schema,tos}` | R+W | Medium | 1 account configured |
| Metrics server | `/cluster/metrics/server` | R+W | Small | 0 servers configured |
| Notifications | `/cluster/notifications/{targets,matchers}` | R+W | Medium | 2 targets, 1 matcher defined |
| Backup info | `/cluster/backup-info` | R | Small | Per-volume backup metadata |

### Node-level

| Area | Endpoints | Read/Write | Effort | Notes |
|---|---|---|---|---|
| USB hardware | `/nodes/{node}/hardware/usb` | R | Small | Needs elevated privileges |
| System report | `/nodes/{node}/report` | R | Small | Debug report generation |
| APT | `/nodes/{node}/apt/{update,changelog}` | R+W | Small | Package updates |
| Journal | `/nodes/{node}/journal` | R | Small | Systemd journal entries |
| RRD stats | `/nodes/{node}/rrd`, `/nodes/{node}/rrddata` | R | Medium | Time-series metrics |
| Storage scan | `/nodes/{node}/scan/{lvm,lvmthin,zfs,nfs,cifs,iscsi,glusterfs}` | R | Small | Discover available storage targets |
| Startup order | `/nodes/{node}/startup` | R+W | Small | VM/CT boot ordering |
| Wake-on-LAN | `/nodes/{node}/wakeonlan` | W | Small | Trigger WoL |

### Access/authentication

| Area | Endpoints | Read/Write | Effort | Notes |
|---|---|---|---|---|
| Auth domains | `/access/domains` | R+W | Medium | LDAP, AD, PAM realm management |
| OpenID Connect | `/access/openid` | R+W | Medium | OIDC realm configuration |
| TFA | `/access/tfa` | R+W | Medium | Two-factor authentication (TOTP, WebAuthn, etc.) |
