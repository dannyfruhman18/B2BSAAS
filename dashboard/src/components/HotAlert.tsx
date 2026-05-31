import { useNavigate } from 'react-router-dom'
import type { Lead } from '../types'

interface HotAlertProps {
  leads: Lead[]
}

function PhoneIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2.5}
      strokeLinecap="round"
      strokeLinejoin="round"
      className="w-4 h-4"
    >
      <path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07A19.5 19.5 0 013.07 9.81a19.79 19.79 0 01-3.07-8.68A2 2 0 012.18 1H5.18a2 2 0 012 1.72c.127.96.361 1.903.7 2.81a2 2 0 01-.45 2.11L6.09 8.91a16 16 0 006 6l1.27-1.27a2 2 0 012.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0122 16.92z" />
    </svg>
  )
}

function FireIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="currentColor"
      className="w-5 h-5"
    >
      <path d="M12 23c-4.97 0-9-3.58-9-8 0-2.29 1.03-4.34 2.7-5.82C6.27 8.74 7 8 7 8s-.28 1.9 1 3c0 0 1-2 3-3.5S14 5 14 5l-.5 2.5S15 5.5 17 4l-1 4s2-1.5 3-4c.5 3.5-1 6.5-1 6.5S21 9.5 21 15c0 4.42-4.03 8-9 8z" />
    </svg>
  )
}

export default function HotAlert({ leads }: HotAlertProps) {
  const navigate = useNavigate()

  if (leads.length === 0) return null

  return (
    <div className="relative overflow-hidden rounded-2xl border border-red-400/30 bg-red-400/5">
      {/* Pulsing background glow */}
      <div className="absolute inset-0 bg-gradient-to-r from-red-400/10 via-amber-alert/5 to-transparent pointer-events-none" />
      <div className="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-red-400 to-amber-alert rounded-l-2xl" />

      <div className="relative p-4 pl-5">
        <div className="flex items-center gap-2 mb-3">
          <span className="text-red-400 animate-bounce">
            <FireIcon />
          </span>
          <h2 className="font-sora font-bold text-red-400 text-sm uppercase tracking-wider">
            Hot Leads — Call Now
          </h2>
          <span className="ml-auto bg-red-400/20 border border-red-400/30 text-red-400 text-xs font-inter font-bold rounded-full px-2 py-0.5">
            {leads.length}
          </span>
        </div>

        <div className="space-y-2">
          {leads.slice(0, 3).map((lead) => (
            <button
              key={lead.id}
              onClick={() => navigate(`/leads/${lead.id}`)}
              className="w-full flex items-center gap-3 bg-surface/50 border border-red-400/15 rounded-xl px-3 py-2.5 text-left transition-all duration-200 hover:border-red-400/30 hover:bg-surface active:scale-[0.98] group"
            >
              <span className="flex-shrink-0 w-8 h-8 rounded-full bg-red-400/15 border border-red-400/25 flex items-center justify-center text-red-400 group-hover:bg-red-400/25 transition-colors">
                <PhoneIcon />
              </span>
              <div className="min-w-0 flex-1">
                <p className="font-sora font-semibold text-white text-sm truncate">
                  {lead.company_name}
                </p>
                <p className="text-white/40 text-xs font-inter truncate">
                  {lead.region} · Score {lead.score}
                </p>
              </div>
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth={2}
                className="w-4 h-4 text-white/25 group-hover:text-white/50 flex-shrink-0 transition-colors"
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
              </svg>
            </button>
          ))}
        </div>

        {leads.length > 3 && (
          <button
            onClick={() => navigate('/leads?status=hot')}
            className="mt-3 w-full text-center text-xs text-red-400/70 font-inter hover:text-red-400 transition-colors py-1"
          >
            +{leads.length - 3} more hot leads →
          </button>
        )}
      </div>
    </div>
  )
}
