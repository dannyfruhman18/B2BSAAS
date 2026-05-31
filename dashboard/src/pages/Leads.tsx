import { useState, useEffect, useCallback } from 'react'
import { useSearchParams } from 'react-router-dom'
import { fetchLeads } from '../api'
import type { Lead, LeadStatus } from '../types'
import LeadCard from '../components/LeadCard'

type FilterTab = 'all' | LeadStatus

const tabs: { id: FilterTab; label: string }[] = [
  { id: 'all', label: 'All' },
  { id: 'new', label: 'New' },
  { id: 'qualified', label: 'Qualified' },
  { id: 'personalised', label: 'Personalised' },
  { id: 'outreach', label: 'Outreach' },
  { id: 'hot', label: '🔥 Hot' },
]

function SkeletonLeadCard() {
  return (
    <div className="bg-surface border border-white/5 rounded-2xl p-4 space-y-3">
      <div className="flex justify-between items-start gap-3">
        <div className="space-y-2 flex-1">
          <div className="skeleton h-4 w-3/4 rounded-full" />
          <div className="skeleton h-3 w-1/2 rounded-full" />
          <div className="skeleton h-3 w-full rounded-full" />
          <div className="skeleton h-3 w-4/5 rounded-full" />
        </div>
        <div className="skeleton h-6 w-16 rounded-full flex-shrink-0" />
      </div>
      <div className="flex justify-between">
        <div className="skeleton h-3 w-28 rounded-full" />
        <div className="skeleton h-3 w-12 rounded-full" />
      </div>
    </div>
  )
}

export default function Leads() {
  const [searchParams, setSearchParams] = useSearchParams()
  const initialStatus = (searchParams.get('status') as FilterTab) || 'all'
  const [activeTab, setActiveTab] = useState<FilterTab>(initialStatus)
  const [leads, setLeads] = useState<Lead[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState('')

  const loadLeads = useCallback(async (tab: FilterTab) => {
    setLoading(true)
    setError(null)
    try {
      const status = tab === 'all' ? undefined : (tab as LeadStatus)
      const data = await fetchLeads(status, 100)
      setLeads(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load leads')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadLeads(activeTab)
  }, [activeTab, loadLeads])

  function handleTabChange(tab: FilterTab) {
    setActiveTab(tab)
    setSearch('')
    if (tab === 'all') {
      setSearchParams({})
    } else {
      setSearchParams({ status: tab })
    }
  }

  const filteredLeads = search.trim()
    ? leads.filter(
        (l) =>
          l.company_name.toLowerCase().includes(search.toLowerCase()) ||
          l.region.toLowerCase().includes(search.toLowerCase()) ||
          l.sic_description.toLowerCase().includes(search.toLowerCase())
      )
    : leads

  const hotLeads = filteredLeads.filter((l) => l.status === 'hot')
  const otherLeads = filteredLeads.filter((l) => l.status !== 'hot')

  return (
    <div className="px-4 py-6 sm:px-6 space-y-5 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="font-sora font-extrabold text-white text-2xl sm:text-3xl">Leads</h1>
        <p className="text-white/40 text-sm font-inter mt-0.5">
          {loading ? 'Loading...' : `${filteredLeads.length} lead${filteredLeads.length !== 1 ? 's' : ''}`}
        </p>
      </div>

      {/* Search */}
      <div className="relative">
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth={2}
          strokeLinecap="round"
          strokeLinejoin="round"
          className="w-4 h-4 text-white/30 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none"
        >
          <circle cx="11" cy="11" r="8" />
          <line x1="21" y1="21" x2="16.65" y2="16.65" />
        </svg>
        <input
          type="text"
          placeholder="Search company, region, industry…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full bg-surface border border-white/10 rounded-xl pl-10 pr-4 py-3 text-white text-sm font-inter placeholder:text-white/30 focus:outline-none focus:border-teal/50 focus:ring-1 focus:ring-teal/20 transition-colors"
        />
      </div>

      {/* Filter tabs */}
      <div className="flex gap-2 overflow-x-auto pb-1 -mx-4 px-4 sm:mx-0 sm:px-0 scrollbar-hide">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => handleTabChange(tab.id)}
            className={`flex-shrink-0 px-4 py-2 rounded-xl text-sm font-inter font-medium transition-all duration-200 ${
              activeTab === tab.id
                ? 'bg-teal text-bg'
                : 'bg-surface border border-white/10 text-white/50 hover:text-white hover:border-white/20'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Error state */}
      {error && (
        <div className="flex flex-col items-center gap-4 py-12 text-center">
          <div className="w-14 h-14 rounded-2xl bg-red-400/10 border border-red-400/20 flex items-center justify-center text-red-400 text-2xl">
            ⚠
          </div>
          <div>
            <h3 className="font-sora font-bold text-white text-base mb-1">Failed to load leads</h3>
            <p className="text-white/50 text-sm font-inter max-w-xs">{error}</p>
          </div>
          <button
            onClick={() => loadLeads(activeTab)}
            className="bg-teal text-bg font-sora font-bold text-sm px-6 py-2.5 rounded-xl transition-all hover:bg-teal-light active:scale-95"
          >
            Retry
          </button>
        </div>
      )}

      {/* Loading state */}
      {loading && !error && (
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <SkeletonLeadCard key={i} />
          ))}
        </div>
      )}

      {/* Lead list */}
      {!loading && !error && (
        <>
          {filteredLeads.length === 0 ? (
            <div className="flex flex-col items-center gap-3 py-16 text-center">
              <div className="w-14 h-14 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center text-white/20 text-2xl">
                ○
              </div>
              <div>
                <h3 className="font-sora font-semibold text-white/60 text-base mb-1">
                  {search ? 'No matches found' : 'No leads in this stage'}
                </h3>
                <p className="text-white/30 text-sm font-inter">
                  {search ? 'Try a different search term' : 'They will appear here once processed'}
                </p>
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              {/* Hot leads first */}
              {hotLeads.length > 0 && activeTab === 'all' && (
                <>
                  <div className="flex items-center gap-2">
                    <span className="text-red-400 text-xs font-inter font-semibold uppercase tracking-widest">Hot — Call Now</span>
                    <div className="flex-1 h-px bg-red-400/20" />
                  </div>
                  {hotLeads.map((lead) => (
                    <LeadCard key={lead.id} lead={lead} highlight />
                  ))}
                  {otherLeads.length > 0 && (
                    <div className="flex items-center gap-2 pt-1">
                      <span className="text-white/30 text-xs font-inter font-semibold uppercase tracking-widest">Other Leads</span>
                      <div className="flex-1 h-px bg-white/5" />
                    </div>
                  )}
                </>
              )}

              {/* Non-hot leads (or all leads when viewing hot tab) */}
              {(activeTab !== 'all' ? filteredLeads : otherLeads).map((lead) => (
                <LeadCard
                  key={lead.id}
                  lead={lead}
                  highlight={lead.status === 'hot' && activeTab === 'hot'}
                />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  )
}
