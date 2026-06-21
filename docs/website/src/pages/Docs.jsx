import React, { useState, useEffect } from 'react'
import { Routes, Route, Link, useLocation } from 'react-router-dom'
import { Terminal, BookOpen, Shield, Cloud, Bot, Cog, Server, ChevronRight, ArrowLeft, ExternalLink, Code2, Key, FileCode, HardDrive, Network, Globe, Clock, Users, Database } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

const REPO_URL = 'https://github.com/xezpeleta/proxcli'

const navSections = [
  {
    title: 'Guides',
    items: [
      { path: '/docs/cloud-init', label: 'Cloud-Init VMs', file: 'cloud-init.md', icon: Cloud },
      { path: '/docs/permissions', label: 'API Permissions', file: 'api-permissions.md', icon: Shield },
      { path: '/docs/coding-agents', label: 'Coding Agents', file: 'coding-agents.md', icon: Bot },
      { path: '/docs/production', label: 'Production Automation', file: 'production-automation.md', icon: Cog },
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

// ── Markdown-based doc page (fetches .md from public/docs/) ──

function MarkdownDocPage({ title, file, icon: Icon }) {
  const [md, setMd] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch(`./docs/${file}`)
      .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.text() })
      .then(setMd)
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
          prose-headings:text-primary prose-headings:font-bold prose-headings:tracking-tight
          prose-h1:text-3xl prose-h1:mb-8
          prose-h2:text-2xl prose-h2:mt-10 prose-h2:mb-4 prose-h2:pb-2 prose-h2:border-b prose-h2:border-border
          prose-h3:text-xl prose-h3:mt-8 prose-h3:mb-3
          prose-p:text-secondary prose-p:leading-relaxed prose-p:mb-5
          prose-a:text-tertiary prose-a:no-underline hover:prose-a:underline
          prose-code:text-sm prose-code:font-mono prose-code:bg-code-bg prose-code:text-code-fg prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:before:content-none prose-code:after:content-none
          prose-pre:bg-code-bg prose-pre:border prose-pre:border-border prose-pre:rounded-lg
          prose-ul:text-secondary prose-li:my-1
          prose-ol:text-secondary prose-li:my-1
          prose-table:border prose-table:border-border
          prose-th:bg-surface-variant prose-th:text-primary prose-th:font-semibold prose-th:px-4 prose-th:py-2 prose-th:text-left
          prose-td:px-4 prose-td:py-2 prose-td:border-t prose-td:border-border prose-td:text-secondary
          prose-strong:text-primary
          prose-blockquote:border-l-tertiary prose-blockquote:text-secondary prose-blockquote:bg-surface prose-blockquote:rounded-r-lg prose-blockquote:py-3 prose-blockquote:px-5 prose-blockquote:border-l-4 prose-blockquote:not-italic
          prose-hr:border-border
        ">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{md}</ReactMarkdown>
        </div>
      )}
    </div>
  )
}

// ── Command Reference (hardcoded since it's interactive) ──

function CommandReferenceDocInner() {
  const resources = [
    { resource: 'vm', icon: Server, desc: 'QEMU virtual machines — create, list, start, stop, reboot, snapshots, cloud-init', examples: ['proxmox vm list', 'proxmox vm create --node pve01 --memory 2048 --cores 2', 'proxmox vm snapshot create 100 pre-upgrade'] },
    { resource: 'container', icon: Server, desc: 'LXC containers — create, list, start, stop, delete', examples: ['proxmox container list', 'proxmox container create --node pve01 --ostemplate local:vztmpl/debian-12'] },
    { resource: 'node', icon: Server, desc: 'Node info and status — DNS, time, services, PCI devices, network stats', examples: ['proxmox node list', 'proxmox node dns pve01', 'proxmox node services pve01'] },
    { resource: 'storage', icon: HardDrive, desc: 'Storage management — list, show, content, upload, usage stats', examples: ['proxmox storage list', 'proxmox storage upload --node pve01 --storage local --file image.qcow2'] },
    { resource: 'network', icon: Network, desc: 'Network interface inspection — bridges, bonds, VLANs, physical NICs', examples: ['proxmox network list --node pve01', 'proxmox network list --type vlan'] },
    { resource: 'cluster', icon: Globe, desc: 'Cluster status, log, options, Ceph health, OSDs, disk inventory', examples: ['proxmox cluster status', 'proxmox ceph status', 'proxmox ceph disks'] },
    { resource: 'task', icon: Clock, desc: 'Task listing, details, and real-time log streaming', examples: ['proxmox task list', 'proxmox task log UPID:pve01:... --follow'] },
    { resource: 'backup', icon: Shield, desc: 'vzdump backup management — list, create, delete, snapshot/suspend/stop modes', examples: ['proxmox backup list', 'proxmox backup create --node pve01 --vmid 100 --storage local'] },
    { resource: 'user / role / acl', icon: Users, desc: 'Access control — users, roles, ACLs, permissions', examples: ['proxmox user list', 'proxmox acl add / --roles PVEVMAdmin --users joe@pve'] },
    { resource: 'pool', icon: Database, desc: 'Resource pools for grouping VMs and containers', examples: ['proxmox pool list', 'proxmox pool create webservers --comment "Web tier"'] },
    { resource: 'auth', icon: Key, desc: 'Auth context, role setup, and permission checking', examples: ['proxmox auth status', 'proxmox auth setup', 'proxmox auth check'] },
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
            <button key={r.resource} onClick={() => setActive(i)} className={`w-full text-left px-4 py-3 rounded-md flex items-center gap-3 transition-colors ${i === active ? 'bg-tertiary/10 text-tertiary border border-tertiary/20' : 'hover:bg-surface-variant text-secondary border border-transparent'}`}>
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
            <div><h3 className="text-lg font-semibold text-primary font-mono">proxmox {resources[active].resource}</h3></div>
          </div>
          <p className="text-secondary mb-6 leading-relaxed">{resources[active].desc}</p>
          <div className="space-y-3">
            {resources[active].examples.map((ex, i) => (
              <div key={i} className="flex items-start gap-3">
                <ChevronRight className="w-4 h-4 text-tertiary flex-shrink-0 mt-1" />
                <code className="text-sm font-mono bg-code-bg text-code-fg px-3 py-1.5 rounded">{ex}</code>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

// ── Docs index ──

function DocsIndex() {
  return (
    <div className="max-w-3xl">
      <h1 className="text-3xl font-bold text-primary mb-4">Documentation</h1>
      <p className="text-secondary text-lg mb-8 leading-relaxed">
        Guides and reference material for getting the most out of proxcli — from your first
        cloud-init VM to running proxcli as a sandbox for coding agents.
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
                <MarkdownDocPage title="API Coverage" file="api-coverage.md" icon={Code2} />
              } />
              <Route path="command-reference" element={<CommandReferenceDocInner />} />
            </Routes>
          </div>
        </main>
      </div>
    </div>
  )
}
