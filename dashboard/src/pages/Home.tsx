import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { fetchPipelineStats, fetchLeads } from '../api'
import type { PipelineStats, Lead } from '../types'
import StatCard from '../components/StatCard'
import PipelineBar from '../components/PipelineBar'
import HotAlert from '../components/HotAlert'

function SkeletonCard() {
  return (
    <div className="bg-surface border border-white/5 rounded-2xl p-5 space-y-3">
      <div className="skeleton h-3 w-24 rounded-full" />
      <div className="skeleton h-10 w-16 rounded-lg" />
    </div>
  )
}

function SkeletonBar() {
  return (
    <div className="bg-surface border border-white/5 rounded-2xl p-5 space-y-4">
      <div className="skeleton h-3 w-40 rounded-full" />
      <div className="skeleton h-3 w-full rounded-full" />
      <div className="grid grid-cols-6 gap-2">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="skeleton h-14 rounded-xl" />
        ))}
      </div>
    </div>
  )
}

function isMondayMorning(): boolean {
  const now = new Date()
  return now.getDay() === 1 && now.getHours() < 12
}

function WeeklyBanner({ stats }: { stats: PipelineStats }) {
  if (!isMondayMorning()) return null

  const weekTotal = stats.new + stats.qualified + stats.outreach
  return (
    <div className="bg-gradient-to-r from-teal/15 to-teal/5 border border-teal/25 rounded-2xl p-4">
      <div className="flex items-center gap-2 mb-1">
        <span className="text-teal text-base">✦</span>
        <span className="font-sora font-semibold text-teal text-sm">Weekly Digest</span>
      </div>
      <p className="text-white/70 text-sm font-inter leading-relaxed">
        Good morning. You have{' '}
        <span className="text-white font-semibold">{weekTotal} active leads</span> in the pipeline,{' '}
        <span className="text-red-400 font-semibold">{stats.hot} hot</span> requiring calls, and{' '}
        <span className="text-emerald-400 font-semibold">{stats.won} won</span> this cycle.
      </p>
    </div>
  )
}

export default function Home() {
  const navigate = useNavigate()
  const [stats, setStats] = useState<PipelineStats | null>(null)
  const [hotLeads, setHotLeads] = useState<Lead[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  async function loadData() {
    setLoading(true)
    setError(null)
    try {
      const [s, hot] = await Promise.all([
        fetchPipelineStats(),
        fetchLeads('hot', 10),
      ])
      setStats(s)
      setHotLeads(hot)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  if (error) {
    return (
      <div className="px-4 py-8 sm:px-6 flex flex-col items-center justify-center min-h-[60vh] gap-4 text-center animate-fade-in">
        <div className="w-16 h-16 rounded-2xl bg-red-400/10 border border-red-400/20 flex items-center justify-center text-red-400 text-2xl">
          ⚠
        </div>
        <div>
          <h2 className="font-sora font-bold text-white text-lg mb-1">Connection Error</h2>
          <p className="text-white/50 text-sm font-inter max-w-xs">{error}</p>
        </div>
        <button
          onClick={loadData}
          className="bg-teal text-bg font-sora font-bold text-sm px-6 py-3 rounded-xl transition-all hover:bg-teal-light active:scale-95"
        >
          Retry
        </button>
      </div>
    )
  }

  return (
    <div className="px-4 py-6 sm:px-6 space-y-6 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="font-sora font-extrabold text-white text-2xl sm:text-3xl">Dashboard</h1>
        <p className="text-white/40 text-sm font-inter mt-0.5">Brightwick Lead Pipeline</p>
      </div>

      {/* Weekly digest (Monday only) */}
      {stats && <WeeklyBanner stats={stats} />}

      {/* Hot leads alert */}
      {loading ? (
        <div className="skeleton h-32 rounded-2xl" />
      ) : (
        hotLeads.length > 0 && <HotAlert leads={hotLeads} />
      )}

      {/* Pipeline overview bar */}
      {loading ? (
        <SkeletonBar />
      ) : (
        stats && <PipelineBar stats={stats} />
      )}

      {/* Stat cards grid */}
      <div>
        <h2 className="font-inter font-medium text-white/40 text-xs uppercase tracking-widest mb-3">
          Pipeline Stats
        </h2>
        {loading ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {Array.from({ length: 6 }).map((_, i) => <SkeletonCard key={i} />)}
          </div>
        ) : stats ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            <StatCard
              label="New"
              value={stats.new}
              accent="white"
              onClick={() => navigate('/leads?status=new')}
            />
            <StatCard
              label="Qualified"
              value={stats.qualified}
              accent="teal"
              onClick={() => navigate('/leads?status=qualified')}
            />
            <StatCard
              label="Outreach"
              value={stats.outreach}
              accent="amber"
              onClick={() => navigate('/leads?status=outreach')}
            />
            <StatCard
              label="Hot"
              value={stats.hot}
              accent="red"
              sublabel="Needs a call"
              onClick={() => navigate('/leads?status=hot')}
            />
            <StatCard
              label="Won"
              value={stats.won}
              accent="teal"
              sublabel="Active clients"
              onClick={() => navigate('/clients')}
            />
            <StatCard
              label="Dead"
              value={stats.dead}
              accent="white"
              sublabel="Closed out"
            />
          </div>
        ) : null}
      </div>

      {/* Quick actions */}
      <div className="grid grid-cols-2 gap-3 pb-4">
        <button
          onClick={() => navigate('/leads?status=new')}
          className="flex items-center gap-3 bg-surface border border-white/5 hover:border-teal/30 rounded-2xl p-4 text-left transition-all active:scale-95 group"
        >
          <span className="w-10 h-10 rounded-xl bg-teal/10 border border-teal/20 flex items-center justify-center text-teal text-lg flex-shrink-0">
            ＋
          </span>
          <div>
            <p className="font-sora font-semibold text-white text-sm">New Leads</p>
            <p className="text-white/40 text-xs font-inter">Review &amp; qualify</p>
          </div>
        </button>
        <button
          onClick={() => navigate('/clients')}
          className="flex items-center gap-3 bg-surface border border-white/5 hover:border-teal/30 rounded-2xl p-4 text-left transition-all active:scale-95 group"
        >
          <span className="w-10 h-10 rounded-xl bg-emerald-400/10 border border-emerald-400/20 flex items-center justify-center text-emerald-400 text-lg flex-shrink-0">
            ★
          </span>
          <div>
            <p className="font-sora font-semibold text-white text-sm">Clients</p>
            <p className="text-white/40 text-xs font-inter">View MRR &amp; accounts</p>
          </div>
        </button>
      </div>
    </div>
  )
}
