import React, { useState, useEffect } from 'react'
import {
  Server, Shield, Container, HardDrive, Globe, Database,
  Clock, Users, Cog, Check, Circle, AlertTriangle
} from 'lucide-react'

const ICON_MAP = {
  Server, Shield, Container, HardDrive, Globe, Database, Clock, Users, Cog
}

// ── Color scheme: green = done, amber = partial, gray = todo ──
const STATUS_COLORS = {
  done: { bg: '#22C55E', border: '#16A34A', text: '#14532D', chip: '#DCFCE7' },
  partial: { bg: '#F59E0B', border: '#D97706', text: '#78350F', chip: '#FEF3C7' },
  todo: { bg: '#E2E8F0', border: '#CBD5E1', text: '#64748B', chip: '#F8FAFC' },
}

function StatusDot({ status }) {
  return (
    <div
      style={{
        width: 10,
        height: 10,
        borderRadius: '50%',
        backgroundColor: STATUS_COLORS[status].bg,
        border: `1.5px solid ${STATUS_COLORS[status].border}`,
        flexShrink: 0,
      }}
    />
  )
}

export default function CoverageGrid() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showGaps, setShowGaps] = useState(false)
  const [expanded, setExpanded] = useState({})

  useEffect(() => {
    fetch(`${import.meta.env.BASE_URL}coverage.json`)
      .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json() })
      .then(setData)
      .catch(setError)
      .finally(() => setLoading(false))
  }, [])

  // auto-expand all categories with partial/todo on first load
  useEffect(() => {
    if (!data) return
    const exp = {}
    data.forEach((cat, i) => {
      if (cat.done < cat.total) exp[i] = true
    })
    setExpanded(exp)
  }, [data])

  if (loading) return <div className="py-12 text-center text-muted text-sm">Loading coverage data…</div>
  if (error) return <div className="py-12 text-center text-red-400 text-sm">Failed to load: {error.message}</div>
  if (!data) return null

  const totalEndpoints = data.reduce((s, c) => s + c.total, 0)
  const doneEndpoints = data.reduce((s, c) => s + c.done, 0)
  const pct = Math.round((doneEndpoints / totalEndpoints) * 100)

  const filtered = showGaps
    ? data.filter(c => c.done < c.total)
    : data

  const toggle = (idx) => setExpanded(prev => ({ ...prev, [idx]: !prev[idx] }))

  return (
    <div className="my-8">
      {/* ── Aggregate bar ── */}
      <div className="mb-6 p-5 bg-white border border-border rounded-lg">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-primary uppercase tracking-wide">API Coverage</h3>
          <span className="text-2xl font-bold text-primary">{pct}%</span>
        </div>
        {/* progress bar */}
        <div className="w-full h-3 bg-[#E2E8F0] rounded-full overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-700"
            style={{
              width: `${pct}%`,
              background: `linear-gradient(90deg, #22C55E, ${pct > 95 ? '#16A34A' : '#4ADE80'})`,
            }}
          />
        </div>
        <div className="flex items-center justify-between mt-2">
          <span className="text-xs text-muted">
            {doneEndpoints} of {totalEndpoints} endpoints implemented
          </span>
          <button
            onClick={() => setShowGaps(!showGaps)}
            className="text-xs text-tertiary hover:underline font-medium"
          >
            {showGaps ? 'Show all categories' : 'Show gaps only'}
          </button>
        </div>
      </div>

      {/* ── Category cards ── */}
      <div className="space-y-3">
        {filtered.map((cat, idx) => {
          const catPct = Math.round((cat.done / cat.total) * 100)
          const isComplete = cat.done === cat.total
          const isExpanded = expanded[idx] ?? false
          const IconComp = ICON_MAP[cat.icon] || Cog

          return (
            <div
              key={cat.category}
              className="border border-border rounded-lg overflow-hidden bg-white transition-shadow hover:shadow-sm"
            >
              {/* Header row */}
              <button
                onClick={() => toggle(idx)}
                className="w-full flex items-center gap-4 px-5 py-3 text-left hover:bg-surface/50 transition-colors"
              >
                <div
                  className="w-10 h-10 rounded-md flex items-center justify-center flex-shrink-0"
                  style={{ backgroundColor: isComplete ? '#DCFCE7' : '#FEF3C7' }}
                >
                  <IconComp
                    className="w-5 h-5"
                    style={{ color: isComplete ? '#16A34A' : '#D97706' }}
                  />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-primary text-sm">{cat.category}</span>
                    {isComplete ? (
                      <span className="text-[0.65rem] px-2 py-0.5 rounded-full font-semibold" style={{ background: '#DCFCE7', color: '#14532D' }}>
                        Complete
                      </span>
                    ) : (
                      <span className="text-[0.65rem] px-2 py-0.5 rounded-full font-semibold" style={{ background: '#FEF3C7', color: '#78350F' }}>
                        {catPct}%
                      </span>
                    )}
                  </div>
                  <span className="text-xs text-muted">{cat.done}/{cat.total} endpoints</span>
                </div>
                {/* mini bar */}
                <div className="hidden sm:block w-24 h-1.5 bg-[#E2E8F0] rounded-full flex-shrink-0">
                  <div
                    className="h-full rounded-full"
                    style={{
                      width: `${catPct}%`,
                      backgroundColor: isComplete ? '#22C55E' : '#F59E0B',
                    }}
                  />
                </div>
                <svg
                  className={`w-4 h-4 text-muted flex-shrink-0 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                  fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}
                >
                  <path d="M6 9l6 6 6-6" />
                </svg>
              </button>

              {/* Expanded groups */}
              {isExpanded && (
                <div className="border-t border-border px-5 py-3 bg-surface/30">
                  <div className="grid gap-3">
                    {cat.groups.map((group) => (
                      <div key={group.name}>
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-[0.65rem] font-semibold text-muted uppercase tracking-wider">
                            {group.name}
                          </span>
                          <span className="text-[0.6rem] text-muted">
                            {group.done}/{group.total}
                          </span>
                        </div>
                        <div className="flex flex-wrap gap-1.5">
                          {group.items.map((item) => (
                            <span
                              key={item.name}
                              className="inline-flex items-center gap-1.5 text-[0.68rem] px-2 py-1 rounded border font-medium"
                              style={{
                                backgroundColor: STATUS_COLORS[item.status].chip,
                                borderColor: STATUS_COLORS[item.status].border,
                                color: STATUS_COLORS[item.status].text,
                              }}
                            >
                              <StatusDot status={item.status} />
                              {item.name}
                            </span>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Legend */}
      <div className="flex items-center gap-5 mt-5 text-xs text-muted">
        <span className="inline-flex items-center gap-1.5">
          <StatusDot status="done" /> Implemented
        </span>
        <span className="inline-flex items-center gap-1.5">
          <StatusDot status="partial" /> Partial / WIP
        </span>
        <span className="inline-flex items-center gap-1.5">
          <StatusDot status="todo" /> Not started
        </span>
      </div>
    </div>
  )
}
