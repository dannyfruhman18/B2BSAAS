interface ScoreBadgeProps {
  score: number
  size?: 'sm' | 'md' | 'lg'
}

function getScoreConfig(score: number) {
  if (score >= 80) {
    return {
      bg: 'bg-red-400/15',
      text: 'text-red-400',
      border: 'border-red-400/30',
      label: 'High Risk',
    }
  }
  if (score >= 50) {
    return {
      bg: 'bg-amber-alert/15',
      text: 'text-amber-alert',
      border: 'border-amber-alert/30',
      label: 'Medium',
    }
  }
  return {
    bg: 'bg-teal/15',
    text: 'text-teal',
    border: 'border-teal/30',
    label: 'Low Risk',
  }
}

const sizeClasses = {
  sm: 'text-xs px-2 py-0.5',
  md: 'text-sm px-3 py-1',
  lg: 'text-base px-4 py-1.5',
}

export default function ScoreBadge({ score, size = 'md' }: ScoreBadgeProps) {
  const config = getScoreConfig(score)

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border font-inter font-semibold ${config.bg} ${config.text} ${config.border} ${sizeClasses[size]}`}
      title={`Score: ${score}/100 — ${config.label}`}
    >
      <span className="font-bold">{score}</span>
      <span className="opacity-70 font-normal hidden sm:inline">{config.label}</span>
    </span>
  )
}
