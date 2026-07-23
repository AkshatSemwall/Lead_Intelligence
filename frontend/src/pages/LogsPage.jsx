import React, { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getWorkflowLogs } from '../api/client'
import {
  FileText, ArrowLeft, Loader2, AlertCircle, CheckCircle2,
  XCircle, Clock, Terminal, ChevronRight, RefreshCw,
} from 'lucide-react'

function StatusIcon({ status }) {
  if (status === 'completed') return <CheckCircle2 size={16} className="text-emerald-400" />
  if (status === 'failed') return <XCircle size={16} className="text-red-400" />
  if (status === 'started') return <Loader2 size={16} className="text-sky-400 animate-spin" />
  return <Clock size={16} className="text-slate-500" />
}

export default function LogsPage() {
  const { workflowId: paramId } = useParams()
  const [workflowId, setWorkflowId] = useState(paramId || '')
  const [inputId, setInputId] = useState(paramId || '')
  const [logs, setLogs] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const fetchLogs = async (id) => {
    if (!id) return
    setLoading(true)
    setError('')
    try {
      const data = await getWorkflowLogs(id)
      setLogs(data)
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to fetch logs for this workflow ID')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (paramId) {
      setWorkflowId(paramId)
      setInputId(paramId)
      fetchLogs(paramId)
    }
  }, [paramId])

  const handleLookup = (e) => {
    e.preventDefault()
    if (!inputId.trim()) return
    setWorkflowId(inputId.trim())
    fetchLogs(inputId.trim())
  }

  return (
    <div className="animate-fade-in max-w-5xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-bold gradient-text">Execution Logs</h1>
          <p className="text-slate-500 text-sm mt-1">Audit trail and step-by-step logs per agent node</p>
        </div>
        {workflowId && (
          <button onClick={() => fetchLogs(workflowId)} className="btn-secondary text-sm gap-2">
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} /> Refresh Logs
          </button>
        )}
      </div>

      {/* Lookup form */}
      <form onSubmit={handleLookup} className="flex gap-3 mb-8">
        <div className="relative flex-1">
          <Terminal size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            type="text"
            value={inputId}
            onChange={(e) => setInputId(e.target.value)}
            placeholder="Enter workflow ID to inspect execution logs..."
            className="input-field pl-10"
          />
        </div>
        <button type="submit" className="btn-primary px-6" disabled={!inputId.trim() || loading}>
          Look Up Logs
        </button>
      </form>

      {error && (
        <div className="card border-red-500/30 bg-red-500/5 mb-6 flex items-center gap-3">
          <AlertCircle size={20} className="text-red-400 flex-shrink-0" />
          <p className="text-red-400 text-sm">{error}</p>
        </div>
      )}

      {loading && (
        <div className="flex justify-center py-16">
          <Loader2 size={40} className="text-sky-500 animate-spin" />
        </div>
      )}

      {logs && !loading && (
        <div className="space-y-6">
          {/* Overview summary */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="card">
              <span className="text-xs text-slate-500 block mb-1">Status</span>
              <span className="text-lg font-semibold text-slate-200 uppercase tracking-wider">
                {logs.status || 'Unknown'}
              </span>
            </div>
            <div className="card">
              <span className="text-xs text-slate-500 block mb-1">Nodes Executed</span>
              <span className="text-lg font-semibold text-sky-400">
                {logs.nodes_completed?.length || 0} / 11
              </span>
            </div>
            <div className="card">
              <span className="text-xs text-slate-500 block mb-1">Errors Reported</span>
              <span className="text-lg font-semibold text-red-400">
                {Object.values(logs.errors || {}).filter(Boolean).length}
              </span>
            </div>
          </div>

          {/* Error alerts if any */}
          {Object.entries(logs.errors || {}).some(([_, err]) => Boolean(err)) && (
            <div className="card border-red-500/30 bg-red-500/5">
              <h3 className="text-sm font-semibold text-red-400 mb-3">Agent Errors</h3>
              <div className="space-y-2">
                {Object.entries(logs.errors).map(([node, err]) =>
                  err ? (
                    <div key={node} className="text-xs text-slate-300 font-mono bg-slate-900/60 p-2.5 rounded-lg border border-red-500/20">
                      <span className="text-red-400 font-semibold uppercase mr-2">[{node}]:</span>
                      {err}
                    </div>
                  ) : null
                )}
              </div>
            </div>
          )}

          {/* Timeline entries */}
          <div className="card">
            <h3 className="text-base font-semibold text-slate-200 mb-6 flex items-center gap-2">
              <Terminal size={18} className="text-sky-400" /> Log Stream
            </h3>

            <div className="space-y-4 font-mono text-xs">
              {logs.log_entries && logs.log_entries.length > 0 ? (
                logs.log_entries.map((entry, idx) => (
                  <div
                    key={idx}
                    className="flex items-start gap-3 p-3.5 rounded-xl bg-slate-900/50 border border-slate-800/80 hover:border-slate-700/80 transition-colors"
                  >
                    <StatusIcon status={entry.status} />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 text-slate-400 mb-1">
                        <span className="text-sky-400 font-semibold uppercase">{entry.node}</span>
                        <span>·</span>
                        <span className="text-slate-500">{entry.timestamp}</span>
                      </div>
                      <p className="text-slate-200 leading-relaxed font-sans text-sm">{entry.message}</p>
                      {entry.error && (
                        <p className="mt-2 text-red-400 font-mono bg-red-950/30 p-2 rounded border border-red-500/20">
                          {entry.error}
                        </p>
                      )}
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-slate-500 text-sm font-sans text-center py-6">No log entries available for this workflow.</p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
