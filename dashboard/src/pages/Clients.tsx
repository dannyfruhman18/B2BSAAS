import { useState, useEffect } from 'react'
import { fetchClients } from '../api'
import type { Client } from '../types'

function ExternalLinkIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" className="w-3.5 h-3.5">
      <path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6" />
      <polyline points="15 3 21 3 21 9" />
      <line x1="10" y1="14" x2="21" y2="3" />
    </svg>
  )
}

function ClientCard({ client }: { client: Client }) {
  const wonDate = new Date(client.won_at).toLocaleDateString('en-GB', {
    day: 'numeric', month: 'short', year: 'numeric',
  })

  const initials = client.company_name
    .split(' ')
    .slice(0, 2)
    .map((w) => w[0])
    .join('')
    .toUpperCase()

  return (
    <div className="bg-surface border border-white/5 hover:border-teal/20 rounded-2xl p-4 transition-all duration-200 group">
      <div className="flex items-start gap-4">
        {/* Avatar */}
        <div className="w-12 h-12 rounded-xl bg-teal/15 border border-teal/20 flex items-center justify-center flex-shrink-0">
          <span className="font-sora font-bold text-teal text-sm">{initials}</span>
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2 flex-wrap">
            <div className="min-w-0">
              <h3 className="font-sora font-semibold text-white text-base truncate">
                {client.company_name}
              </h3>
              <p className="text-white/40 text-sm font-inter truncate">
                {client.contact_name}
              </p>
            </div>
            <div className="text-right flex-shrink-0">
              <p className="font-sora font-bold text-teal text-lg leading-tight">
                £{client.monthly_value_gbp.toLocaleString('en-GB')}
              </p>
              <p className="text-white/30 text-xs font-inter">/month</p>
            </div>
          </div>

          <div className="flex items-center gap-4 mt-3">
            <span className="text-white/25 text-xs font-inter">
              Won {wonDate}
            </span>
            {client.site_url && (
              <a
                href={client.site_url.startsWith('http') ? client.site_url : `https://${client.site_url}`}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1 text-teal/60 hover:text-teal text-xs font-inter transition-colors ml-auto"
                onClick={(e) => e.stopPropagation()}
              >
                Visit site
                <ExternalLinkIcon />
              </a>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

function SkeletonClientCard() {
  return (
    <div className="bg-surface border border-white/5 rounded-2xl p-4">
      <div className="flex items-start gap-4">
        <div className="skeleton w-12 h-12 rounded-xl flex-shrink-0" />
        <div className="flex-1 space-y-2">
          <div className="flex justify-between">
            <div className="skeleton h-4 w-1/2 rounded-full" />
            <div className="skeleton h-5 w-20 rounded-full" />
          </div>
          <div className="skeleton h-3 w-1/3 rounded-full" />
          <div className="skeleton h-3 w-1/4 rounded-full" />
        </div>
      </div>
    </div>
  )
}

export default function Clients() {
  const [clients, setClients] = useState<Client[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  async function loadClients() {
    setLoading(true)
    setError(null)
    try {
      const data = await fetchClients()
      setClients(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load clients')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadClients()
  }, [])

  const totalMRR = clients.reduce((sum, c) => sum + c.monthly_value_gbp, 0)
  const totalARR = totalMRR * 12

  return (
    <div className="px-4 py-6 sm:px-6 space-y-5 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="font-sora font-extrabold text-white text-2xl sm:text-3xl">Clients</h1>
        <p className="text-white/40 text-sm font-inter mt-0.5">
          Active accounts
        </p>
      </div>

      {/* MRR summary */}
      {!loading && !error && clients.length > 0 && (
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-surface border border-teal/20 rounded-2xl p-4">
            <p className="text-white/40 text-xs font-inter font-medium uppercase tracking-widest mb-1">
              MRR
            </p>
            <p className="font-sora font-bold text-teal text-3xl leading-none">
              £{totalMRR.toLocaleString('en-GB')}
            </p>
            <p className="text-white/30 text-xs font-inter mt-1.5">Monthly recurring</p>
          </div>
          <div className="bg-surface border border-white/5 rounded-2xl p-4">
            <p className="text-white/40 text-xs font-inter font-medium uppercase tracking-widest mb-1">
              ARR
            </p>
            <p className="font-sora font-bold text-white text-3xl leading-none">
              £{totalARR.toLocaleString('en-GB')}
            </p>
            <p className="text-white/30 text-xs font-inter mt-1.5">Annual run rate</p>
          </div>
        </div>
      )}

      {/* MRR skeleton */}
      {loading && (
        <div className="grid grid-cols-2 gap-3">
          <div className="skeleton h-28 rounded-2xl" />
          <div className="skeleton h-28 rounded-2xl" />
        </div>
      )}

      {/* Client count badge */}
      {!loading && !error && (
        <div className="flex items-center gap-2">
          <span className="text-white/30 text-xs font-inter font-semibold uppercase tracking-widest">
            {clients.length} active {clients.length === 1 ? 'client' : 'clients'}
          </span>
          <div className="flex-1 h-px bg-white/5" />
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="flex flex-col items-center gap-4 py-16 text-center">
          <div className="w-14 h-14 rounded-2xl bg-red-400/10 border border-red-400/20 flex items-center justify-center text-red-400 text-2xl">⚠</div>
          <div>
            <h3 className="font-sora font-bold text-white text-base mb-1">Failed to load clients</h3>
            <p className="text-white/50 text-sm font-inter max-w-xs">{error}</p>
          </div>
          <button
            onClick={loadClients}
            className="bg-teal text-bg font-sora font-bold text-sm px-6 py-2.5 rounded-xl hover:bg-teal-light transition-colors active:scale-95"
          >
            Retry
          </button>
        </div>
      )}

      {/* Loading state */}
      {loading && !error && (
        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <SkeletonClientCard key={i} />
          ))}
        </div>
      )}

      {/* Client list */}
      {!loading && !error && (
        <>
          {clients.length === 0 ? (
            <div className="flex flex-col items-center gap-3 py-16 text-center">
              <div className="w-14 h-14 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center text-white/20 text-2xl">★</div>
              <div>
                <h3 className="font-sora font-semibold text-white/60 text-base mb-1">No clients yet</h3>
                <p className="text-white/30 text-sm font-inter">
                  Mark leads as won to see them here
                </p>
              </div>
            </div>
          ) : (
            <div className="space-y-3 pb-4">
              {clients
                .slice()
                .sort((a, b) => b.monthly_value_gbp - a.monthly_value_gbp)
                .map((client) => (
                  <ClientCard key={client.id} client={client} />
                ))}
            </div>
          )}
        </>
      )}
    </div>
  )
}
