# proxcli API Coverage

Last updated: 2026-06-20

This document tracks every Proxmox VE REST API endpoint wrapped by proxcli,
along with endpoints not yet implemented.

---

## Summary

| Category       | Status                                            |
|----------------|---------------------------------------------------|
| VM lifecycle   | Full CRUD, snapshots, cloud-init, guest agent      |
| Containers     | Full CRUD, firewall                                |
| Nodes          | Full read — DNS, time, services, PCI, netstat       |
| Storage        | List, show, content, upload, status                 |
| Networking     | Read-only — bridges, bonds, VLANs, physical NICs   |
| Cluster        | Status, log, options, full firewall management     |
| Ceph           | Status, OSDs, logs, disk inventory                 |
| Access control | Users, roles, ACLs — full CRUD                     |
| Auth           | Status, setup, permission check                    |
| Backup         | List, create, delete, task tracking, defaults      |
| Tasks          | List, show, real-time log streaming (`--follow`)   |
| Shell          | Bash, Zsh, Fish completion                         |

## Implemented endpoints

### Virtual machines (`vm`)

| Subcommand | HTTP | API path |
|------------|------|----------|
| `list` | GET | `/nodes/{node}/qemu` |
| `show <vmid>` | GET | `/nodes/{node}/qemu/{vmid}/status/current` |
| `create` | POST | `/nodes/{node}/qemu` |
| `start <vmid>` | POST | `/nodes/{node}/qemu/{vmid}/status/start` |
| `stop <vmid>` | POST | `/nodes/{node}/qemu/{vmid}/status/stop` |
| `reboot <vmid>` | POST | `/nodes/{node}/qemu/{vmid}/status/reboot` |
| `suspend <vmid>` | POST | `/nodes/{node}/qemu/{vmid}/status/suspend` |
| `resume <vmid>` | POST | `/nodes/{node}/qemu/{vmid}/status/resume` |
| `delete <vmid>` | DEL | `/nodes/{node}/qemu/{vmid}` |
| `config <vmid>` | GET | `/nodes/{node}/qemu/{vmid}/config` |
| `snapshot list <vmid>` | GET | `/nodes/{node}/qemu/{vmid}/snapshot` |
| `snapshot create <vmid> <name>` | POST | `/nodes/{node}/qemu/{vmid}/snapshot` |
| `snapshot show <vmid> <name>` | GET | `/nodes/{node}/qemu/{vmid}/snapshot/{snapname}` |
| `snapshot rollback <vmid> <name>` | POST | `/nodes/{node}/qemu/{vmid}/snapshot/{snapname}/rollback` |
| `snapshot delete <vmid> <name>` | DEL | `/nodes/{node}/qemu/{vmid}/snapshot/{snapname}` |
| `cloudinit generate <vmid>` | PUT | `/nodes/{node}/qemu/{vmid}/config` |
| `agent interfaces <vmid>` | GET | `/nodes/{node}/qemu/{vmid}/agent/network-get-interfaces` |

#### `vm firewall`

| Subcommand | HTTP | API path |
|------------|------|----------|
| `options <vmid>` | GET | `/nodes/{node}/qemu/{vmid}/firewall/options` |
| `enable <vmid>` | PUT | `/nodes/{node}/qemu/{vmid}/firewall/options` |
| `disable <vmid>` | PUT | `/nodes/{node}/qemu/{vmid}/firewall/options` |
| `policy <vmid>` | PUT | `/nodes/{node}/qemu/{vmid}/firewall/options` |
| `rules list <vmid>` | GET | `/nodes/{node}/qemu/{vmid}/firewall/rules` |
| `rules add <vmid>` | POST | `/nodes/{node}/qemu/{vmid}/firewall/rules` |
| `rules show <vmid> <pos>` | GET | `/nodes/{node}/qemu/{vmid}/firewall/rules/{pos}` |
| `rules update <vmid> <pos>` | PUT | `/nodes/{node}/qemu/{vmid}/firewall/rules/{pos}` |
| `rules delete <vmid> <pos>` | DEL | `/nodes/{node}/qemu/{vmid}/firewall/rules/{pos}` |
| `refs <vmid>` | GET | `/nodes/{node}/qemu/{vmid}/firewall/refs` |

### Containers (`container`)

| Subcommand | HTTP | API path |
|------------|------|----------|
| `list` | GET | `/nodes/{node}/lxc` |
| `show <vmid>` | GET | `/nodes/{node}/lxc/{vmid}/status/current` |
| `create` | POST | `/nodes/{node}/lxc` |
| `start <vmid>` | POST | `/nodes/{node}/lxc/{vmid}/status/start` |
| `stop <vmid>` | POST | `/nodes/{node}/lxc/{vmid}/status/stop` |
| `delete <vmid>` | DEL | `/nodes/{node}/lxc/{vmid}` |
| `firewall …` | — | `/nodes/{node}/lxc/{vmid}/firewall/*` |

### Nodes (`node`)

| Subcommand | HTTP | API path |
|------------|------|----------|
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
| `firewall …` | — | `/nodes/{node}/firewall/*` |

### Storage (`storage`)

| Subcommand | HTTP | API path |
|------------|------|----------|
| `list` | GET | `/storage` |
| `show <storage>` | GET | `/storage/{storage}` |
| `content <storage>` | GET | `/nodes/{node}/storage/{storage}/content` |
| `upload` | POST | `/nodes/{node}/storage/{storage}/upload` |
| `status <storage>` | GET | `/nodes/{node}/storage/{storage}/status` |

### Networking (`network`)

| Subcommand | HTTP | API path |
|------------|------|----------|
| `list` | GET | `/nodes/{node}/network` |
| `show <node> <iface>` | GET | `/nodes/{node}/network/{iface}` |

### Cluster (`cluster`)

| Subcommand | HTTP | API path |
|------------|------|----------|
| `status` | GET | `/cluster/status` |
| `log` | GET | `/cluster/log` |
| `options` | GET | `/cluster/options` |
| `firewall …` | — | `/cluster/firewall/*` |

#### `cluster firewall`

| Subcommand | HTTP | API path |
|------------|------|----------|
| `options` | GET | `/cluster/firewall/options` |
| `enable` | PUT | `/cluster/firewall/options` |
| `disable` | PUT | `/cluster/firewall/options` |
| `policy` | PUT | `/cluster/firewall/options` |
| `rules …` | CRUD | `/cluster/firewall/rules[/{pos}]` |
| `aliases list` | GET | `/cluster/firewall/aliases` |
| `aliases add <name>` | POST | `/cluster/firewall/aliases` |
| `aliases delete <name>` | DEL | `/cluster/firewall/aliases/{name}` |
| `ipsets list` | GET | `/cluster/firewall/ipset` |
| `ipsets add <name>` | POST | `/cluster/firewall/ipset` |
| `ipsets show <name>` | GET | `/cluster/firewall/ipset/{name}` |
| `ipsets delete <name>` | DEL | `/cluster/firewall/ipset/{name}` |
| `ipsets add-cidr <name>` | POST | `/cluster/firewall/ipset/{name}` |
| `ipsets delete-cidr <name>` | DEL | `/cluster/firewall/ipset/{name}/{cidr}` |
| `refs` | GET | `/cluster/firewall/refs` |

### Ceph (`ceph`)

| Subcommand | HTTP | API path |
|------------|------|----------|
| `status` | GET | `/cluster/ceph/status` |
| `osd` | GET | `/nodes/{node}/ceph/osd` |
| `log` | GET | `/nodes/{node}/ceph/log` |
| `disks` | GET | `/nodes/{node}/disks/list` |

### Access control (`user`, `role`, `acl`)

| Subcommand | HTTP | API path |
|------------|------|----------|
| `user list` | GET | `/access/users` |
| `user show <userid>` | GET | `/access/users/{userid}` |
| `user create <userid>` | POST | `/access/users` |
| `user update <userid>` | PUT | `/access/users/{userid}` |
| `user delete <userid>` | DEL | `/access/users/{userid}` |
| `role list` | GET | `/access/roles` |
| `role show <roleid>` | GET | `/access/roles/{roleid}` |
| `role create <roleid>` | POST | `/access/roles` |
| `role update <roleid>` | PUT | `/access/roles/{roleid}` |
| `role delete <roleid>` | DEL | `/access/roles/{roleid}` |
| `acl list` | GET | `/access/acl` |
| `acl add <path>` | POST | `/access/acl` |
| `acl delete <path>` | DEL | `/access/acl` |
| `acl show <path>` | GET | `/access/acl` |

### Backups (`backup`)

| Subcommand | HTTP | API path |
|------------|------|----------|
| `list` | GET | `/nodes/{node}/storage/{storage}/content` |
| `create` | POST | `/nodes/{node}/vzdump` |
| `delete <id>` | DEL | `/nodes/{node}/storage/{storage}/content/{volid}` |
| `tasks` | GET | `/nodes/{node}/tasks` |
| `defaults` | GET | `/cluster/backup/default` |

### Tasks (`task`)

| Subcommand | HTTP | API path |
|------------|------|----------|
| `list` | GET | `/nodes/{node}/tasks` |
| `show <upid>` | GET | `/nodes/{node}/tasks/{upid}/status` |
| `log <upid>` | GET | `/nodes/{node}/tasks/{upid}/log` |

### Auth & completion

| Subcommand | HTTP | API path |
|------------|------|----------|
| `auth status` | — | Config file only (local) |
| `auth setup` | — | Config file only (local) |
| `auth check` | — | Config file only (local) |
| `completion bash` | — | Local generation |
| `completion zsh` | — | Local generation |
| `completion fish` | — | Local generation |

---

## Not yet implemented

### Cluster-level

| Area | Endpoints | R/W | Effort | Notes |
|------|-----------|-----|--------|-------|
| HA | `/cluster/ha/{status,resources,groups}` | R+W | Medium | HA status across nodes, resource group management |
| SDN | `/cluster/sdn/{zones,vnets,subnets,controllers}` | R+W | Large | Software-defined networking layers |
| Replication | `/cluster/replication` | R+W | Medium | Cross-cluster VM replication jobs |
| ACME certs | `/cluster/acme/{account,plugins,challenge-schema,tos}` | R+W | Medium | Let's Encrypt certificate management |
| Metrics server | `/cluster/metrics/server` | R+W | Small | InfluxDB/Graphite export targets |
| Notifications | `/cluster/notifications/{targets,matchers}` | R+W | Medium | Alert routing and notification targets |
| Backup info | `/cluster/backup-info` | R | Small | Per-volume backup metadata |

### Node-level

| Area | Endpoints | R/W | Effort | Notes |
|------|-----------|-----|--------|-------|
| USB hardware | `/nodes/{node}/hardware/usb` | R | Small | Lists connected USB devices |
| System report | `/nodes/{node}/report` | R | Small | Generates debug bundles |
| APT | `/nodes/{node}/apt/{update,changelog}` | R+W | Small | Package update management |
| Journal | `/nodes/{node}/journal` | R | Small | Systemd journal entries |
| RRD stats | `/nodes/{node}/rrd`<br>`/nodes/{node}/rrddata` | R | Medium | Time-series metrics (CPU, memory, disk, net) |
| Storage scan | `/nodes/{node}/scan/{lvm,lvmthin,zfs,nfs,cifs,iscsi,glusterfs}` | R | Small | Discover available storage targets |
| Startup order | `/nodes/{node}/startup` | R+W | Small | VM/CT boot ordering |
| Wake-on-LAN | `/nodes/{node}/wakeonlan` | W | Small | Trigger WoL for VMs/CTs |

### Access & authentication

| Area | Endpoints | R/W | Effort | Notes |
|------|-----------|-----|--------|-------|
| Auth domains | `/access/domains` | R+W | Medium | LDAP, AD, PAM realm management |
| OpenID Connect | `/access/openid` | R+W | Medium | OIDC realm configuration |
| TFA | `/access/tfa` | R+W | Medium | Two-factor auth (TOTP, WebAuthn, YubiKey) |
