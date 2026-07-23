import React, { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import { getReport, getPdfUrl } from '../api/client'
import {
  Download, ExternalLink, FileText, ArrowLeft,
  Loader2, AlertCircle, Share2,
} from 'lucide-react'
import toast from 'react-hot-toast'

export default function ReportPage() {
  const { workflowId } = useParams()
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!workflowId) return
    getReport(workflowId)
      .then(setReport)
      .catch((err) => {
        const msg = err?.response?.data?.detail || 'Failed to load report'
        setError(msg)
      })
      .finally(() => setLoading(false))
  }, [workflowId])

  const handleCopyLink = () => {
    navigator.clipboard.writeText(window.location.href)
    toast.success('Link copied to clipboard')
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-24 gap-4">
        <Loader2 size={40} className="text-sky-500 animate-spin" />
        <p className="text-slate-400">Loading your report…</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="max-w-lg mx-auto mt-20 card border-red-500/30 bg-red-500/5 text-center">
        <AlertCircle size={40} className="text-red-400 mx-auto mb-4" />
        <h2 className="text-lg font-semibold text-slate-200 mb-2">Report Not Available</h2>
        <p className="text-slate-400 text-sm mb-6">{error}</p>
        <Link to="/dashboard" className="btn-secondary text-sm">
          <ArrowLeft size={14} /> Back to Dashboard
        </Link>
      </div>
    )
  }

  return (
    <div className="animate-fade-in max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <Link to="/dashboard" className="inline-flex items-center gap-1 text-sm text-slate-500 hover:text-sky-400 mb-2 transition-colors">
            <ArrowLeft size={14} /> Back to Dashboard
          </Link>
          <h1 className="text-3xl font-bold gradient-text">Business Audit Report</h1>
          <p className="text-slate-500 text-sm mt-1">Workflow: {workflowId}</p>
        </div>

        <div className="flex gap-3 flex-wrap">
          <button onClick={handleCopyLink} className="btn-secondary text-sm gap-2">
            <Share2 size={15} /> Share
          </button>
          {report?.drive_url && (
            <a href={report.drive_url} target="_blank" rel="noreferrer" className="btn-secondary text-sm gap-2">
              <ExternalLink size={15} /> Google Drive
            </a>
          )}
          {report?.pdf_url && (
            <a href={report.pdf_url} download className="btn-primary text-sm gap-2">
              <Download size={15} /> Download PDF
            </a>
          )}
        </div>
      </div>

      {/* Report content */}
      {report?.report_markdown ? (
        <div className="card">
          <article className="prose prose-invert prose-sky max-w-none
            prose-headings:text-slate-100 prose-h1:text-3xl prose-h1:font-bold prose-h1:gradient-text
            prose-h2:text-xl prose-h2:text-sky-300 prose-h2:font-semibold prose-h2:mt-8 prose-h2:mb-3
            prose-h3:text-base prose-h3:text-slate-300 prose-h3:font-semibold prose-h3:mt-6 prose-h3:mb-2
            prose-p:text-slate-400 prose-p:leading-relaxed
            prose-li:text-slate-400
            prose-strong:text-slate-200 prose-strong:font-semibold
            prose-code:text-sky-300 prose-code:bg-slate-800 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded
            prose-hr:border-slate-700
            prose-blockquote:border-l-sky-500 prose-blockquote:text-slate-400
            prose-table:text-sm prose-thead:bg-slate-800 prose-th:text-slate-200 prose-th:font-semibold prose-th:p-3
            prose-td:text-slate-400 prose-td:p-3 prose-td:border-b prose-td:border-slate-700
          ">
            <ReactMarkdown>{report.report_markdown}</ReactMarkdown>
          </article>
        </div>
      ) : (
        <div className="card text-center py-16">
          <FileText size={48} className="text-slate-700 mx-auto mb-4" />
          <p className="text-slate-500">Report content is not available yet.</p>
        </div>
      )}

      {/* Metadata footer */}
      {report?.generated_at && (
        <p className="text-center text-xs text-slate-600 mt-6">
          Generated at {new Date(report.generated_at).toLocaleString()} · Lead Intelligence AI
        </p>
      )}
    </div>
  )
}
