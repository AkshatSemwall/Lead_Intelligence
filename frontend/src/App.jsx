import React from 'react'
import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { Brain, FileText, Activity, LayoutDashboard, Zap } from 'lucide-react'
import LeadForm from './pages/LeadForm'
import WorkflowStatus from './pages/WorkflowStatus'
import ReportPage from './pages/ReportPage'
import LogsPage from './pages/LogsPage'
import DashboardPage from './pages/DashboardPage'

function NavLink({ to, icon: Icon, label }) {
  const loc = useLocation()
  const active = loc.pathname === to || (to !== '/' && loc.pathname.startsWith(to))
  return (
    <Link
      to={to}
      className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
        active
          ? 'bg-sky-500/15 text-sky-400 border border-sky-500/30'
          : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
      }`}
    >
      <Icon size={16} />
      {label}
    </Link>
  )
}

function Navbar() {
  return (
    <nav className="sticky top-0 z-50 glass border-b border-slate-800/80">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-3 group">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-sky-500 to-indigo-600 flex items-center justify-center shadow-lg group-hover:shadow-sky-500/30 transition-shadow">
            <Zap size={18} className="text-white" />
          </div>
          <span className="text-lg font-bold gradient-text">Lead Intelligence</span>
        </Link>

        {/* Nav links */}
        <div className="flex items-center gap-1">
          <NavLink to="/" icon={Brain} label="Submit Lead" />
          <NavLink to="/dashboard" icon={LayoutDashboard} label="Dashboard" />
          <NavLink to="/status" icon={Activity} label="Status" />
          <NavLink to="/logs" icon={FileText} label="Logs" />
        </div>
      </div>
    </nav>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen" style={{ backgroundColor: 'var(--color-bg)' }}>
        <Navbar />
        <main className="max-w-7xl mx-auto px-6 py-10">
          <Routes>
            <Route path="/" element={<LeadForm />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/status" element={<WorkflowStatus />} />
            <Route path="/status/:workflowId" element={<WorkflowStatus />} />
            <Route path="/report/:workflowId" element={<ReportPage />} />
            <Route path="/logs" element={<LogsPage />} />
            <Route path="/logs/:workflowId" element={<LogsPage />} />
          </Routes>
        </main>
        <Toaster
          position="top-right"
          toastOptions={{
            style: {
              background: '#1e293b',
              color: '#f1f5f9',
              border: '1px solid #334155',
              borderRadius: '12px',
            },
          }}
        />
      </div>
    </BrowserRouter>
  )
}
