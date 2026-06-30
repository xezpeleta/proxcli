# Production Automation with proxcli

proxcli's structured output, declarative specs, and predictable behavior make
it a strong foundation for production Proxmox VE automation. This guide covers
patterns for scripting, CI/CD, and infrastructure-as-code (IaC) workflows.

## Design principles

proxcli follows three rules that make it reliable for automation:

1. **JSON by default** — Every command returns structured data. No screen-scraping needed.
2. **Strict exit codes** — `0` on success, non-zero on any error. `set -e` safe.
3. **Idempotent flags** — The same command repeated produces the same result. No hidden state.

## Shell scripting patterns

### Error handling

```bash
#!/usr/bin/env bash
set -euo pipefail

# proxcli respects exit codes — set -e catches failures
proxmox vm start 100  # exits non-zero if VM doesn't exist or is already running
```

### Safe VM creation

Check if a VM name already exists before creating:

```bash
vmid=$(proxmox --output json vm list | jq -r '.[] | select(.name=="webserver") | .vmid')

if [ -n "$vmid" ]; then
  echo "VM 'webserver' already exists as $vmid"
else
  proxmox vm create \
    --node pve01 --memory 4096 --cores 2 --name webserver
fi
```

### Parallel operations

Run operations across multiple VMs:

```bash
# Start all stopped VMs on a node
proxmox --output json vm list --node pve01 | \
  jq -r '.[] | select(.status=="stopped") | .vmid' | \
  xargs -I {} proxmox vm start {}
```

### Backup automation script

```bash
#!/usr/bin/env bash
# backup-all.sh — create backups for all running VMs across all nodes
set -euo pipefail

DATE=$(date +%Y%m%d-%H%M)
BACKUP_STORAGE="local"

# For each node, back up its running VMs
for node in $(proxmox --output json node list | jq -r '.[] | select(.status=="online") | .node'); do
  proxmox --output json vm list --node "$node" | \
    jq -r '.[] | select(.status=="running") | .vmid' | \
    while read -r vmid; do
      echo "Backing up VM $vmid on $node..."
      proxmox backup create \
        --node "$node" --vmid "$vmid" \
        --storage "$BACKUP_STORAGE" \
        --mode snapshot
    done
done

echo "Backups complete."
```

## Infrastructure as Code (IaC)

### Version-controlled VM specs

Export, edit, and version-control your VM configurations:

```bash
# Export an existing VM config
proxmox --output yaml vm config 100 > webserver.yaml

# Edit it
vim webserver.yaml

# Commit it
git add webserver.yaml && git commit -m "Update webserver config"

# Recreate or update from spec
proxmox vm create --file webserver.yaml
```

### Template VM pattern

Create a base template, clone it for workloads:

```bash
# 1. Create a cloud-init template
proxmox vm create \
  --node pve01 --vmid 9000 --name debian12-template \
  --memory 2048 --cores 2 \
  --import-from local:import/debian-12-genericcloud-amd64.qcow2 \
  --citype nocloud --ciuser debian \
  --sshkeys ~/.ssh/id_rsa.pub

# 2. (Optional) Start, configure packages, then stop

# 3. Convert to template
proxmox vm template 9000 --node pve01

# 4. Clone the template for new VMs
proxmox vm create \
  --node pve01 --name webserver01 \
  --import-from local:import/debian-12-genericcloud-amd64.qcow2 \
  --citype nocloud --ciuser debian \
  --cipassword 'ChangeMe123!' \
  --sshkeys ~/.ssh/id_rsa.pub \
  --net 'virtio,bridge=vmbr0'
```

### GitOps workflow

```yaml
# .github/workflows/deploy-vm.yml
name: Deploy VM from Spec

on:
  push:
    paths:
      - 'vm-specs/**.yaml'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install proxcli
        run: pipx install proxcli

      - name: Validate specs
        run: |
          for spec in vm-specs/*.yaml; do
            proxmox --dry-run vm create --file "$spec"
          done

      - name: Deploy VMs
        env:
          PROXMOX_URL: ${{ secrets.PROXMOX_URL }}
          PROXMOX_TOKEN_ID: ${{ secrets.PROXMOX_TOKEN_ID }}
          PROXMOX_TOKEN_SECRET: ${{ secrets.PROXMOX_TOKEN_SECRET }}
        run: |
          proxmox auth status
          for spec in vm-specs/*.yaml; do
            proxmox vm create --file "$spec"
          done
```

## Monitoring and health checks

### Cluster health check script

```bash
#!/usr/bin/env bash
# cluster-health.sh — exit 1 if anything is wrong
set -euo pipefail

HEALTHY=true

# Check all nodes are online
offline=$(proxmox --output json node list | jq -r '.[] | select(.status!="online") | .node')
if [ -n "$offline" ]; then
  echo "ERROR: Offline nodes: $offline"
  HEALTHY=false
fi

# Check all VMs are running
stopped=$(proxmox --output json vm list | jq -r '.[] | select(.status!="running") | .vmid')
if [ -n "$stopped" ]; then
  echo "WARNING: Stopped VMs: $stopped"
fi

# Check Ceph (if applicable)
ceph_health=$(proxmox --output json ceph status | jq -r '.health')
if [ "$ceph_health" != "HEALTH_OK" ]; then
  echo "ERROR: Ceph health: $ceph_health"
  HEALTHY=false
fi

if [ "$HEALTHY" = false ]; then
  exit 1
fi
echo "Cluster healthy."
```

### Cron-based snapshot rotation

```bash
# crontab entry: daily at 2 AM
# 0 2 * * * /usr/local/bin/snapshot-rotate.sh

#!/usr/bin/env bash
set -euo pipefail

MAX_SNAPS=7
PREFIX="daily"

for vmid in $(proxmox --output json vm list | jq -r '.[] | .vmid'); do
  # List existing snapshots for this VM
  snaps=$(proxmox --output json vm snapshot list "$vmid" | \
    jq -r --arg p "$PREFIX" '.[] | select(.name | startswith($p)) | .name')

  # Delete oldest if over limit
  count=$(echo "$snaps" | wc -l)
  if [ "$count" -ge "$MAX_SNAPS" ]; then
    oldest=$(echo "$snaps" | head -1)
    proxmox vm snapshot delete "$vmid" "$oldest"
  fi

  # Create new snapshot
  proxmox vm snapshot create "$vmid" "${PREFIX}-$(date +%Y%m%d)"
done
```

## Application deployment with cloud-init

### Nginx webserver spec

```yaml
# nginx-server.yaml
name: nginx-prod-01
node: pve01
memory: 4096
cores: 2
import_from: local:import/debian-12-genericcloud-amd64.qcow2
citype: nocloud
ciuser: debian
cipassword: "[REDACTED]"
sshkeys: ~/.ssh/id_rsa.pub
nameserver: 1.1.1.1
net0: "virtio,bridge=vmbr0"
cicustom: "user=local:snippets/nginx-userdata.yaml"
```

```yaml
# nginx-userdata.yaml
#cloud-config
packages:
  - nginx
  - certbot
  - python3-certbot-nginx

package_update: true
package_upgrade: true

write_files:
  - path: /var/www/html/index.html
    content: |
      <h1>proxcli-managed server</h1>

runcmd:
  - systemctl enable --now nginx
```

## Multi-environment workflow

Maintain separate spec directories per environment:

```
vm-specs/
├── production/
│   ├── webserver.yaml
│   └── database.yaml
├── staging/
│   ├── webserver.yaml
│   └── database.yaml
└── development/
    ├── dev-vm-01.yaml
    └── dev-vm-02.yaml
```

Deploy with environment-specific overrides:

```bash
# Production VMs get 8GB RAM
for spec in vm-specs/production/*.yaml; do
  proxmox vm create --file "$spec" --memory 8192
done

# Staging VMs get 4GB RAM
for spec in vm-specs/staging/*.yaml; do
  proxmox vm create --file "$spec" --memory 4096
done

# Dev VMs are minimal
for spec in vm-specs/development/*.yaml; do
  proxmox vm create --file "$spec" --memory 1024
done
```

## Integrating with existing tools

### Ansible dynamic inventory

```bash
#!/usr/bin/env bash
# proxmox-inventory.sh — Ansible dynamic inventory script
proxmox --output json vm list | jq '{
  _meta: { hostvars: {} },
  all: { children: ["ungrouped"] },
  ungrouped: { hosts: [.[] | .name] }
}'
```

### Terraform / OpenTofu data source

```hcl
data "external" "proxmox_vms" {
  program = ["bash", "-c", "proxmox --output json vm list"]
}
```

### Prometheus node metrics

```bash
#!/usr/bin/env bash
# proxmox-metrics.sh — export cluster metrics for node_exporter textfile collector
OUTPUT="/var/lib/node_exporter/textfile_collector/proxmox.prom"

vm_count=$(proxmox --output json vm list | jq 'length')
running=$(proxmox --output json vm list | jq '[.[] | select(.status=="running")] | length')

cat > "$OUTPUT" <<EOF
proxmox_vm_count $vm_count
proxmox_vm_running $running
EOF
```

## Best practices checklist

- [ ] Use `set -euo pipefail` in all scripts
- [ ] Always check VM/node existence before operations
- [ ] Use `--dry-run` in CI/CD validation stages
- [ ] Store VM specs in version control alongside application code
- [ ] Use separate API tokens per environment (production, staging)
- [ ] Apply least-privilege roles: production token != staging token
- [ ] Never hardcode credentials — use environment variables or secrets managers
- [ ] Run `proxmox auth check` in CI to validate permissions before deploying
- [ ] Include `--output json` in every automated command
- [ ] Log all proxcli output for audit trails
