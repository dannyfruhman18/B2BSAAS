import { useNavigate } from 'react-router-dom'
import type { Lead } from '../types'
import ScoreBadge from './ScoreBadge'

interface LeadCardProps {
  lead: Lead
  highlight?: boolean
}

function timeSince(dateStr: string): string {
  const now = Date.now()
  const then = new Date(dateStr).getTime()
  const diffMs = now - then
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))
  if (diffDays === 0) return 'Today'
  if (diffDays === 1) return 'Yesterday'
  if (diffDays < 7) return `${diffDays}d ago`
  if (diffDays < 30) return `${Math.floor(diffDays / 7)}w ago`
  return `${Math.floor(diffDays / 30)}mo ago`
}

const statusLabel: Record<string, string> = {
  new: 'New',
  qualified: 'Qualified',
  personalised: 'Personalised',
  outreach: 'In Outreach',
  hot: 'Hot',
  won: 'Won',
  dead: 'Dead',
}

const statusColor: Record<string, string> = {
  new: 'text-white/50 bg-white/5 border-white/10',
  qualified: 'text-teal bg-teal/10 border-teal/20',
  personalised: 'text-sky-400 bg-sky-400/10 border-sky-400/20',
  outreach: 'text-amber-alert bg-amber-alert/10 border-amber-alert/20',
  hot: 'text-red-400 bg-red-400/10 border-red-400/20',
  won: 'text-emerald-400 bg-emerald-400/10 border-emerald-400/20',
  dead: 'text-white/30 bg-white/5 border-white/10',
}

export default function LeadCard({ lead, highlight = false }: LeadCardProps) {
  const navigate = useNavigate()

  return (
    <button
      onClick={() => navigate(`/leads/${lead.id}`)}
      className={`w-full text-left bg-surface border rounded-2xl p-4 transition-all duration-200 active:scale-[0.98] hover:bg-card group ${
        highlight
          ? 'border-teal/40 animate-pulse-ring'
          : 'border-white/5 hover:border-white/15'
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="font-sora font-semibold text-white text-sm leading-tight truncate">
              {lead.company_name}
            </h3>
            <span
              className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-inter font-semibold flex-shrink-0 ${
                statusColor[lead.status] ?? 'text-white/50 bg-white/5 border-white/10'
              }`}
            >
              {statusLabel[lead.status] ?? lead.status}
            </span>
          </div>

          <p className="text-white/40 text-xs font-inter mt-1 truncate">
            {lead.sic_description} · {lead.region}
          </p>

          {lead.weakness_summary && (
            <p className="text-white/60 text-xs font-inter mt-2 line-clamp-2 leading-relaxed">
              {lead.weakness_summary}
            </p>
          )}

          <div className="flex items-center gap-3 mt-3">
            {lead.discovered_domain && (
              <span className="text-teal/70 text-xs font-inter truncate max-w-[140px]">
                {lead.discovered_domain}
              </span>
            )}
            <span className="text-white/25 text-xs font-inter ml-auto flex-shrink-0">
              {timeSince(lead.scraped_at)}
            </span>
          </div>
        </div>

        <div className="flex-shrink-0 mt-0.5">
          <ScoreBadge score={lead.score} size="sm" />
        </div>
      </div>
    </button>
  )
}
