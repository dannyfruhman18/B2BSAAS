import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { fetchLeadDetail, markLeadWon, markLeadDead } from '../api'
import type { LeadDetail as LeadDetailType } from '../types'
import ScoreBadge from '../components/ScoreBadge'

function BackArrow() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5} strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5">
      <path d="M19 12H5M12 5l-7 7 7 7" />
    </svg>
  )
}

function ExternalLinkIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" className="w-4 h-4">
      <path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6" />
      <polyline points="15 3 21 3 21 9" />
      <line x1="10" y1="14" x2="21" y2="3" />
    </svg>
  )
}

function MarkWonModal({
  onClose,
  onConfirm,
  loading,
}: {
  onClose: () => void
  onConfirm: (monthly: number, name: string, email: string) => Promise<void>
  loading: boolean
}) {
  const [monthly, setMonthly] = useState('')
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [err, setErr] = useState('')

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setErr('')
    const val = parseFloat(monthly)
    if (!val || val <= 0) { setErr('Enter a valid monthly value'); return }
    if (!name.trim()) { setErr('Contact name is required'); return }
    if (!email.trim() || !email.includes('@')) { setErr('Enter a valid email'); return }
    try {
      await onConfirm(val, name.trim(), email.trim())
    } catch {
      setErr('Failed to mark as won. Please try again.')
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-fade-in"
      onClick={(e) => { if (e.target === e.currentTarget) onClose() }}
    >
      <div className="w-full max-w-md bg-surface border border-teal/25 rounded-3xl p-6 space-y-5 animate-slide-up">
        <div className="flex items-center justify-between">
          <h2 className="font-sora font-bold text-white text-xl">Mark as Won</h2>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-white/5 hover:bg-white/10 flex items-center justify-center text-white/50 transition-colors"
          >
            ✕
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-white/60 text-xs font-inter font-medium uppercase tracking-widest mb-1.5">
              Monthly Value (GBP)
            </label>
            <div className="relative">
              <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-white/40 font-inter font-semibold">£</span>
              <input
                type="number"
                min="1"
                step="any"
                placeholder="e.g. 1500"
                value={monthly}
                onChange={(e) => setMonthly(e.target.value)}
                className="w-full bg-bg border border-white/10 rounded-xl pl-8 pr-4 py-3 text-white font-inter placeholder:text-white/25 focus:outline-none focus:border-teal/50 focus:ring-1 focus:ring-teal/20 transition-colors text-sm"
              />
            </div>
          </div>

          <div>
            <label className="block text-white/60 text-xs font-inter font-medium uppercase tracking-widest mb-1.5">
              Contact Name
            </label>
            <input
              type="text"
              placeholder="e.g. Jane Smith"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full bg-bg border border-white/10 rounded-xl px-4 py-3 text-white font-inter placeholder:text-white/25 focus:outline-none focus:border-teal/50 focus:ring-1 focus:ring-teal/20 transition-colors text-sm"
            />
          </div>

          <div>
            <label className="block text-white/60 text-xs font-inter font-medium uppercase tracking-widest mb-1.5">
              Contact Email
            </label>
            <input
              type="email"
              placeholder="jane@company.co.uk"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full bg-bg border border-white/10 rounded-xl px-4 py-3 text-white font-inter placeholder:text-white/25 focus:outline-none focus:border-teal/50 focus:ring-1 focus:ring-teal/20 transition-colors text-sm"
            />
          </div>

          {err && (
            <p className="text-red-400 text-xs font-inter bg-red-400/10 border border-red-400/20 rounded-xl px-3 py-2">
              {err}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-teal hover:bg-teal-light text-bg font-sora font-bold text-sm py-3.5 rounded-xl transition-all active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Marking as Won…' : 'Confirm Won ✓'}
          </button>
        </form>
      </div>
    </div>
  )
}

function TimelineEvent({
  type,
  summary,
  createdAt,
}: {
  type: string
  summary: string
  createdAt: string
}) {
  const icons: Record<string, string> = {
    email_sent: '📧',
    reply_received: '↩',
    call_scheduled: '📅',
    call_completed: '✓',
    note: '📝',
  }
  const colors: Record<string, string> = {
    email_sent: 'border-sky-400/30 bg-sky-400/10 text-sky-400',
    reply_received: 'border-teal/30 bg-teal/10 text-teal',
    call_scheduled: 'border-amber-alert/30 bg-amber-alert/10 text-amber-alert',
    call_completed: 'border-emerald-400/30 bg-emerald-400/10 text-emerald-400',
    note: 'border-white/15 bg-white/5 text-white/50',
  }

  return (
    <div className="flex gap-3">
      <div className={`flex-shrink-0 w-8 h-8 rounded-full border flex items-center justify-center text-sm ${colors[type] ?? 'border-white/15 bg-white/5 text-white/50'}`}>
        {icons[type] ?? '○'}
      </div>
      <div className="flex-1 min-w-0 pb-4 border-b border-white/5 last:border-0">
        <p className="text-white text-sm font-inter leading-relaxed">{summary}</p>
        <p className="text-white/30 text-xs font-inter mt-1">
          {new Date(createdAt).toLocaleString('en-GB', {
            day: 'numeric', month: 'short', year: 'numeric',
            hour: '2-digit', minute: '2-digit',
          })}
        </p>
      </div>
    </div>
  )
}

function EmailPreview({ subject, body, generatedAt }: { subject: string; body: string; generatedAt: string }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className="bg-bg border border-white/8 rounded-xl overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-white/3 transition-colors text-left"
      >
        <div className="min-w-0 flex-1">
          <p className="font-inter font-semibold text-white text-sm truncate">{subject}</p>
          <p className="text-white/30 text-xs font-inter mt-0.5">
            {new Date(generatedAt).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })}
          </p>
        </div>
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth={2}
          strokeLinecap="round"
          strokeLinejoin="round"
          className={`w-4 h-4 text-white/40 flex-shrink-0 ml-3 transition-transform duration-200 ${expanded ? 'rotate-180' : ''}`}
        >
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>
      {expanded && (
        <div className="px-4 pb-4 border-t border-white/5 animate-fade-in">
          <pre className="text-white/70 text-xs font-inter leading-relaxed whitespace-pre-wrap mt-3 font-sans">
            {body}
          </pre>
        </div>
      )}
    </div>
  )
}

function SkeletonDetail() {
  return (
    <div className="px-4 py-6 sm:px-6 space-y-6 animate-fade-in">
      <div className="flex items-center gap-3">
        <div className="skeleton w-8 h-8 rounded-full" />
        <div className="skeleton h-4 w-32 rounded-full" />
      </div>
      <div className="space-y-3">
        <div className="skeleton h-8 w-3/4 rounded-xl" />
        <div className="skeleton h-4 w-1/2 rounded-full" />
        <div className="skeleton h-4 w-2/3 rounded-full" />
      </div>
      <div className="skeleton h-24 rounded-2xl" />
      <div className="skeleton h-32 rounded-2xl" />
    </div>
  )
}

export default function LeadDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [lead, setLead] = useState<LeadDetailType | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showWonModal, setShowWonModal] = useState(false)
  const [wonLoading, setWonLoading] = useState(false)
  const [deadLoading, setDeadLoading] = useState(false)
  const [actionDone, setActionDone] = useState<'won' | 'dead' | null>(null)

  async function loadLead() {
    if (!id) return
    setLoading(true)
    setError(null)
    try {
      const data = await fetchLeadDetail(id)
      setLead(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load lead')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadLead()
  }, [id])

  async function handleMarkWon(monthly: number, contactName: string, contactEmail: string) {
    if (!id) return
    setWonLoading(true)
    try {
      await markLeadWon(id, {
        monthly_value_gbp: monthly,
        contact_name: contactName,
        contact_email: contactEmail,
      })
      setActionDone('won')
      setShowWonModal(false)
    } finally {
      setWonLoading(false)
    }
  }

  async function handleMarkDead() {
    if (!id || deadLoading) return
    const confirmed = window.confirm('Mark this lead as dead? This cannot be undone.')
    if (!confirmed) return
    setDeadLoading(true)
    try {
      await markLeadDead(id)
      setActionDone('dead')
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to mark as dead')
    } finally {
      setDeadLoading(false)
    }
  }

  if (loading) return <SkeletonDetail />

  if (error) {
    return (
      <div className="px-4 py-6 sm:px-6 flex flex-col items-center gap-4 text-center min-h-[50vh] justify-center animate-fade-in">
        <div className="w-14 h-14 rounded-2xl bg-red-400/10 border border-red-400/20 flex items-center justify-center text-red-400 text-2xl">⚠</div>
        <div>
          <h2 className="font-sora font-bold text-white text-lg mb-1">Error Loading Lead</h2>
          <p className="text-white/50 text-sm font-inter max-w-xs">{error}</p>
        </div>
        <div className="flex gap-3">
          <button onClick={() => navigate(-1)} className="border border-white/15 text-white/60 font-inter text-sm px-5 py-2.5 rounded-xl hover:border-white/25 transition-colors">
            Back
          </button>
          <button onClick={loadLead} className="bg-teal text-bg font-sora font-bold text-sm px-5 py-2.5 rounded-xl hover:bg-teal-light transition-colors active:scale-95">
            Retry
          </button>
        </div>
      </div>
    )
  }

  if (!lead) return null

  const isActioned = actionDone !== null || lead.status === 'won' || lead.status === 'dead'

  return (
    <>
      <div className="px-4 py-6 sm:px-6 space-y-6 animate-fade-in">
        {/* Back button */}
        <button
          onClick={() => navigate(-1)}
          className="flex items-center gap-2 text-white/50 hover:text-white transition-colors text-sm font-inter -ml-1"
        >
          <BackArrow />
          Leads
        </button>

        {/* Action done banner */}
        {actionDone && (
          <div className={`rounded-2xl border p-4 flex items-center gap-3 ${
            actionDone === 'won'
              ? 'bg-teal/10 border-teal/30 text-teal'
              : 'bg-red-400/10 border-red-400/30 text-red-400'
          }`}>
            <span className="text-xl">{actionDone === 'won' ? '✓' : '✕'}</span>
            <p className="font-sora font-semibold text-sm">
              {actionDone === 'won'
                ? 'Lead marked as Won! Head to Clients to see them.'
                : 'Lead marked as Dead.'}
            </p>
          </div>
        )}

        {/* Company header */}
        <div>
          <div className="flex items-start justify-between gap-3 flex-wrap">
            <div className="min-w-0">
              <h1 className="font-sora font-extrabold text-white text-2xl sm:text-3xl leading-tight">
                {lead.company_name}
              </h1>
              <p className="text-white/50 text-sm font-inter mt-1">
                {lead.sic_description} · {lead.region}
              </p>
            </div>
            <ScoreBadge score={lead.score} size="lg" />
          </div>

          {lead.discovered_domain && (
            <a
              href={`https://${lead.discovered_domain}`}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 mt-3 text-teal text-sm font-inter hover:text-teal-light transition-colors"
            >
              {lead.discovered_domain}
              <ExternalLinkIcon />
            </a>
          )}
        </div>

        {/* Weakness summary */}
        {lead.weakness_summary && (
          <div className="bg-surface border border-amber-alert/20 rounded-2xl p-4">
            <h2 className="font-inter font-semibold text-amber-alert text-xs uppercase tracking-widest mb-2">
              Weakness Analysis
            </h2>
            <p className="text-white/80 text-sm font-inter leading-relaxed">
              {lead.weakness_summary}
            </p>
          </div>
        )}

        {/* Score meter */}
        <div className="bg-surface border border-white/5 rounded-2xl p-5">
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-inter font-semibold text-white/50 text-xs uppercase tracking-widest">
              Lead Score
            </h2>
            <span className="font-sora font-bold text-white text-2xl">{lead.score}<span className="text-white/30 text-sm font-inter">/100</span></span>
          </div>
          <div className="h-2.5 bg-bg rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-700 ${
                lead.score >= 80 ? 'bg-red-400' : lead.score >= 50 ? 'bg-amber-alert' : 'bg-teal'
              }`}
              style={{ width: `${lead.score}%` }}
            />
          </div>
          <div className="flex justify-between mt-2 text-white/25 text-xs font-inter">
            <span>Low risk (buy signals)</span>
            <span>High risk (urgent need)</span>
          </div>
        </div>

        {/* Contact info (if won) */}
        {(lead.contact_name || lead.contact_email) && (
          <div className="bg-surface border border-white/5 rounded-2xl p-4">
            <h2 className="font-inter font-semibold text-white/50 text-xs uppercase tracking-widest mb-3">Contact</h2>
            {lead.contact_name && (
              <p className="text-white font-inter text-sm font-medium">{lead.contact_name}</p>
            )}
            {lead.contact_email && (
              <a
                href={`mailto:${lead.contact_email}`}
                className="text-teal text-sm font-inter hover:text-teal-light transition-colors"
              >
                {lead.contact_email}
              </a>
            )}
            {lead.monthly_value_gbp && (
              <p className="text-emerald-400 font-sora font-bold text-lg mt-2">
                £{lead.monthly_value_gbp.toLocaleString('en-GB')}<span className="text-white/30 text-xs font-inter font-normal">/mo</span>
              </p>
            )}
          </div>
        )}

        {/* Email previews */}
        {lead.emails && lead.emails.length > 0 && (
          <div className="space-y-3">
            <h2 className="font-inter font-semibold text-white/50 text-xs uppercase tracking-widest">
              Generated Emails ({lead.emails.length})
            </h2>
            {lead.emails.map((email, i) => (
              <EmailPreview
                key={i}
                subject={email.subject}
                body={email.body_text}
                generatedAt={email.generated_at}
              />
            ))}
          </div>
        )}

        {/* Outreach timeline */}
        {lead.outreach_history && lead.outreach_history.length > 0 && (
          <div className="space-y-3">
            <h2 className="font-inter font-semibold text-white/50 text-xs uppercase tracking-widest">
              Outreach Timeline
            </h2>
            <div className="bg-surface border border-white/5 rounded-2xl p-4 space-y-3">
              {lead.outreach_history.map((event) => (
                <TimelineEvent
                  key={event.id}
                  type={event.type}
                  summary={event.summary}
                  createdAt={event.created_at}
                />
              ))}
            </div>
          </div>
        )}

        {/* Metadata */}
        <div className="flex items-center justify-between bg-surface border border-white/5 rounded-2xl px-4 py-3">
          <span className="text-white/30 text-xs font-inter">Scraped</span>
          <span className="text-white/50 text-xs font-inter">
            {new Date(lead.scraped_at).toLocaleDateString('en-GB', {
              day: 'numeric', month: 'short', year: 'numeric',
            })}
          </span>
        </div>

        {/* Action buttons */}
        {!isActioned && (
          <div className="space-y-3 pb-4">
            <button
              onClick={() => setShowWonModal(true)}
              className="w-full bg-teal hover:bg-teal-light text-bg font-sora font-bold text-base py-4 rounded-2xl transition-all active:scale-[0.98]"
            >
              Mark as Won
            </button>
            <button
              onClick={handleMarkDead}
              disabled={deadLoading}
              className="w-full border border-red-400/30 text-red-400 hover:border-red-400/50 hover:bg-red-400/5 font-sora font-semibold text-sm py-3.5 rounded-2xl transition-all active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {deadLoading ? 'Processing…' : 'Mark as Dead'}
            </button>
          </div>
        )}
      </div>

      {/* Won modal */}
      {showWonModal && (
        <MarkWonModal
          onClose={() => setShowWonModal(false)}
          onConfirm={handleMarkWon}
          loading={wonLoading}
        />
      )}
    </>
  )
}
