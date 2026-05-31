import type { PipelineStats } from '../types'

interface PipelineBarProps {
  stats: PipelineStats
}

interface Stage {
  key: keyof PipelineStats
  label: string
  color: string
  bg: string
}

const stages: Stage[] = [
  { key: 'new', label: 'New', color: 'bg-white/30', bg: 'bg-white/10' },
  { key: 'qualified', label: 'Qualified', color: 'bg-teal', bg: 'bg-teal/20' },
  { key: 'personalised', label: 'Personalised', color: 'bg-sky-400', bg: 'bg-sky-400/20' },
  { key: 'outreach', label: 'Outreach', color: 'bg-amber-alert', bg: 'bg-amber-alert/20' },
  { key: 'hot', label: 'Hot', color: 'bg-red-400', bg: 'bg-red-400/20' },
  { key: 'won', label: 'Won', color: 'bg-emerald-400', bg: 'bg-emerald-400/20' },
]

export default function PipelineBar({ stats }: PipelineBarProps) {
  const activeTotal = stages.reduce((sum, s) => sum + stats[s.key], 0)

  return (
    <div className="bg-surface border border-white/5 rounded-2xl p-5">
      <h2 className="font-sora font-semibold text-white text-sm mb-4 uppercase tracking-widest opacity-60">
        Pipeline Overview
      </h2>

      {/* Stacked bar */}
      {activeTotal > 0 ? (
        <div className="flex rounded-full overflow-hidden h-3 mb-5 gap-0.5">
          {stages.map((stage) => {
            const count = stats[stage.key]
            if (count === 0) return null
            const pct = (count / activeTotal) * 100
            return (
              <div
                key={stage.key}
                className={`${stage.color} transition-all duration-700 first:rounded-l-full last:rounded-r-full`}
                style={{ width: `${pct}%` }}
                title={`${stage.label}: ${count}`}
              />
            )
          })}
        </div>
      ) : (
        <div className="h-3 rounded-full bg-white/5 mb-5" />
      )}

      {/* Stage breakdown */}
      <div className="grid grid-cols-3 sm:grid-cols-6 gap-2">
        {stages.map((stage) => {
          const count = stats[stage.key]
          const pct = activeTotal > 0 ? Math.round((count / activeTotal) * 100) : 0
          return (
            <div
              key={stage.key}
              className={`rounded-xl p-2.5 text-center ${stage.bg} border border-white/5`}
            >
              <div className="font-sora font-bold text-white text-lg leading-none">
                {count}
              </div>
              <div className="text-white/40 text-[10px] font-inter mt-1 leading-tight">
                {stage.label}
              </div>
              <div className="text-white/20 text-[9px] font-inter mt-0.5">
                {pct}%
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
