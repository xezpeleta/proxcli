# proxcli API Coverage

Last updated: 2026-06-22

The coverage visualization above shows at a glance which Proxmox VE API
areas are fully implemented, partially covered, or not yet started.

This document provides the full reference: every CLI subcommand mapped to
its underlying REST API endpoint and HTTP method.

---

## Endpoint reference

### Virtual machines (vm)

| Subcommand | Method | API path |
|---|---|---|
| `list` | GET | `/nodes/{node}/qemu` |
| `show <vmid>` | GET | `/nodes/{node}/qemu/{vmid}/status/current` |
| `create` | POST | `/nodes/{node}/qemu` |
| `start <vmid>` | POST | `/nodes/{node}/qemu/{vmid}/status/start` |
| `stop <vmid>` | POST | `/nodes/{node}/qemu/{vmid}/status/stop` |
| `reboot <vmid>` | POST | `/nodes/{node}/qemu/{vmid}/status/reboot` |
| `suspend <vmid>` | POST | `/nodes/{node}/qemu/{vmid}/status/suspend` |
| `resume <vmid>` | POST | `/nodes/{node}/qemu/{vmid}/status/resume` |
| `delete <vmid>` | DELETE | `/nodes/{node}/qemu/{vmid}` |
| `config <vmid>` | GET | `/nodes/{node}/qemu/{vmid}/config` |
| `snapshot list <vmid>` | GET | `/nodes/{node}/qemu/{vmid}/snapshot` |
| `snapshot create <vmid>` | POST | `/nodes/{node}/qemu/{vmid}/snapshot` |
| `snapshot show <vmid> <name>` | GET | `/nodes/{node}/qemu/{vmid}/snapshot/{snapname}` |
| `snapshot rollback <vmid> <name>` | POST | `/nodes/{node}/qemu/{vmid}/snapshot/{snapname}/rollback` |
| `snapshot delete <vmid> <name>` | DELETE | `/nodes/{node}/qemu/{vmid}/snapshot/{snapname}` |
| `clone <vmid>` | POST | `/nodes/{node}/qemu/{vmid}/clone` |
| `migrate <vmid>` | POST | `/nodes/{node}/qemu/{vmid}/migrate` |
| `template <vmid>` | POST | `/nodes/{node}/qemu/{vmid}/template` |
| `ip <vmid>` | GET | `/nodes/{node}/qemu/{vmid}/agent/network-get-interfaces` |
| `iso attach <vmid>` | PUT | `/nodes/{node}/qemu/{vmid}/config` (ide2) |
| `iso detach <vmid>` | PUT | `/nodes/{node}/qemu/{vmid}/config` (ide2=none) |
| `disk resize <vmid>` | PUT | `/nodes/{node}/qemu/{vmid}/resize` |
| `disk detach <vmid>` | PUT | `/nodes/{node}/qemu/{vmid}/config` (disk=none) |
| `disk remove <vmid>` | PUT | `/nodes/{node}/qemu/{vmid}/config` (delete=disk) |
| `agent interfaces <vmid>` | GET | `/nodes/{node}/qemu/{vmid}/agent/network-get-interfaces` |
| `agent osinfo <vmid>` | GET | `/nodes/{node}/qemu/{vmid}/agent/get-osinfo` |
| `agent fsinfo <vmid>` | GET | `/nodes/{node}/qemu/{vmid}/agent/get-fsinfo` |
| `agent users <vmid>` | GET | `/nodes/{node}/qemu/{vmid}/agent/get-users` |
| `agent exec <vmid>` | POST | `/nodes/{node}/qemu/{vmid}/agent/exec` + `exec-status` |
| `cloudinit generate <vmid>` | PUT | `/nodes/{node}/qemu/{vmid}/config` |

#### VM firewall

| Subcommand | Method | API path |
|---|---|---|
| `firewall options <vmid>` | GET | `/nodes/{node}/qemu/{vmid}/firewall/options` |
| `firewall enable <vmid>` | PUT | `/nodes/{node}/qemu/{vmid}/firewall/options` |
| `firewall disable <vmid>` | PUT | `/nodes/{node}/qemu/{vmid}/firewall/options` |
| `firewall policy <vmid>` | PUT | `/nodes/{node}/qemu/{vmid}/firewall/options` |
| `firewall rules list <vmid>` | GET | `/nodes/{node}/qemu/{vmid}/firewall/rules` |
| `firewall rules add <vmid>` | POST | `/nodes/{node}/qemu/{vmid}/firewall/rules` |
| `firewall rules show <vmid> <pos>` | GET | `/nodes/{node}/qemu/{vmid}/firewall/rules/{pos}` |
| `firewall rules update <vmid> <pos>` | PUT | `/nodes/{node}/qemu/{vmid}/firewall/rules/{pos}` |
| `firewall rules delete <vmid> <pos>` | DELETE | `/nodes/{node}/qemu/{vmid}/firewall/rules/{pos}` |
| `firewall refs <vmid>` | GET | `/nodes/{node}/qemu/{vmid}/firewall/refs` |

### Containers (container)

| Subcommand | Method | API path |
|---|---|---|
| `list` | GET | `/nodes/{node}/lxc` |
| `show <vmid>` | GET | `/nodes/{node}/lxc/{vmid}/status/current` |
| `create` | POST | `/nodes/{node}/lxc` |
| `start <vmid>` | POST | `/nodes/{node}/lxc/{vmid}/status/start` |
| `stop <vmid>` | POST | `/nodes/{node}/lxc/{vmid}/status/stop` |
| `delete <vmid>` | DELETE | `/nodes/{node}/lxc/{vmid}` |
| `ip <vmid>` | GET | `/nodes/{node}/lxc/{vmid}/interfaces` |
| `firewall … <vmid>` | CRUD | `/nodes/{node}/lxc/{vmid}/firewall/*` |

### Nodes (node)

| Subcommand | Method | API path |
|---|---|---|
| `list` | GET | `/nodes` |
| `show <node>` | GET | `/nodes/{node}/status` |
| `status <node>` | GET | `/nodes/{node}/status` |
| `subscription <node>` | GET | `/nodes/{node}/subscription` |
| `dns <node>` | GET | `/nodes/{node}/dns` |
| `time <node>` | GET | `/nodes/{node}/time` |
| `services <node>` | GET | `/nodes/{node}/services` |
| `pci <node>` | GET | `/nodes/{node}/hardware/pci` |
| `netstat <node>` | GET | `/nodes/{node}/netstat` |
| `config <node>` | GET | `/nodes/{node}/config` |
| `firewall …` | CRUD | `/nodes/{node}/firewall/*` |

### Storage (storage)

| Subcommand | Method | API path |
|---|---|---|
| `list` | GET | `/storage` |
| `show <storage>` | GET | `/storage/{storage}` |
| `content <storage>` | GET | `/nodes/{node}/storage/{storage}/content` |
| `upload` | POST | `/nodes/{node}/storage/{storage}/upload` |
| `status <storage>` | GET | `/nodes/{node}/storage/{storage}/status` |

### Network (network)

| Subcommand | Method | API path |
|---|---|---|
| `list` | GET | `/nodes/{node}/network` |
| `show <node> <iface>` | GET | `/nodes/{node}/network/{iface}` |

### Cluster (cluster)

| Subcommand | Method | API path |
|---|---|---|
| `status` | GET | `/cluster/status` |
| `log` | GET | `/cluster/log` |
| `options` | GET | `/cluster/options` |

#### Cluster firewall

| Subcommand | Method | API path |
|---|---|---|
| `firewall options` | GET | `/cluster/firewall/options` |
| `firewall enable` | PUT | `/cluster/firewall/options` |
| `firewall disable` | PUT | `/cluster/firewall/options` |
| `firewall policy` | PUT | `/cluster/firewall/options` |
| `firewall rules list` | GET | `/cluster/firewall/rules` |
| `firewall rules add` | POST | `/cluster/firewall/rules` |
| `firewall rules show <pos>` | GET | `/cluster/firewall/rules/{pos}` |
| `firewall rules update <pos>` | PUT | `/cluster/firewall/rules/{pos}` |
| `firewall rules delete <pos>` | DELETE | `/cluster/firewall/rules/{pos}` |
| `firewall aliases list` | GET | `/cluster/firewall/aliases` |
| `firewall aliases add <name>` | POST | `/cluster/firewall/aliases` |
| `firewall aliases delete <name>` | DELETE | `/cluster/firewall/aliases/{name}` |
| `firewall ipsets list` | GET | `/cluster/firewall/ipset` |
| `firewall ipsets add <name>` | POST | `/cluster/firewall/ipset` |
| `firewall ipsets show <name>` | GET | `/cluster/firewall/ipset/{name}` |
| `firewall ipsets delete <name>` | DELETE | `/cluster/firewall/ipset/{name}` |
| `firewall ipsets add-cidr <name>` | POST | `/cluster/firewall/ipset/{name}` |
| `firewall ipsets delete-cidr <name>` | DELETE | `/cluster/firewall/ipset/{name}/{cidr}` |
| `firewall refs` | GET | `/cluster/firewall/refs` |

### Ceph (ceph)

| Subcommand | Method | API path |
|---|---|---|
| `status` | GET | `/cluster/ceph/status` |
| `osd` | GET | `/nodes/{node}/ceph/osd` |
| `log` | GET | `/nodes/{node}/ceph/log` |
| `disks` | GET | `/nodes/{node}/disks/list` |

### Access control (user, role, acl, pool)

| Subcommand | Method | API path |
|---|---|---|
| `user list` | GET | `/access/users` |
| `user show <userid>` | GET | `/access/users/{userid}` |
| `user create <userid>` | POST | `/access/users` |
| `user update <userid>` | PUT | `/access/users/{userid}` |
| `user delete <userid>` | DELETE | `/access/users/{userid}` |
| `role list` | GET | `/access/roles` |
| `role show <roleid>` | GET | `/access/roles/{roleid}` |
| `role create <roleid>` | POST | `/access/roles` |
| `role update <roleid>` | PUT | `/access/roles/{roleid}` |
| `role delete <roleid>` | DELETE | `/access/roles/{roleid}` |
| `acl list` | GET | `/access/acl` |
| `acl add <path>` | POST | `/access/acl` |
| `acl delete <path>` | DELETE | `/access/acl` |
| `acl show <path>` | GET | `/access/acl` |
| `pool list` | GET | `/pools` |
| `pool show <poolid>` | GET | `/pools/{poolid}` |
| `pool create <poolid>` | POST | `/pools` |
| `pool update <poolid>` | PUT | `/pools/{poolid}` |
| `pool delete <poolid>` | DELETE | `/pools/{poolid}` |

### Backups (backup)

| Subcommand | Method | API path |
|---|---|---|
| `list` | GET | `/nodes/{node}/storage/{storage}/content` |
| `create` | POST | `/nodes/{node}/vzdump` |
| `restore` | POST | `/nodes/{node}/qemu` or `/nodes/{node}/lxc` |
| `delete <id>` | DELETE | `/nodes/{node}/storage/{storage}/content/{volid}` |
| `tasks` | GET | `/nodes/{node}/tasks` |
| `defaults` | GET | `/cluster/backup/default` |

### Tasks (task)

| Subcommand | Method | API path |
|---|---|---|
| `list` | GET | `/nodes/{node}/tasks` |
| `show <upid>` | GET | `/nodes/{node}/tasks/{upid}/status` |
| `wait <upid>` | GET | `/nodes/{node}/tasks/{upid}/status` (polling loop) |
| `log <upid>` | GET | `/nodes/{node}/tasks/{upid}/log` |

### Auth & shell

| Subcommand | Method | API path |
|---|---|---|
| `auth status` | — | Config file (local) |
| `auth setup` | — | Config file (local) |
| `auth check` | — | Config file (local) |
| `completion bash\|zsh\|fish` | — | Local generation |

---

## Not yet implemented

<details>
<summary><strong>Cluster-level</strong> (7 areas)</summary>

| Area | Endpoints | Effort |
|---|---|---|
| HA | `/cluster/ha/{status,resources,groups}` | Medium |
| SDN | `/cluster/sdn/{zones,vnets,subnets,controllers}` | Large |
| Replication | `/cluster/replication` | Medium |
| ACME certs | `/cluster/acme/{account,plugins,challenge-schema,tos}` | Medium |
| Metrics server | `/cluster/metrics/server` | Small |
| Notifications | `/cluster/notifications/{targets,matchers}` | Medium |
| Backup info | `/cluster/backup-info` | Small |

</details>

<details>
<summary><strong>Node-level</strong> (8 areas)</summary>

| Area | Endpoints | Effort |
|---|---|---|
| USB hardware | `/nodes/{node}/hardware/usb` | Small |
| System report | `/nodes/{node}/report` | Small |
| APT | `/nodes/{node}/apt/{update,changelog}` | Small |
| Journal | `/nodes/{node}/journal` | Small |
| RRD metrics | `/nodes/{node}/rrddata` (CPU, memory, disk, net) | Medium |
| Storage scan | `/nodes/{node}/scan/{lvm,lvmthin,zfs,nfs,…}` | Small |
| Startup order | `/nodes/{node}/startup` | Small |
| Wake-on-LAN | `/nodes/{node}/wakeonlan` | Small |

</details>

<details>
<summary><strong>Access & authentication</strong> (3 areas)</summary>

| Area | Endpoints | Effort |
|---|---|---|
| Auth domains | `/access/domains` (LDAP, AD, PAM realm management) | Medium |
| OpenID Connect | `/access/openid` (OIDC realm configuration) | Medium |
| TFA | `/access/tfa` (TOTP, WebAuthn, YubiKey) | Medium |

</details>
