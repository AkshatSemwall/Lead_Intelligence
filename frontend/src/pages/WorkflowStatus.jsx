import React, { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { getWorkflowStatus } from '../api/client'
import {
  CheckCircle2, XCircle, Loader2, Clock, ArrowRight,
  Shield, Search, BarChart3, Lightbulb, FileText,
  FileDown, Mail, BookOpen, Database, HardDrive,
} from 'lucide-react'

const NODE_SEQUENCE = [
  { key: 'orchestrator', label: 'Orchestrator', icon: Shield, desc: 'Initialising workflow' },
  { key: 'validation', label: 'Validation', icon: Shield, desc: 'Verifying lead data' },
  { key: 'company_research', label: 'Company Research', icon: Search, desc: 'Gathering company intelligence' },
  { key: 'business_analysis', label: 'Business Analysis', icon: BarChart3, desc: 'Analysing business model & strengths' },
  { key: 'insight_generation', label: 'Insight Generation', icon: Lightbulb, desc: 'Generating AI recommendations' },
  { key: 'report_generation', label: 'Report Generation', icon: FileText, desc: 'Composing audit report' },
  { key: 'pdf_generation', label: 'PDF Generation', icon: FileDown, desc: 'Converting to PDF' },
  { key: 'drive', label: 'Google Drive', icon: HardDrive, desc: 'Uploading to cloud storage' },
  { key: 'email', label: 'Email Delivery', icon: Mail, desc: 'Sending report to inbox' },
  { key: 'logging', label: 'Logging', icon: BookOpen, desc: 'Recording execution data' },
  { key: 'sheets', label: 'Google Sheets', icon: Database, desc: 'Updating records' },
]

function StatusBadge({ status }) {
  const configs = {
    pending: { cls: 'badge-pending', label: 'Pending' },
    running: { cls: 'badge-running', label: 'Running' },
    completed: { cls: 'badge-completed', label: 'Completed' },
    failed: { cls: 'badge-failed', label: 'Failed' },
  }
  const c = configs[status] || configs.pending
  return <span className={`badge ${c.cls}`}>{c.label}</span>
}

function NodeStep({ node, completed, active, failed }) {
  const Icon = node.icon
  const stepClass = failed ? 'failed' : active ? 'active' : completed ? 'completed' : 'pending'

  return (
    <div className={`node-step ${stepClass}`}>
      <div className={`w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 ${
        failed ? 'bg-red-500/20' : active ? 'bg-sky-500/20' : completed ? 'bg-emerald-500/20' : 'bg-slate-800/60'
      }`}>
        {active ? (
          <Loader2 size={18} className="text-sky-400 animate-spin" />
        ) : completed ? (
          <CheckCircle2 size={18} className="text-emerald-400" />
        ) : failed ? (
          <XCircle size={18} className="text-red-400" />
        ) : (
          <Icon size={18} className="text-slate-600" />
        )}
      </div>
      <div className="min-w-0 flex-1">
        <div className={`text-sm font-semibold ${
          failed ? 'text-red-400' : active ? 'text-sky-300' : completed ? 'text-emerald-300' : 'text-slate-500'
        }`}>{node.label}</div>
        <div className="text-xs text-slate-600 truncate">{node.desc}</div>
      </div>
      {active && (
        <div className="w-2 h-2 rounded-full bg-sky-400 animate-pulse flex-shrink-0" />
      )}
    </div>
  )
}

function ProgressRing({ pct }) {
  const r = 44
  const circ = 2 * Math.PI * r
  const offset = circ * (1 - pct / 100)
  return (
    <svg width="120" height="120" className="transform -rotate-90">
      <circle cx="60" cy="60" r={r} fill="none" stroke="#1e293b" strokeWidth="8" />
      <circle
        cx="60" cy="60" r={r} fill="none"
        stroke="url(#ring-gradient)" strokeWidth="8"
        strokeLinecap="round"
        strokeDasharray={circ}
        strokeDashoffset={offset}
        style={{ transition: 'stroke-dashoffset 0.6s ease' }}
      />
      <defs>
        <linearGradient id="ring-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#0ea5e9" />
          <stop offset="100%" stopColor="#6366f1" />
        </linearGradient>
      </defs>
    </svg>
  )
}

export default function WorkflowStatus() {
  const { workflowId: paramId } = useParams()
  const navigate = useNavigate()
  const [workflowId, setWorkflowId] = useState(paramId || '')
  const [inputId, setInputId] = useState(paramId || '')
  const [status, setStatus] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [polling, setPolling] = useState(false)

  const fetchStatus = useCallback(async (id) => {
    if (!id) return
    setLoading(true)
    setError('')
    try {
      const data = await getWorkflowStatus(id)
      setStatus(data)
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to fetch workflow status')
    } finally {
      setLoading(false)
    }
  }, [])

  // Auto-poll while running
  useEffect(() => {
    if (!workflowId) return
    fetchStatus(workflowId)
    const interval = setInterval(() => {
      if (status?.status === 'completed' || status?.status === 'failed') {
        clearInterval(interval)
        return
      }
      fetchStatus(workflowId)
    }, 3000)
    return () => clearInterval(interval)
  }, [workflowId, fetchStatus])

  useEffect(() => {
    if (status?.status === 'completed' || status?.status === 'failed') {
      // Stop polling
    }
  }, [status])

  const handleLookup = (e) => {
    e.preventDefault()
    setWorkflowId(inputId.trim())
    navigate(`/status/${inputId.trim()}`)
  }

  const nodesCompleted = status?.nodes_completed || []
  const currentNode = status?.current_node
  const isActive = status?.status === 'running' || status?.status === 'pending'

  return (
    <div className="animate-fade-in max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-2 gradient-text">Workflow Status</h1>
      <p className="text-slate-500 mb-8">Track your AI agent pipeline in real-time</p>

      {/* Lookup form */}
      {!paramId && (
        <form onSubmit={handleLookup} className="flex gap-3 mb-8">
          <input
            type="text" value={inputId}
            onChange={(e) => setInputId(e.target.value)}
            placeholder="Enter workflow ID…"
            className="input-field flex-1"
          />
          <button type="submit" className="btn-primary px-6" disabled={!inputId.trim()}>
            <ArrowRight size={16} /> Look Up
          </button>
        </form>
      )}

      {error && (
        <div className="card border-red-500/30 bg-red-500/5 mb-6">
          <p className="text-red-400 text-sm">{error}</p>
        </div>
      )}

      {loading && !status && (
        <div className="flex justify-center py-16">
          <Loader2 size={40} className="text-sky-500 animate-spin" />
        </div>
      )}

      {status && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Progress card */}
          <div className="lg:col-span-1">
            <div className="card sticky top-24">
              <div className="flex flex-col items-center mb-6">
                <div className="relative">
                  <ProgressRing pct={status.progress_pct || 0} />
                  <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <span className="text-2xl font-bold text-slate-100">{status.progress_pct || 0}%</span>
                    <span className="text-xs text-slate-500">complete</span>
                  </div>
                </div>
                <StatusBadge status={status.status} />
              </div>

              <div className="space-y-3 text-sm">
                <InfoRow label="Workflow ID" value={status.workflow_id?.slice(0, 8) + '…'} />
                {status.started_at && <InfoRow label="Started" value={formatTime(status.started_at)} />}
                {status.completed_at && <InfoRow label="Completed" value={formatTime(status.completed_at)} />}
                <InfoRow label="Current Step" value={status.current_node || '—'} />
              </div>

              {status.status === 'completed' && (
                <Link to={`/report/${status.workflow_id}`} className="btn-primary w-full mt-6 text-sm">
                  <FileText size={16} /> View Report
                </Link>
              )}

              {status.error && (
                <div className="mt-4 p-3 rounded-lg bg-red-500/10 border border-red-500/20">
                  <p className="text-xs text-red-400">{status.error}</p>
                </div>
              )}

              {isActive && (
                <div className="mt-4 flex items-center gap-2 text-xs text-sky-400">
                  <Loader2 size={12} className="animate-spin" />
                  Auto-refreshing every 3s
                </div>
              )}
            </div>
          </div>

          {/* Pipeline steps */}
          <div className="lg:col-span-2">
            <div className="card">
              <h3 className="text-base font-semibold text-slate-200 mb-5">Agent Pipeline</h3>
              <div className="space-y-2">
                {NODE_SEQUENCE.map((node, idx) => {
                  const completed = nodesCompleted.includes(node.key)
                  const active = currentNode === node.key && !completed
                  const failed = status.status === 'failed' && currentNode === node.key
                  return (
                    <React.Fragment key={node.key}>
                      <NodeStep node={node} completed={completed} active={active} failed={failed} />
                      {idx < NODE_SEQUENCE.length - 1 && (
                        <div className="ml-4 w-px h-3 bg-slate-800" />
                      )}
                    </React.Fragment>
                  )
                })}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function InfoRow({ label, value }) {
  return (
    <div className="flex justify-between items-center">
      <span className="text-slate-500">{label}</span>
      <span className="text-slate-300 font-mono text-xs">{value}</span>
    </div>
  )
}

function formatTime(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString()
}
