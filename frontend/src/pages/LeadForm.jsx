import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { submitLead } from '../api/client'
import {
  Send, User, Mail, Building2, Globe, Phone, MessageSquare,
  Sparkles, Shield, Zap, BarChart3, CheckCircle,
} from 'lucide-react'

const features = [
  { icon: Zap, label: 'AI-Powered Research', desc: 'Deep company intelligence gathered automatically' },
  { icon: BarChart3, label: 'Business Analysis', desc: 'SWOT, AI opportunities, and market positioning' },
  { icon: Shield, label: 'Professional PDF Report', desc: 'Consulting-grade report delivered to your inbox' },
]

function FloatingParticle({ style }) {
  return <div className="absolute w-1 h-1 rounded-full bg-sky-500/30 animate-pulse" style={style} />
}

export default function LeadForm() {
  const navigate = useNavigate()
  const [form, setForm] = useState({
    name: '', email: '', company: '', website: '', phone: '', message: '',
  })
  const [errors, setErrors] = useState({})
  const [loading, setLoading] = useState(false)

  const validate = () => {
    const errs = {}
    if (!form.name.trim()) errs.name = 'Name is required'
    if (!form.email.trim()) errs.email = 'Email is required'
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) errs.email = 'Invalid email address'
    if (!form.company.trim()) errs.company = 'Company name is required'
    if (!form.website.trim()) errs.website = 'Website is required'
    setErrors(errs)
    return Object.keys(errs).length === 0
  }

  const handleChange = (e) => {
    const { name, value } = e.target
    setForm((p) => ({ ...p, [name]: value }))
    if (errors[name]) setErrors((p) => ({ ...p, [name]: undefined }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!validate()) return
    setLoading(true)
    try {
      const res = await submitLead(form)
      toast.success('Lead submitted! Your report is being generated.')
      navigate(`/status/${res.workflow_id}`)
    } catch (err) {
      const msg = err?.response?.data?.detail || 'Submission failed. Please try again.'
      toast.error(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="animate-fade-in">
      {/* Hero section */}
      <div className="relative text-center mb-14 overflow-hidden">
        <div className="absolute inset-0 -z-10">
          {[...Array(8)].map((_, i) => (
            <FloatingParticle key={i} style={{
              top: `${Math.random() * 100}%`,
              left: `${Math.random() * 100}%`,
              animationDelay: `${i * 0.5}s`,
              animationDuration: `${2 + Math.random() * 2}s`,
            }} />
          ))}
        </div>
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass mb-6 text-sm text-sky-400 border border-sky-500/20">
          <Sparkles size={14} className="text-sky-400" />
          Autonomous AI-Powered Lead Intelligence
        </div>
        <h1 className="text-5xl font-bold mb-5 leading-tight">
          Get Your Free{' '}
          <span className="gradient-text">Business Audit</span>
          <br />Report in Minutes
        </h1>
        <p className="text-slate-400 text-lg max-w-2xl mx-auto leading-relaxed">
          Our AI agents research your company, analyse your digital presence, identify AI opportunities,
          and deliver a personalised consulting report directly to your inbox.
        </p>

        {/* Feature pills */}
        <div className="flex flex-wrap justify-center gap-4 mt-8">
          {features.map(({ icon: Icon, label, desc }) => (
            <div key={label} className="flex items-center gap-3 glass rounded-xl px-5 py-3 max-w-xs">
              <div className="w-8 h-8 rounded-lg bg-sky-500/15 flex items-center justify-center flex-shrink-0">
                <Icon size={16} className="text-sky-400" />
              </div>
              <div className="text-left">
                <div className="text-sm font-semibold text-slate-200">{label}</div>
                <div className="text-xs text-slate-500">{desc}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Form card */}
      <div className="max-w-2xl mx-auto">
        <div className="card gradient-border">
          <div className="flex items-center gap-3 mb-8">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-sky-500 to-indigo-600 flex items-center justify-center">
              <Send size={18} className="text-white" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-100">Submit Your Lead</h2>
              <p className="text-sm text-slate-500">Fill in your details to receive your free audit</p>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5" noValidate>
            {/* Row 1: Name + Email */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <FormField
                icon={User} label="Full Name" name="name" type="text"
                placeholder="Jane Smith" value={form.name}
                onChange={handleChange} error={errors.name} required
              />
              <FormField
                icon={Mail} label="Email Address" name="email" type="email"
                placeholder="jane@company.com" value={form.email}
                onChange={handleChange} error={errors.email} required
              />
            </div>

            {/* Row 2: Company + Website */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <FormField
                icon={Building2} label="Company Name" name="company" type="text"
                placeholder="Acme Corporation" value={form.company}
                onChange={handleChange} error={errors.company} required
              />
              <FormField
                icon={Globe} label="Website URL" name="website" type="url"
                placeholder="https://acme.com" value={form.website}
                onChange={handleChange} error={errors.website} required
              />
            </div>

            {/* Phone */}
            <FormField
              icon={Phone} label="Phone (Optional)" name="phone" type="tel"
              placeholder="+1 (555) 000-0000" value={form.phone}
              onChange={handleChange}
            />

            {/* Message */}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                <span className="flex items-center gap-2">
                  <MessageSquare size={14} className="text-slate-500" />
                  Additional Notes (Optional)
                </span>
              </label>
              <textarea
                name="message"
                value={form.message}
                onChange={handleChange}
                placeholder="Tell us about your specific challenges or goals…"
                rows={3}
                className="input-field resize-none"
              />
            </div>

            {/* Disclaimer */}
            <div className="flex items-start gap-3 p-4 rounded-xl bg-slate-800/50 border border-slate-700/50">
              <CheckCircle size={16} className="text-sky-400 flex-shrink-0 mt-0.5" />
              <p className="text-xs text-slate-500 leading-relaxed">
                By submitting, you agree that our AI will research publicly available information about your company
                to generate a personalised business audit report. No payment required.
              </p>
            </div>

            <button type="submit" className="btn-primary w-full" disabled={loading}>
              {loading ? (
                <>
                  <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Submitting…
                </>
              ) : (
                <>
                  <Send size={16} />
                  Generate My Free Audit Report
                </>
              )}
            </button>
          </form>
        </div>

        {/* Social proof */}
        <div className="mt-8 text-center text-sm text-slate-600">
          <span className="text-slate-500">Powered by</span>{' '}
          <span className="text-sky-500 font-medium">Gemini AI</span> ·{' '}
          <span className="text-sky-500 font-medium">Tavily</span> ·{' '}
          <span className="text-sky-500 font-medium">Firecrawl</span>
        </div>
      </div>
    </div>
  )
}

function FormField({ icon: Icon, label, name, type, placeholder, value, onChange, error, required }) {
  return (
    <div>
      <label className="block text-sm font-medium text-slate-300 mb-2">
        <span className="flex items-center gap-2">
          <Icon size={14} className="text-slate-500" />
          {label} {required && <span className="text-sky-500">*</span>}
        </span>
      </label>
      <input
        type={type}
        name={name}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        className={`input-field ${error ? 'error' : ''}`}
        required={required}
      />
      {error && <p className="mt-1 text-xs text-red-400">{error}</p>}
    </div>
  )
}
