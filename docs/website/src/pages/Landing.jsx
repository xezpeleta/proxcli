import React from 'react'
import { 
  Terminal, Shield, Bot, Zap, Server, 
  ChevronRight, Copy, Check, Star, 
  ArrowRight, Code2, Globe, Key, Lock, 
  Container, HardDrive, Network, Users, 
  Keyboard, Eye, Clock, Cloud, Workflow,
  FileCode, Database, Monitor
} from 'lucide-react'
import SplitFlapAgent from '../components/SplitFlapAgent'

const REPO_URL = 'https://github.com/xezpeleta/proxcli'
function GithubIcon({ className = 'w-5 h-5' }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/>
    </svg>
  )
}

function Hero() {
  return (
    <section className="bg-primary text-white py-24 md:py-32 relative overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-br from-primary via-primary to-primary/90" />
      <div className="absolute inset-0 opacity-[0.03] bg-[radial-gradient(circle_at_50%_50%,_#3B82F6_1px,_transparent_1px)] [background-size:24px_24px]" />
      
      <div className="max-w-7xl mx-auto px-6 relative z-10">
        <div className="max-w-3xl">
          <h1 className="text-4xl md:text-6xl font-bold leading-tight mb-6">
            proxcli,
            <br />
            <span className="text-tertiary">a tool for</span>
          </h1>
          <div className="mb-8 -mt-2 overflow-hidden" style={{ height: 'clamp(100px, 16vw, 170px)' }}>
            <SplitFlapAgent />
          </div>
          <p className="text-lg md:text-xl text-muted max-w-2xl mb-8 leading-relaxed">
            Automate every corner of your Proxmox cluster from the terminal.
            A sandbox your AI agent can trust, and production deployments
            you can rely on — all from a single binary with
            <code className="text-tertiary font-mono mx-1">--dry-run</code>
            confidence.
          </p>
          <div className="flex flex-wrap gap-4">
            <a 
              href="#quickstart" 
              className="inline-flex items-center gap-2 bg-tertiary hover:bg-blue-600 text-white px-6 py-3 rounded-md font-semibold transition-colors"
            >
              Get Started <ChevronRight className="w-4 h-4" />
            </a>
            <a 
              href={REPO_URL}
              className="inline-flex items-center gap-2 border border-border text-white hover:bg-white/5 px-6 py-3 rounded-md font-semibold transition-colors"
            >
              <GithubIcon className="w-5 h-5" /> View on GitHub
            </a>
          </div>
        </div>
      </div>
    </section>
  )
}

function CopyButton({ text }) {
  const [copied, setCopied] = React.useState(false)
  
  const copy = () => {
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }
  
  return (
    <button 
      onClick={copy}
      className="absolute top-3 right-3 p-2 rounded-md bg-code-bg hover:bg-secondary/50 text-muted hover:text-white transition-all"
    >
      {copied ? <Check className="w-4 h-4 text-success" /> : <Copy className="w-4 h-4" />}
    </button>
  )
}

function CodeBlock({ code, lang = 'bash' }) {
  return (
    <div className="relative group">
      <div className="absolute top-3 left-3 text-xs text-muted font-mono uppercase tracking-wider">
        {lang === 'bash-cmd' ? '$' : lang}
      </div>
      <pre className="bg-code-bg text-code-fg rounded-lg p-4 pt-10 overflow-x-auto text-sm leading-relaxed font-mono">
        <code>{code}</code>
      </pre>
      <CopyButton text={code} />
    </div>
  )
}

function SectionTitle({ icon: Icon, children }) {
  return (
    <div className="text-center mb-16">
      <div className="inline-flex items-center gap-3 text-tertiary mb-4">
        {Icon && <Icon className="w-8 h-8" />}
      </div>
      <h2 className="text-3xl md:text-4xl font-bold text-primary mb-4">
        {children}
      </h2>
    </div>
  )
}

function Card({ icon: Icon, title, children }) {
  return (
    <div className="bg-surface border border-border rounded-lg p-8 hover:border-tertiary/30 transition-colors">
      {Icon && (
        <div className="w-12 h-12 bg-tertiary/10 rounded-md flex items-center justify-center mb-4">
          <Icon className="w-6 h-6 text-tertiary" />
        </div>
      )}
      <h3 className="text-lg font-semibold text-primary mb-2">{title}</h3>
      <p className="text-secondary leading-relaxed">{children}</p>
    </div>
  )
}

function Features() {
  const features = [
    {
      icon: Terminal,
      title: 'Familiar CLI Pattern',
      description: 'proxmox vm list, proxmox vm start 100 — a discoverable <resource> <action> interface that feels like docker or kubectl.'
    },
    {
      icon: Shield,
      title: 'API Token & Password Auth',
      description: 'Authenticate via Proxmox API tokens or user/password. Credentials persist in XDG config with strict file permissions.'
    },
    {
      icon: Monitor,
      title: 'Beautiful Rich Tables',
      description: 'Human-readable colored tables for list commands, with sortable columns and automatic column sizing.'
    },
    {
      icon: Bot,
      title: 'AI Agent Native',
      description: 'Default JSON output, strict exit codes, and --dry-run mode make it ideal for LLM-powered infrastructure management.'
    },
    {
      icon: FileCode,
      title: 'Declarative VM Specs',
      description: 'Define VMs as YAML files. Export existing configs, edit, version-control, and recreate — infrastructure as code.'
    },
    {
      icon: Cloud,
      title: 'Cloud-Init Ready',
      description: 'Create VMs from cloud images with users, SSH keys, and networking configured in a single command.'
    },
    {
      icon: Container,
      title: 'VMs & Containers',
      description: 'Full lifecycle management for both QEMU VMs and LXC containers: create, start, stop, snapshots, delete.'
    },
    {
      icon: Lock,
      title: 'Full Firewall Management',
      description: 'Manage firewall rules, aliases, and ipsets at cluster, node, VM, and container levels with consistent flags.'
    },
    {
      icon: Database,
      title: 'Ceph Monitoring',
      description: 'Check Ceph cluster health, OSD status with disk wearout, and physical disk inventory from the CLI.'
    },
    {
      icon: Users,
      title: 'User & ACL Management',
      description: 'Create users, roles, and ACLs. Built-in auth setup and permission checking for least-privilege access.'
    },
    {
      icon: Clock,
      title: 'Task Monitoring',
      description: 'List tasks, show details, and stream logs in real-time with --follow, just like tail -f.'
    },
    {
      icon: Workflow,
      title: 'Shell Completions',
      description: 'Built-in bash, zsh, and fish completion scripts generated from the parser tree — always in sync.'
    }
  ]

  return (
    <section id="features" className="py-24 bg-surface-variant/50">
      <div className="max-w-7xl mx-auto px-6">
        <SectionTitle icon={Zap}>Why proxcli?</SectionTitle>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((f, i) => (
            <Card key={i} icon={f.icon} title={f.title}>{f.description}</Card>
          ))}
        </div>
      </div>
    </section>
  )
}

function QuickStart() {
  return (
    <section id="quickstart" className="py-24">
      <div className="max-w-7xl mx-auto px-6">
        <SectionTitle icon={Zap}>Quick Start</SectionTitle>
        <div className="max-w-3xl mx-auto space-y-6">
          <div>
            <h3 className="text-lg font-semibold text-primary mb-3 flex items-center gap-2">
              <span className="w-8 h-8 bg-tertiary/10 text-tertiary rounded-md flex items-center justify-center text-sm font-bold">1</span>
              Install
            </h3>
            <CodeBlock code="uv tool install proxcli" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-primary mb-3 flex items-center gap-2">
              <span className="w-8 h-8 bg-tertiary/10 text-tertiary rounded-md flex items-center justify-center text-sm font-bold">2</span>
              Configure credentials
            </h3>
            <CodeBlock code={`mkdir -p ~/.config/proxmox-cli && chmod 700 ~/.config/proxmox-cli

cat > ~/.config/proxmox-cli/credentials.json <<'EOF'
{
  "url": "https://192.168.1.10:8006",
  "username": "root@pam",
  "auth_method": "api_token",
  "api_token_id": "my-token",
  "api_token_secret": "deadbeef-...",
  "verify_tls": false
}
EOF

chmod 600 ~/.config/proxmox-cli/credentials.json`} />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-primary mb-3 flex items-center gap-2">
              <span className="w-8 h-8 bg-tertiary/10 text-tertiary rounded-md flex items-center justify-center text-sm font-bold">3</span>
              Start managing your cluster
            </h3>
            <CodeBlock code={`# List all VMs
proxmox vm list

# Show VM details
proxmox vm show 100

# Create a new VM
proxmox vm create --node pve01 --memory 2048 --cores 2 --name webserver

# Start it up
proxmox vm start 100

# Check cluster status
proxmox cluster status`} />
          </div>
          <div className="mt-6 p-6 bg-surface border border-border rounded-lg">
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 bg-success/10 rounded-md flex items-center justify-center flex-shrink-0 mt-0.5">
                <Zap className="w-4 h-4 text-success" />
              </div>
              <div>
                <h4 className="font-semibold text-primary mb-1">Install-to-first-command in under 60 seconds</h4>
                <p className="text-secondary text-sm">
                  uv tool install, one config file, and you&apos;re managing VMs from the terminal. 
                  No web UI needed.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

function GifDemo({ src, title, icon: Icon, alt }) {
  return (
    <div className="space-y-3">
      <h3 className="text-lg font-semibold text-primary flex items-center gap-2">
        {Icon && <Icon className="w-5 h-5 text-tertiary" />}
        {title}
      </h3>
      <div className="rounded-lg overflow-hidden border border-border bg-code-bg">
        <img 
          src={src} 
          alt={alt}
          className="w-full h-auto"
          loading="lazy"
        />
      </div>
    </div>
  )
}

function DemoSection() {
  return (
    <section className="py-24 bg-surface-variant/50">
      <div className="max-w-7xl mx-auto px-6">
        <SectionTitle icon={Eye}>Watch it in action</SectionTitle>
        
        <p className="text-center text-secondary max-w-2xl mx-auto mb-12 -mt-8">
          Real rich terminal output from <code className="font-mono text-xs bg-surface-variant px-1.5 py-0.5 rounded">proxcli</code>,
          rendered with the same{' '}
          <a href="https://github.com/Textualize/rich" className="text-tertiary hover:underline">rich</a>{' '}
          library the CLI uses. Status colors, unicode box-drawing, and column sizing are authentic.
        </p>

        <div className="max-w-3xl mx-auto space-y-8">
          <GifDemo src="demos/vm-list.gif" title="VM list — real rich output" icon={Server} alt="proxmox vm list animated demo" />
          <GifDemo src="demos/vm-show.gif" title="VM show — key-value table" icon={Monitor} alt="proxmox vm show animated demo" />
          <GifDemo src="demos/node-list.gif" title="Node list — status coloring" icon={Network} alt="proxmox node list animated demo" />
          <GifDemo src="demos/cluster.gif" title="Cluster status" icon={Globe} alt="proxmox cluster status demo" />
          <GifDemo src="demos/yaml-spec.gif" title="Declarative YAML VM spec" icon={FileCode} alt="proxmox vm create --file demo" />
        </div>
      </div>
    </section>
  )
}

function OutputFormats() {
  const formats = [
    {
      name: 'table',
      description: 'Rich colored tables with automatic sizing — ideal for interactive use',
      code: `┌──────┬───────────┬─────────┬──────┬──────┐
│ vmid │ name      │ status  │ cpu  │ mem  │
├──────┼───────────┼─────────┼──────┼──────┤
│ 100  │ webserver │ running │ 1.2% │ 2048 │
│ 101  │ database  │ running │ 0.8% │ 4096 │
└──────┴───────────┴─────────┴──────┴──────┘`
    },
    {
      name: 'json',
      description: 'Machine-readable JSON — default output format for scripts and agents',
      code: `[{
  "vmid": 100,
  "name": "webserver",
  "status": "running",
  "cpu": 0.012,
  "mem": 2048
}]`
    },
    {
      name: 'yaml',
      description: 'Human-friendly YAML with clean indentation — export configs, create templates',
      code: `- vmid: 100
  name: webserver
  status: running
  cpu: 0.012
  mem: 2048`
    }
  ]

  return (
    <section className="py-24">
      <div className="max-w-7xl mx-auto px-6">
        <SectionTitle icon={Code2}>Three output formats</SectionTitle>
        <div className="grid md:grid-cols-3 gap-6">
          {formats.map((fmt) => (
            <div key={fmt.name} className="bg-surface border border-border rounded-lg overflow-hidden">
              <div className="px-5 py-3 border-b border-border bg-surface-variant/50">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold text-primary uppercase tracking-wider">
                    {fmt.name}
                  </span>
                  {fmt.name === 'json' && (
                    <span className="text-[10px] px-2 py-0.5 bg-tertiary/10 text-tertiary rounded-full font-semibold">default</span>
                  )}
                </div>
              </div>
              <div className="p-5">
                <p className="text-secondary text-sm mb-4">{fmt.description}</p>
                <pre className="bg-code-bg text-code-fg rounded-md p-3 text-xs leading-relaxed font-mono overflow-x-auto">
                  {fmt.code}
                </pre>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

function Stats() {
  const stats = [
    { label: 'CLI Resources', value: '11', icon: Terminal },
    { label: 'Python Version', value: '3.10+', icon: Code2 },
    { label: 'Runtime Deps', value: '4', icon: Database },
    { label: 'Install Time', value: '≤60s', icon: Clock },
  ]

  return (
    <section className="py-16 bg-primary">
      <div className="max-w-7xl mx-auto px-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
          {stats.map((s) => (
            <div key={s.label} className="text-center">
              <div className="text-3xl font-bold text-tertiary mb-1">{s.value}</div>
              <div className="text-sm text-muted">{s.label}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

function Installation() {
  return (
    <section className="py-24 bg-surface-variant/50">
      <div className="max-w-7xl mx-auto px-6">
        <SectionTitle icon={Code2}>Installation</SectionTitle>
        <div className="max-w-3xl mx-auto space-y-6">
          <CodeBlock code={`# From PyPI (recommended)
uv tool install proxcli

# From Git
uv tool install git+https://github.com/xezpeleta/proxcli.git

# From local checkout
git clone https://github.com/xezpeleta/proxcli.git
cd proxcli
uv tool install .`} />
          <div className="mt-4 space-y-2">
            <div className="flex items-start gap-3 text-sm">
              <Check className="w-5 h-5 text-success flex-shrink-0 mt-0.5" />
              <span className="text-secondary"><code className="text-primary font-mono text-xs bg-surface-variant px-1.5 py-0.5 rounded">Python 3.10+</code> required</span>
            </div>
            <div className="flex items-start gap-3 text-sm">
              <Check className="w-5 h-5 text-success flex-shrink-0 mt-0.5" />
              <span className="text-secondary"><code className="text-primary font-mono text-xs bg-surface-variant px-1.5 py-0.5 rounded">uv</code> for dependency management and installation</span>
            </div>
            <div className="flex items-start gap-3 text-sm">
              <Check className="w-5 h-5 text-success flex-shrink-0 mt-0.5" />
              <span className="text-secondary">Only 4 runtime dependencies: <code className="text-primary font-mono text-xs bg-surface-variant px-1.5 py-0.5 rounded">httpx</code>, <code className="text-primary font-mono text-xs bg-surface-variant px-1.5 py-0.5 rounded">pydantic</code>, <code className="text-primary font-mono text-xs bg-surface-variant px-1.5 py-0.5 rounded">rich</code>, <code className="text-primary font-mono text-xs bg-surface-variant px-1.5 py-0.5 rounded">pyyaml</code></span>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

function CommandReference() {
  const resources = [
    {
      resource: 'vm',
      icon: Monitor,
      desc: 'QEMU virtual machines — create, list, start, stop, reboot, snapshots, cloud-init',
      examples: ['proxmox vm list', 'proxmox vm create --node pve01 --memory 2048 --cores 2', 'proxmox vm snapshot create 100 pre-upgrade']
    },
    {
      resource: 'container',
      icon: Container,
      desc: 'LXC containers — create, list, start, stop, delete',
      examples: ['proxmox container list', 'proxmox container create --node pve01 --ostemplate local:vztmpl/debian-12']
    },
    {
      resource: 'node',
      icon: Server,
      desc: 'Node info and status — DNS, time, services, PCI devices, network stats',
      examples: ['proxmox node list', 'proxmox node dns pve01', 'proxmox node services pve01']
    },
    {
      resource: 'storage',
      icon: HardDrive,
      desc: 'Storage management — list, show, content, upload, usage stats',
      examples: ['proxmox storage list', 'proxmox storage upload --node pve01 --storage local --file image.qcow2']
    },
    {
      resource: 'network',
      icon: Network,
      desc: 'Network interface inspection — bridges, bonds, VLANs, physical NICs',
      examples: ['proxmox network list --node pve01', 'proxmox network list --type vlan']
    },
    {
      resource: 'cluster',
      icon: Globe,
      desc: 'Cluster status, log, options, Ceph health, OSDs, disk inventory',
      examples: ['proxmox cluster status', 'proxmox ceph status', 'proxmox ceph disks']
    },
    {
      resource: 'task',
      icon: Clock,
      desc: 'Task listing, details, and real-time log streaming',
      examples: ['proxmox task list', 'proxmox task log UPID:pve01:... --follow']
    },
    {
      resource: 'backup',
      icon: Shield,
      desc: 'vzdump backup management — list, create, delete, snapshot/suspend/stop modes',
      examples: ['proxmox backup list', 'proxmox backup create --node pve01 --vmid 100 --storage local']
    },
    {
      resource: 'user / role / acl',
      icon: Users,
      desc: 'Access control — users, roles, ACLs, permissions',
      examples: ['proxmox user list', 'proxmox acl add / --roles PVEVMAdmin --users joe@pve']
    },
    {
      resource: 'pool',
      icon: Database,
      desc: 'Resource pools for grouping VMs and containers',
      examples: ['proxmox pool list', 'proxmox pool create webservers --comment "Web tier"']
    },
    {
      resource: 'auth',
      icon: Key,
      desc: 'Auth context, role setup, and permission checking',
      examples: ['proxmox auth status', 'proxmox auth setup', 'proxmox auth check']
    }
  ]

  const [active, setActive] = React.useState(0)

  return (
    <section className="py-24">
      <div className="max-w-7xl mx-auto px-6">
        <SectionTitle icon={Keyboard}>Command Reference</SectionTitle>
        <div className="grid lg:grid-cols-5 gap-8">
          <div className="lg:col-span-2 space-y-1">
            {resources.map((r, i) => (
              <button
                key={r.resource}
                onClick={() => setActive(i)}
                className={`w-full text-left px-4 py-3 rounded-md flex items-center gap-3 transition-colors ${
                  i === active 
                    ? 'bg-tertiary/10 text-tertiary border border-tertiary/20' 
                    : 'hover:bg-surface-variant text-secondary border border-transparent'
                }`}
              >
                <r.icon className={`w-4 h-4 flex-shrink-0 ${i === active ? 'text-tertiary' : 'text-muted'}`} />
                <span className="font-mono text-sm">proxmox {r.resource}</span>
              </button>
            ))}
          </div>
          <div className="lg:col-span-3 bg-surface border border-border rounded-lg p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-tertiary/10 rounded-md flex items-center justify-center">
                {React.createElement(resources[active].icon, { className: 'w-5 h-5 text-tertiary' })}
              </div>
              <div>
                <h3 className="text-lg font-semibold text-primary font-mono">
                  proxmox {resources[active].resource}
                </h3>
              </div>
            </div>
            <p className="text-secondary mb-6 leading-relaxed">{resources[active].desc}</p>
            <div className="space-y-3">
              {resources[active].examples.map((ex, i) => (
                <div key={i} className="flex items-start gap-3">
                  <ArrowRight className="w-4 h-4 text-tertiary flex-shrink-0 mt-1" />
                  <code className="text-sm font-mono bg-code-bg text-code-fg px-3 py-1.5 rounded">
                    {ex}
                  </code>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

function Footer() {
  return (
    <footer className="py-16 bg-primary text-muted">
      <div className="max-w-7xl mx-auto px-6">
        <div className="flex flex-col md:flex-row justify-between items-center gap-6">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <Terminal className="w-5 h-5 text-tertiary" />
              <span className="text-white font-bold text-lg">proxcli</span>
            </div>
            <p className="text-sm">Proxmox VE CLI — for humans &amp; agents</p>
          </div>
          <div className="flex items-center gap-4">
            <a href={REPO_URL} className="hover:text-white transition-colors">
              <GithubIcon className="w-5 h-5" />
            </a>
            <span className="text-sm">MIT License</span>
          </div>
        </div>
      </div>
    </footer>
  )
}

function NavBar() {
  return (
    <nav className="sticky top-0 z-50 bg-primary/95 backdrop-blur border-b border-border/10">
      <div className="max-w-7xl mx-auto px-6">
        <div className="flex items-center justify-between h-16">
          <a href="#" className="flex items-center gap-2 text-white font-bold">
            <Terminal className="w-5 h-5 text-tertiary" />
            proxcli
          </a>
          <div className="hidden md:flex items-center gap-6 text-sm">
            <a href="#features" className="text-muted hover:text-white transition-colors">Features</a>
            <a href="#quickstart" className="text-muted hover:text-white transition-colors">Quick Start</a>
            <a href="#/docs" className="text-muted hover:text-white transition-colors">Docs</a>
            <a href={REPO_URL} className="inline-flex items-center gap-1.5 text-white bg-tertiary hover:bg-blue-600 px-4 py-1.5 rounded-md transition-colors text-sm font-semibold">
              <GithubIcon className="w-4 h-4" /> GitHub
            </a>
          </div>
        </div>
      </div>
    </nav>
  )
}

function LandingPage() {
  return (
    <div className="min-h-screen bg-surface">
      <NavBar />
      <Hero />
      <Features />
      <Stats />
      <QuickStart />
      <OutputFormats />
      <DemoSection />
      <Installation />
      <CommandReference />
      <Footer />
    </div>
  )
}

export default LandingPage
