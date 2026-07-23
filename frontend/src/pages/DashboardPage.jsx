import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { listWorkflows } from '../api/client'
import {
  LayoutDashboard, Activity, FileText, ArrowRight,
  RefreshCw, Loader2, CheckCircle2, XCircle, Clock,
  PlusCircle, Building2, Mail,
} from 'lucide-react'

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

export default function DashboardPage() {
  const [workflows, setWorkflows] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const fetchWorkflows = async () => {
    setLoading(true)
    setError('')
    try {
      const data = await listWorkflows()
      setWorkflows(data.workflows || [])
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to fetch workflows')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchWorkflows()
  }, [])

  const stats = {
    total: workflows.length,
    completed: workflows.filter((w) => w.status === 'completed').length,
    running: workflows.filter((w) => w.status === 'running' || w.status === 'pending').length,
    failed: workflows.filter((w) => w.status === 'failed').length,
  }

  return (
    <div className="animate-fade-in max-w-6xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold gradient-text">Lead Intelligence Dashboard</h1>
          <p className="text-slate-500 text-sm mt-1">Overview of active workflows and generated reports</p>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={fetchWorkflows} className="btn-secondary text-sm gap-2">
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} /> Refresh
          </button>
          <Link to="/" className="btn-primary text-sm gap-2">
            <PlusCircle size={16} /> Submit New Lead
          </Link>
        </div>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="card flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-sky-500/15 flex items-center justify-center text-sky-400">
            <LayoutDashboard size={24} />
          </div>
          <div>
            <span className="text-xs text-slate-500 block">Total Leads</span>
            <span className="text-2xl font-bold text-slate-100">{stats.total}</span>
          </div>
        </div>

        <div className="card flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-emerald-500/15 flex items-center justify-center text-emerald-400">
            <CheckCircle2 size={24} />
          </div>
          <div>
            <span className="text-xs text-slate-500 block">Completed</span>
            <span className="text-2xl font-bold text-slate-100">{stats.completed}</span>
          </div>
        </div>

        <div className="card flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-amber-500/15 flex items-center justify-center text-amber-400">
            <Activity size={24} />
          </div>
          <div>
            <span className="text-xs text-slate-500 block">In Progress</span>
            <span className="text-2xl font-bold text-slate-100">{stats.running}</span>
          </div>
        </div>

        <div className="card flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-red-500/15 flex items-center justify-center text-red-400">
            <XCircle size={24} />
          </div>
          <div>
            <span className="text-xs text-slate-500 block">Failed</span>
            <span className="text-2xl font-bold text-slate-100">{stats.failed}</span>
          </div>
        </div>
      </div>

      {/* Workflows table */}
      <div className="card overflow-hidden">
        <h3 className="text-lg font-semibold text-slate-200 mb-4">Recent Workflows</h3>

        {error && (
          <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm mb-4">
            {error}
          </div>
        )}

        {loading && workflows.length === 0 ? (
          <div className="flex justify-center py-16">
            <Loader2 size={36} className="text-sky-500 animate-spin" />
          </div>
        ) : workflows.length === 0 ? (
          <div className="text-center py-12">
            <Building2 size={40} className="text-slate-700 mx-auto mb-3" />
            <p className="text-slate-400 font-medium mb-1">No lead submissions yet</p>
            <p className="text-slate-600 text-xs mb-4">Submit a lead form to initiate the multi-agent workflow</p>
            <Link to="/" className="btn-primary text-sm inline-flex">
              Submit First Lead
            </Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 text-xs font-semibold uppercase tracking-wider">
                  <th className="py-3 px-4">Company</th>
                  <th className="py-3 px-4">Lead Email</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Progress</th>
                  <th className="py-3 px-4">Submitted At</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-sm">
                {workflows.map((w) => (
                  <tr key={w.workflow_id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3.5 px-4 font-semibold text-slate-200">
                      {w.company || 'N/A'}
                    </td>
                    <td className="py-3.5 px-4 text-slate-400">
                      {w.email || 'N/A'}
                    </td>
                    <td className="py-3.5 px-4">
                      <StatusBadge status={w.status} />
                    </td>
                    <td className="py-3.5 px-4">
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-gradient-to-r from-sky-500 to-indigo-500 rounded-full"
                            style={{ width: `${w.progress_pct || 0}%` }}
                          />
                        </div>
                        <span className="text-xs text-slate-400 font-mono">{w.progress_pct || 0}%</span>
                      </div>
                    </td>
                    <td className="py-3.5 px-4 text-xs text-slate-500 font-mono">
                      {w.submitted_at ? new Date(w.submitted_at).toLocaleTimeString() : '—'}
                    </td>
                    <td className="py-3.5 px-4 text-right space-x-2">
                      <Link
                        to={`/status/${w.workflow_id}`}
                        className="inline-flex items-center gap-1 text-xs text-sky-400 hover:text-sky-300 transition-colors"
                      >
                        <Activity size={13} /> Status
                      </Link>
                      {w.status === 'completed' && (
                        <Link
                          to={`/report/${w.workflow_id}`}
                          className="inline-flex items-center gap-1 text-xs text-emerald-400 hover:text-emerald-300 transition-colors ml-3"
                        >
                          <FileText size={13} /> Report
                        </Link>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
