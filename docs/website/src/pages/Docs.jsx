import React, { useState, useEffect, useCallback } from 'react'
import { Routes, Route, Link, useLocation } from 'react-router-dom'
import { Terminal, BookOpen, Shield, Cloud, Bot, Cog, Server, ChevronRight, ArrowLeft, ExternalLink, Code2, Key, FileCode, HardDrive, Network, Globe, Clock, Users, Database, Copy, Check, Zap, Send } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeRaw from 'rehype-raw'
import { Light as SyntaxHighlighter } from 'react-syntax-highlighter'
import bash from 'react-syntax-highlighter/dist/esm/languages/hljs/bash'
import yaml from 'react-syntax-highlighter/dist/esm/languages/hljs/yaml'
import json from 'react-syntax-highlighter/dist/esm/languages/hljs/json'
import js from 'react-syntax-highlighter/dist/esm/languages/hljs/javascript'
import plaintext from 'react-syntax-highlighter/dist/esm/languages/hljs/plaintext'
import { atomOneDark } from 'react-syntax-highlighter/dist/esm/styles/hljs'
import CoverageGrid from '../components/CoverageGrid'

SyntaxHighlighter.registerLanguage('bash', bash)
SyntaxHighlighter.registerLanguage('sh', bash)
SyntaxHighlighter.registerLanguage('shell', bash)
SyntaxHighlighter.registerLanguage('yaml', yaml)
SyntaxHighlighter.registerLanguage('yml', yaml)
SyntaxHighlighter.registerLanguage('json', json)
SyntaxHighlighter.registerLanguage('js', js)
SyntaxHighlighter.registerLanguage('javascript', js)
SyntaxHighlighter.registerLanguage('plaintext', plaintext)
SyntaxHighlighter.registerLanguage('text', plaintext)
SyntaxHighlighter.registerLanguage('txt', plaintext)

const REPO_URL = 'https://github.com/xezpeleta/proxcli'

const navSections = [
  {
    title: 'Guides',
    items: [
      { path: '/docs/quickstart', label: 'Quick Start', file: 'quickstart.md', icon: Zap },
      { path: '/docs/permissions', label: 'API Permissions', file: 'api-permissions.md', icon: Shield },
      { path: '/docs/coding-agents', label: 'Coding Agents', file: 'coding-agents.md', icon: Bot },
      { path: '/docs/production', label: 'Production Automation', file: 'production-automation.md', icon: Cog },
      { path: '/docs/cloud-init', label: 'Cloud-Init VMs', file: 'cloud-init.md', icon: Cloud },
    ]
  },
  {
    title: 'Reference',
    items: [
      { path: '/docs/command-reference', label: 'Command Reference', commandRef: true, icon: Terminal },
      { path: '/docs/api-coverage', label: 'API Coverage', file: 'api-coverage.md', icon: Code2 },
    ]
  },
]

function Sidebar() {
  const location = useLocation()

  return (
    <aside className="w-64 flex-shrink-0 border-r border-border min-h-[calc(100vh-4rem)] bg-surface/80">
      <div className="sticky top-16 p-6">
        <Link to="/" className="flex items-center gap-2 text-muted hover:text-tertiary text-sm mb-8 transition-colors">
          <ArrowLeft className="w-4 h-4" /> Back to home
        </Link>
        
        {navSections.map((section) => (
          <div key={section.title} className="mb-6">
            <h3 className="text-xs font-semibold text-muted uppercase tracking-wider mb-3">
              {section.title}
            </h3>
            <nav className="space-y-1">
              {section.items.map((item) => {
                const isActive = location.pathname === item.path
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors ${
                      isActive
                        ? 'bg-tertiary/10 text-tertiary font-medium'
                        : 'text-secondary hover:text-primary hover:bg-surface-variant'
                    }`}
                  >
                    <item.icon className={`w-4 h-4 flex-shrink-0 ${isActive ? 'text-tertiary' : 'text-muted'}`} />
                    {item.label}
                  </Link>
                )
              })}
            </nav>
          </div>
        ))}

        <div className="mt-8 pt-6 border-t border-border">
          <a
            href={REPO_URL}
            className="flex items-center gap-2 text-sm text-muted hover:text-tertiary transition-colors"
          >
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/>
            </svg>
            proxcli on GitHub
          </a>
        </div>
      </div>
    </aside>
  )
}

// ── Code block with syntax highlighting + copy ──

function CodeBlock({ language, value }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = useCallback(() => {
    navigator.clipboard.writeText(value).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }, [value])

  const lang = language || 'text'

  return (
    <div className="group relative my-6 rounded-lg border border-border overflow-hidden shadow-sm">
      <div className="flex items-center justify-between px-4 py-1.5 bg-[#E2E8F0] border-b border-border">
        <span className="text-[0.65rem] font-mono text-muted uppercase tracking-widest font-semibold">{lang}</span>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1.5 text-xs text-muted hover:text-primary transition-colors"
        >
          {copied ? (
            <>
              <Check className="w-3.5 h-3.5 text-success" />
              <span className="text-success">Copied!</span>
            </>
          ) : (
            <>
              <Copy className="w-3.5 h-3.5" />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>
      <SyntaxHighlighter
        language={lang}
        style={atomOneDark}
        customStyle={{
          margin: 0,
          padding: '1rem 1.25rem',
          background: '#0F172A',
          borderRadius: 0,
          fontSize: '0.8125rem',
          lineHeight: 1.7,
        }}
        codeTagProps={{ style: { fontFamily: "'JetBrains Mono', 'Fira Code', monospace" } }}
      >
        {value}
      </SyntaxHighlighter>
    </div>
  )
}

// ── Shared markdown-to-React components ──
// Only overriding code/pre blocks for syntax highlighting.
// Everything else (headings, paragraphs, tables, blockquotes, lists)
// is handled by @tailwindcss/typography via the prose class.

function mdComponents(defaultLanguage) {
  return {
    code({ node, inline, className, children, ...props }) {
      const match = /language-(\w+)/.exec(className || '')
      const raw = String(children).replace(/\n$/, '')

      // Heuristic: inline code never has newlines, and remark-gfm sets className only on fenced blocks.
      // If there's a language- class OR the content has newlines, it's a block.
      const isBlock = !!match || raw.includes('\n')

      if (!isBlock) {
        return (
          <code
            className="bg-[#E2E8F0] text-[#1E293B] px-1.5 py-0.5 rounded font-normal text-[0.85em] before:content-none after:content-none"
            {...props}
          >
            {children}
          </code>
        )
      }

      const lang = match ? match[1] : (defaultLanguage || 'text')
      return <CodeBlock language={lang} value={raw} />
    },
    pre({ children }) {
      // Let our custom CodeBlock handle all pre rendering
      return <>{children}</>
    },
  }
}

// ── Markdown-based doc page ──

function MarkdownDocPage({ title, file, icon: Icon, defaultLanguage }) {
  const [md, setMd] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch(`${import.meta.env.BASE_URL}${file}`)
      .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.text() })
      .then(text => {
        // Strip the first h1 heading since the component provides its own title
        const stripped = text.replace(/^# .*\n\n?/, '')
        setMd(stripped)
      })
      .catch(setError)
      .finally(() => setLoading(false))
  }, [file])

  return (
    <div className="max-w-3xl">
      <div className="flex items-center gap-4 mb-8">
        {Icon && (
          <div className="w-12 h-12 bg-tertiary/10 rounded-lg flex items-center justify-center">
            <Icon className="w-6 h-6 text-tertiary" />
          </div>
        )}
        <h1 className="text-3xl font-bold text-primary">{title}</h1>
      </div>

      {loading && <p className="text-muted">Loading...</p>}
      {error && <p className="text-red-400">Failed to load documentation: {error.message}</p>}

      {!loading && !error && (
        <div className="prose prose-slate max-w-none
          prose-headings:text-primary prose-headings:tracking-tight
          prose-h2:text-[1.5rem] prose-h2:border-b prose-h2:border-border prose-h2:pb-2.5 prose-h2:mt-12 prose-h2:mb-5
          prose-h3:text-lg prose-h3:mt-8 prose-h3:mb-3
          prose-p:text-secondary prose-p:leading-relaxed
          prose-a:text-tertiary prose-a:no-underline prose-a:font-medium hover:prose-a:underline
          prose-code:before:content-none prose-code:after:content-none
          prose-pre:bg-transparent prose-pre:p-0 prose-pre:m-0 prose-pre:rounded-none
          prose-li:text-secondary prose-li:my-0.5
          prose-strong:text-primary
          prose-blockquote:border-l-tertiary prose-blockquote:bg-blue-50/50 prose-blockquote:text-secondary prose-blockquote:not-italic prose-blockquote:py-3 prose-blockquote:px-5 prose-blockquote:rounded-r-lg
          prose-hr:border-border
          prose-img:rounded-lg
          prose-th:text-left prose-th:text-primary prose-th:font-semibold prose-th:text-sm
          prose-td:text-secondary prose-td:text-sm
          prose-table:border prose-table:border-border
        ">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            rehypePlugins={[rehypeRaw]}
            components={mdComponents(defaultLanguage)}
          >
            {md}
          </ReactMarkdown>
          <div className="mt-12 pt-6 border-t border-border">
            <a
              href={REPO_URL}
              className="inline-flex items-center gap-1.5 text-sm text-muted hover:text-tertiary transition-colors"
            >
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/>
              </svg>
              proxcli on GitHub
            </a>
          </div>
        </div>
      )}
    </div>
  )
}

// ── Command Reference ──

function CommandReferenceDocInner() {
  const resources = [
    {
      resource: 'vm',
      icon: Server,
      desc: 'QEMU/KVM virtual machines — full lifecycle management.',
      subcommands: [
        { name: 'list', desc: 'List VMs across the cluster or on a specific node' },
        { name: 'show <vmid>', desc: 'Show full VM status and configuration' },
        { name: 'config <vmid>', desc: 'Export clean VM config (suitable for --file import)' },
        { name: 'create', desc: 'Create a new VM from flags or --file YAML spec' },
        { name: 'start <vmid>', desc: 'Start a stopped VM' },
        { name: 'stop <vmid>', desc: 'Stop a running VM (graceful ACPI shutdown)' },
        { name: 'reboot <vmid>', desc: 'Reboot a running VM' },
        { name: 'suspend <vmid>', desc: 'Suspend VM to disk (hibernate)' },
        { name: 'resume <vmid>', desc: 'Resume a suspended VM' },
        { name: 'delete <vmid>', desc: 'Permanently delete a VM and all its disks' },
        { name: 'snapshot', desc: 'Manage snapshots — list, create, show, rollback, delete', nested: [
          { name: 'list <vmid>', desc: 'List snapshots for a VM' },
          { name: 'create <vmid> <name>', desc: 'Create a named snapshot (optionally with --description)' },
          { name: 'show <vmid> <name>', desc: 'Show snapshot metadata' },
          { name: 'rollback <vmid> <name>', desc: 'Roll back to a snapshot (VM must be stopped)' },
          { name: 'delete <vmid> <name>', desc: 'Delete a snapshot' },
        ]},
        { name: 'agent', desc: 'Query QEMU guest agent', nested: [
          { name: 'interfaces <vmid>', desc: 'List network interfaces via guest agent' },
        ]},
        { name: 'cloudinit generate <vmid>', desc: 'Regenerate cloud-init ISO for a VM' },
        { name: 'firewall …', desc: 'Manage VM firewall', nested: [
          { name: 'options <vmid>', desc: 'Show firewall options (enable, default policy, log rate)' },
          { name: 'enable <vmid>', desc: 'Enable firewall for this VM' },
          { name: 'disable <vmid>', desc: 'Disable firewall for this VM' },
          { name: 'policy <vmid>', desc: 'Set default input/output policy (ACCEPT/DROP/REJECT)' },
          { name: 'rules … <vmid>', desc: 'Manage firewall rules — list, add, show <pos>, update <pos>, delete <pos>' },
          { name: 'refs <vmid>', desc: 'List firewall references (aliases and ipsets used by VM rules)' },
        ]},
      ],
      examples: [
        'proxmox vm list --node pve01',
        'proxmox vm show 100',
        'proxmox vm create --node pve01 --memory 2048 --cores 2 --name test-vm',
        'proxmox vm snapshot create 100 pre-upgrade',
        'proxmox vm agent exec 100 --command "uname -a"',
        'proxmox vm firewall rules list 100',
      ],
    },
    {
      resource: 'container',
      icon: Server,
      desc: 'LXC containers — lightweight OS-level virtualization.',
      subcommands: [
        { name: 'list', desc: 'List containers across the cluster' },
        { name: 'show <vmid>', desc: 'Show container status and configuration' },
        { name: 'create', desc: 'Create a new container from a template' },
        { name: 'start <vmid>', desc: 'Start a stopped container' },
        { name: 'stop <vmid>', desc: 'Stop a running container' },
        { name: 'delete <vmid>', desc: 'Delete a container and its rootfs' },
        { name: 'firewall … <vmid>', desc: 'Manage container firewall — rules list/add/show/update/delete' },
      ],
      examples: [
        'proxmox container list',
        'proxmox container create --node pve01 --ostemplate local:vztmpl/debian-12-standard \\\n  --storage local-lvm --memory 1024 --cores 1',
        'proxmox container start 101',
      ],
    },
    {
      resource: 'node',
      icon: Server,
      desc: 'Proxmox node management — status, DNS, time, services, PCI, networking.',
      subcommands: [
        { name: 'list', desc: 'List all nodes in the cluster with status' },
        { name: 'show <node>', desc: 'Show node status (CPU, memory, uptime, KSM)' },
        { name: 'status <node>', desc: 'Query current node status' },
        { name: 'dns <node>', desc: 'Show DNS configuration' },
        { name: 'time <node>', desc: 'Show system time and timezone' },
        { name: 'services <node>', desc: 'List systemd services (pveproxy, pvedaemon, etc.)' },
        { name: 'pci <node>', desc: 'List PCI devices' },
        { name: 'netstat <node>', desc: 'Show network device statistics' },
        { name: 'config <node>', desc: 'Show node configuration' },
        { name: 'subscription <node>', desc: 'Show subscription status' },
        { name: 'firewall …', desc: 'Manage node-level firewall — rules list/add/show/update/delete, options, enable, disable, policy' },
      ],
      examples: [
        'proxmox node list',
        'proxmox node show pve01',
        'proxmox node dns pve01',
        'proxmox node services pve01',
        'proxmox node firewall rules list pve01',
      ],
    },
    {
      resource: 'storage',
      icon: HardDrive,
      desc: 'Storage management — list, content, upload, status.',
      subcommands: [
        { name: 'list', desc: 'List all storages with type, content, and usage' },
        { name: 'show <storage>', desc: 'Show storage configuration' },
        { name: 'content <storage>', desc: 'List volumes/images/ISOs in a storage' },
        { name: 'upload', desc: 'Upload an image or ISO to storage' },
        { name: 'status <storage>', desc: 'Show storage usage and availability' },
      ],
      examples: [
        'proxmox storage list',
        'proxmox storage content local --node pve01',
        'proxmox storage upload --node pve01 --storage local \\\n  --content-type import --file debian-12.qcow2',
        'proxmox storage status local --node pve01',
      ],
    },
    {
      resource: 'network',
      icon: Network,
      desc: 'Network interface inspection — bridges, bonds, VLANs, physical NICs.',
      subcommands: [
        { name: 'list', desc: 'List network interfaces on nodes' },
        { name: 'show <node> <iface>', desc: 'Show detailed interface configuration' },
      ],
      examples: [
        'proxmox network list --node pve01',
        'proxmox network list --type bond',
        'proxmox network show pve01 vmbr0',
      ],
    },
    {
      resource: 'cluster',
      icon: Globe,
      desc: 'Cluster status, logs, options, and firewall management.',
      subcommands: [
        { name: 'status', desc: 'Show cluster quorum status and node membership' },
        { name: 'log', desc: 'Show cluster task log (--max N to limit entries)' },
        { name: 'options', desc: 'Show cluster-wide configuration options' },
        { name: 'firewall …', desc: 'Manage cluster-level firewall', nested: [
          { name: 'options', desc: 'Show firewall options (enable, policy, ebtables, log level)' },
          { name: 'enable', desc: 'Enable cluster firewall' },
          { name: 'disable', desc: 'Disable cluster firewall' },
          { name: 'policy', desc: 'Set default input/output policy (ACCEPT/DROP/REJECT)' },
          { name: 'rules …', desc: 'Manage firewall rules — list, add, show <pos>, update <pos>, delete <pos>' },
          { name: 'aliases …', desc: 'Manage aliases — list, add <name>, delete <name>' },
          { name: 'ipsets …', desc: 'Manage ipsets — list, add, show, delete, add-cidr, delete-cidr' },
          { name: 'refs', desc: 'List firewall references' },
        ]},
      ],
      examples: [
        'proxmox cluster status',
        'proxmox cluster log --max 50',
        'proxmox cluster firewall rules list',
        'proxmox cluster firewall aliases add www --cidr 10.0.0.0/8',
      ],
    },
    {
      resource: 'ceph',
      icon: Database,
      desc: 'Ceph cluster health, OSDs, logs, and disk inventory.',
      subcommands: [
        { name: 'status', desc: 'Show Ceph cluster health and PG status' },
        { name: 'log', desc: 'Show recent Ceph log entries' },
        { name: 'osd', desc: 'List Ceph OSDs (--node to filter, --json for raw data)' },
        { name: 'disks', desc: 'List physical disks available for Ceph OSDs' },
      ],
      examples: [
        'proxmox ceph status',
        'proxmox ceph osd --node pve01',
        'proxmox ceph disks',
      ],
    },
    {
      resource: 'task',
      icon: Clock,
      desc: 'Task listing, details, and real-time log streaming.',
      subcommands: [
        { name: 'list', desc: 'List recent tasks across the cluster' },
        { name: 'show <upid>', desc: 'Show task details and exit status' },
        { name: 'log <upid>', desc: 'Stream task log in real time (--follow for tail -f)' },
      ],
      examples: [
        'proxmox task list',
        'proxmox task list --node pve01 --limit 20',
        'proxmox task log UPID:pve01:000A1B2C:... --follow',
      ],
    },
    {
      resource: 'backup',
      icon: Shield,
      desc: 'vzdump backup management — create, list, delete, snapshot/suspend/stop modes.',
      subcommands: [
        { name: 'list', desc: 'List existing backups' },
        { name: 'create', desc: 'Create a new backup (snapshot, suspend, or stop mode)' },
        { name: 'delete <backup-id>', desc: 'Delete a backup' },
        { name: 'show <backup-id>', desc: 'Show backup details' },
        { name: 'tasks', desc: 'List backup tasks and their status' },
        { name: 'defaults', desc: 'Show default backup settings' },
      ],
      examples: [
        'proxmox backup list --node pve01',
        'proxmox backup create --node pve01 --vmid 100 --storage local --mode snapshot',
        'proxmox backup delete --node pve01 --id vzdump-qemu-100-2024_01_01',
      ],
    },
    {
      resource: 'user',
      icon: Users,
      desc: 'User management — CRUD operations for Proxmox VE users.',
      subcommands: [
        { name: 'list', desc: 'List all users' },
        { name: 'show <userid>', desc: 'Show user details' },
        { name: 'create <userid>', desc: 'Create a new user' },
        { name: 'update <userid>', desc: 'Update user properties (email, comment, etc.)' },
        { name: 'delete <userid>', desc: 'Delete a user' },
      ],
      examples: [
        'proxmox user list',
        'proxmox user show joe@pve',
        'proxmox user create agent@pve --comment "CI agent user"',
      ],
    },
    {
      resource: 'role',
      icon: Shield,
      desc: 'Role management — define custom privilege sets.',
      subcommands: [
        { name: 'list', desc: 'List all roles (built-in and custom)' },
        { name: 'show <roleid>', desc: 'Show role privileges' },
        { name: 'create <roleid>', desc: 'Create a custom role' },
        { name: 'update <roleid>', desc: 'Update role privileges' },
        { name: 'delete <roleid>', desc: 'Delete a custom role' },
      ],
      examples: [
        'proxmox role list',
        'proxmox role create proxcli-agent --privileges Sys.Audit,VM.Audit,VM.Allocate',
      ],
    },
    {
      resource: 'acl',
      icon: Key,
      desc: 'Access Control Lists — grant roles to users/tokens on paths.',
      subcommands: [
        { name: 'list', desc: 'List all ACLs' },
        { name: 'add <path>', desc: 'Add an ACL entry (grant role on path to user/token)' },
        { name: 'delete <path>', desc: 'Delete an ACL entry' },
        { name: 'show <path>', desc: 'Show ACL entries for a path' },
      ],
      examples: [
        'proxmox acl list',
        'proxmox acl add / --roles PVEVMAdmin --users joe@pve',
        'proxmox acl add /vms --roles proxcli-vm --tokenid agent-token --users agent@pve',
      ],
    },
    {
      resource: 'pool',
      icon: Database,
      desc: 'Resource pools — group VMs and containers for organizational purposes.',
      subcommands: [
        { name: 'list', desc: 'List all resource pools' },
        { name: 'show <poolid>', desc: 'Show pool members' },
        { name: 'create <poolid>', desc: 'Create a new resource pool' },
        { name: 'update <poolid>', desc: 'Update pool properties' },
        { name: 'delete <poolid>', desc: 'Delete an empty resource pool' },
      ],
      examples: [
        'proxmox pool list',
        'proxmox pool create webservers --comment "Web tier"',
      ],
    },
    {
      resource: 'auth',
      icon: Key,
      desc: 'Authentication — status, setup, and permission verification.',
      subcommands: [
        { name: 'status', desc: 'Show current authentication context and effective user' },
        { name: 'setup', desc: 'Bootstrap roles and ACLs for proxcli (requires Administrator)' },
        { name: 'check', desc: 'Validate the current token and list effective privileges' },
      ],
      examples: [
        'proxmox auth status',
        'proxmox auth setup',
        'proxmox auth check',
      ],
    },
    {
      resource: 'api',
      icon: Send,
      desc: 'Raw authenticated API calls — for endpoints not yet covered by dedicated subcommands.',
      subcommands: [
        { name: 'GET <path>', desc: 'Send a GET request (e.g. /nodes/pve01/status)' },
        { name: 'POST <path>', desc: 'Send a POST request with --data or --data-file' },
        { name: 'PUT <path>', desc: 'Send a PUT request to update a resource' },
        { name: 'DELETE <path>', desc: 'Send a DELETE request' },
      ],
      examples: [
        'proxmox api GET /nodes/pve01/status',
        'proxmox api PUT /nodes/pve01/qemu/100/config -d \'{"memory": 4096}\'',
        'echo \'{"memory": 4096}\' | proxmox api PUT /nodes/pve01/qemu/100/config',
      ],
    },
  ]

  const [active, setActive] = useState(0)

  return (
    <div className="max-w-4xl">
      <div className="flex items-center gap-4 mb-8">
        <div className="w-12 h-12 bg-tertiary/10 rounded-lg flex items-center justify-center">
          <Terminal className="w-6 h-6 text-tertiary" />
        </div>
        <h1 className="text-3xl font-bold text-primary">Command Reference</h1>
      </div>
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

        <div className="lg:col-span-3">
          {(() => {
            const r = resources[active]
            return (
              <div>
                {/* Header */}
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-10 bg-tertiary/10 rounded-md flex items-center justify-center flex-shrink-0">
                    {React.createElement(r.icon, { className: 'w-5 h-5 text-tertiary' })}
                  </div>
                  <div>
                    <h2 className="text-lg font-bold text-primary font-mono">
                      proxmox {r.resource}
                    </h2>
                  </div>
                </div>

                <p className="text-secondary leading-relaxed mb-6">{r.desc}</p>

                {/* Subcommands table */}
                <div className="mb-6">
                  <h3 className="text-xs font-semibold text-muted uppercase tracking-wider mb-3">
                    Subcommands
                  </h3>
                  <div className="border border-border rounded-lg overflow-hidden">
                    <table className="w-full text-sm">
                      <thead className="bg-surface-variant">
                        <tr>
                          <th className="px-4 py-2.5 text-left font-semibold text-primary w-[40%]">Command</th>
                          <th className="px-4 py-2.5 text-left font-semibold text-primary">Description</th>
                        </tr>
                      </thead>
                      <tbody>
                        {r.subcommands.flatMap((sc, idx) => {
                          const rows = [
                            <tr key={sc.name} className={idx % 2 === 0 ? 'bg-white' : 'bg-surface/50'}>
                              <td className={`px-4 py-2 font-mono text-xs border-t border-border whitespace-nowrap ${sc.nested ? 'text-primary font-semibold' : 'text-tertiary'}`}>
                                {sc.name}
                              </td>
                              <td className="px-4 py-2 text-secondary text-xs border-t border-border leading-relaxed">
                                {sc.desc}
                              </td>
                            </tr>
                          ]
                          if (sc.nested) {
                            sc.nested.forEach((n, ni) => {
                              rows.push(
                                <tr key={`${sc.name}-${n.name}`} className="bg-surface/50">
                                  <td className="px-4 py-2 pl-8 font-mono text-[0.7rem] text-tertiary/70 border-t border-border/50 whitespace-nowrap">
                                    └ {n.name}
                                  </td>
                                  <td className="px-4 py-2 text-secondary/70 text-[0.7rem] border-t border-border/50 leading-relaxed">
                                    {n.desc}
                                  </td>
                                </tr>
                              )
                            })
                          }
                          return rows
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Examples */}
                <div>
                  <h3 className="text-xs font-semibold text-muted uppercase tracking-wider mb-3">
                    Examples
                  </h3>
                  <div className="bg-[#0F172A] rounded-lg border border-border overflow-hidden">
                    <div className="flex items-center justify-between px-4 py-1.5 bg-[#1E293B] border-b border-border/30">
                      <span className="text-[0.6rem] font-mono text-muted uppercase tracking-widest font-semibold">shell</span>
                    </div>
                    <pre className="p-4 m-0 bg-transparent text-sm font-mono leading-relaxed overflow-x-auto">
                      <code className="text-[#E2E8F0]">
                        {r.examples.join('\n\n')}
                      </code>
                    </pre>
                  </div>
                </div>
              </div>
            )
          })()}
        </div>
      </div>
    </div>
  )
}

// ── API Coverage page ──

function ApiCoveragePage() {
  const [md, setMd] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch(`${import.meta.env.BASE_URL}api-coverage.md`)
      .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.text() })
      .then(text => {
        const stripped = text.replace(/^# .*\n\n?/, '')
        setMd(stripped)
      })
      .catch(setError)
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="max-w-3xl">
      <div className="flex items-center gap-4 mb-8">
        <div className="w-12 h-12 bg-tertiary/10 rounded-lg flex items-center justify-center">
          <Code2 className="w-6 h-6 text-tertiary" />
        </div>
        <h1 className="text-3xl font-bold text-primary">API Coverage</h1>
      </div>

      <CoverageGrid />

      {loading && <p className="text-muted">Loading reference…</p>}
      {error && <p className="text-red-400">Failed to load: {error.message}</p>}

      {!loading && !error && (
        <div className="prose prose-slate max-w-none mt-8
          prose-headings:text-primary prose-headings:tracking-tight
          prose-h2:text-[1.5rem] prose-h2:border-b prose-h2:border-border prose-h2:pb-2.5 prose-h2:mt-12 prose-h2:mb-5
          prose-h3:text-lg prose-h3:mt-8 prose-h3:mb-3
          prose-p:text-secondary prose-p:leading-relaxed
          prose-a:text-tertiary prose-a:no-underline prose-a:font-medium hover:prose-a:underline
          prose-code:before:content-none prose-code:after:content-none
          prose-pre:bg-transparent prose-pre:p-0 prose-pre:m-0 prose-pre:rounded-none
          prose-li:text-secondary prose-li:my-0.5
          prose-strong:text-primary
          prose-blockquote:border-l-tertiary prose-blockquote:bg-blue-50/50 prose-blockquote:text-secondary prose-blockquote:not-italic prose-blockquote:py-3 prose-blockquote:px-5 prose-blockquote:rounded-r-lg
          prose-hr:border-border
          prose-img:rounded-lg
          prose-th:text-left prose-th:text-primary prose-th:font-semibold prose-th:text-sm
          prose-td:text-secondary prose-td:text-sm
          prose-table:border prose-table:border-border
        ">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            rehypePlugins={[rehypeRaw]}
            components={mdComponents()}
          >
            {md}
          </ReactMarkdown>
        </div>
      )}
    </div>
  )
}

// ── Docs index ──

function DocsIndex() {
  return (
    <div className="max-w-3xl">
      <h1 className="text-3xl font-bold text-primary mb-4">Documentation</h1>
      <p className="text-secondary text-lg mb-8 leading-relaxed">
        Guides and reference material for getting the most out of{' '}
        <a href={REPO_URL} className="text-tertiary hover:underline font-medium">proxcli</a>
        {' '}— from your first cloud-init VM to running proxcli as a sandbox for
        coding agents.
      </p>

      <div className="grid gap-4">
        {navSections.map(section => (
          <div key={section.title}>
            <h2 className="text-sm font-semibold text-muted uppercase tracking-wider mb-3 mt-6">
              {section.title}
            </h2>
            <div className="grid sm:grid-cols-2 gap-3">
              {section.items.map(item => (
                <Link
                  key={item.path}
                  to={item.path}
                  className="flex items-start gap-3 p-4 rounded-lg border border-border hover:border-tertiary/30 hover:bg-surface transition-colors"
                >
                  <div className="w-10 h-10 bg-tertiary/10 rounded-md flex items-center justify-center flex-shrink-0">
                    <item.icon className="w-5 h-5 text-tertiary" />
                  </div>
                  <div>
                    <h3 className="font-medium text-primary">{item.label}</h3>
                  </div>
                  <ChevronRight className="w-4 h-4 text-muted flex-shrink-0 mt-1 ml-auto" />
                </Link>
              ))}
            </div>

            {/* api escape hatch card — not a nav item, inline highlight */}
            {section.title === 'Reference' && (
              <div className="mt-3 p-4 rounded-lg border border-tertiary/20 bg-tertiary/5 relative overflow-hidden">
                <div className="absolute top-0 right-0 w-24 h-24 bg-tertiary/5 rounded-bl-full" />
                <div className="flex items-start gap-3 relative">
                  <div className="w-10 h-10 bg-tertiary/10 rounded-md flex items-center justify-center flex-shrink-0">
                    <Send className="w-5 h-5 text-tertiary" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-medium text-primary">Raw API escape hatch</h3>
                    <p className="text-xs text-secondary mt-1 leading-relaxed">
                      For endpoints not yet wrapped in dedicated subcommands,{' '}
                      <code className="bg-white/80 text-primary px-1 py-0.5 rounded text-[0.75em] font-mono">proxmox api</code>{' '}
                      lets you make authenticated raw API calls — no manual token management with{' '}
                      <code className="bg-white/80 text-primary px-1 py-0.5 rounded text-[0.75em] font-mono">curl</code>.
                    </p>
                    <div className="mt-3 bg-[#0F172A] rounded-md overflow-hidden">
                      <pre className="p-3 m-0 text-[0.65rem] font-mono leading-relaxed text-[#E2E8F0] overflow-x-auto">
<code>{`# GET request
$ proxmox api GET /nodes/pve01/status

# PUT with JSON body
$ proxmox api PUT /nodes/pve01/qemu/100/config \\
  -d '{"memory": 4096, "cores": 4}'

# Piped from stdin
$ echo '{"memory": 4096}' | proxmox api PUT \\
  /nodes/pve01/qemu/100/config`}</code>
                      </pre>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

// ── Layout ──

export default function DocsLayout() {
  return (
    <div className="min-h-screen bg-surface">
      {/* Top nav */}
      <nav className="sticky top-0 z-50 bg-primary/95 backdrop-blur border-b border-border/10 h-16">
        <div className="max-w-full px-6 h-full">
          <div className="flex items-center justify-between h-full">
            <div className="flex items-center gap-4">
              <Link to="/" className="flex items-center gap-2 text-white font-bold">
                <Terminal className="w-5 h-5 text-tertiary" />
                proxcli
              </Link>
              <span className="text-muted text-sm font-semibold">Docs</span>
            </div>
            <a
              href={REPO_URL}
              className="inline-flex items-center gap-1.5 text-white bg-tertiary hover:bg-blue-600 px-4 py-1.5 rounded-md transition-colors text-sm font-semibold"
            >
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/>
              </svg>
              GitHub
            </a>
          </div>
        </div>
      </nav>

      <div className="flex">
        <Sidebar />
        
        <main className="flex-1 min-w-0">
          <div className="p-8 lg:p-12">
            <Routes>
              <Route index element={<DocsIndex />} />
              <Route path="quickstart" element={
                <MarkdownDocPage title="Quick Start" file="quickstart.md" icon={Zap} />
              } />
              <Route path="cloud-init" element={
                <MarkdownDocPage title="Cloud-Init VMs" file="cloud-init.md" icon={Cloud} />
              } />
              <Route path="permissions" element={
                <MarkdownDocPage title="API Permissions & Least Privilege" file="api-permissions.md" icon={Shield} />
              } />
              <Route path="coding-agents" element={
                <MarkdownDocPage title="proxcli as a Sandbox for Coding Agents" file="coding-agents.md" icon={Bot} />
              } />
              <Route path="production" element={
                <MarkdownDocPage title="Production Automation with proxcli" file="production-automation.md" icon={Cog} />
              } />
              <Route path="api-coverage" element={
                <ApiCoveragePage />
              } />
              <Route path="command-reference" element={<CommandReferenceDocInner />} />
            </Routes>
          </div>
        </main>
      </div>
    </div>
  )
}
