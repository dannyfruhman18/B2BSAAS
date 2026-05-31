interface StatCardProps {
  label: string
  value: number | string
  accent?: 'teal' | 'amber' | 'red' | 'white'
  sublabel?: string
  onClick?: () => void
}

const accentClasses = {
  teal: 'text-teal',
  amber: 'text-amber-alert',
  red: 'text-red-400',
  white: 'text-white',
}

const borderClasses = {
  teal: 'border-teal/20 hover:border-teal/40',
  amber: 'border-amber-alert/20 hover:border-amber-alert/40',
  red: 'border-red-400/20 hover:border-red-400/40',
  white: 'border-white/10 hover:border-white/20',
}

export default function StatCard({
  label,
  value,
  accent = 'white',
  sublabel,
  onClick,
}: StatCardProps) {
  const Tag = onClick ? 'button' : 'div'

  return (
    <Tag
      onClick={onClick}
      className={`group bg-surface border rounded-2xl p-5 transition-all duration-200 text-left w-full ${
        borderClasses[accent]
      } ${onClick ? 'cursor-pointer hover:bg-card active:scale-95' : ''}`}
    >
      <div className="flex flex-col gap-1">
        <span className="text-white/50 text-xs font-inter font-medium uppercase tracking-widest">
          {label}
        </span>
        <span
          className={`font-sora font-bold text-4xl leading-none ${accentClasses[accent]}`}
        >
          {value}
        </span>
        {sublabel && (
          <span className="text-white/40 text-xs font-inter mt-1">{sublabel}</span>
        )}
      </div>
    </Tag>
  )
}
