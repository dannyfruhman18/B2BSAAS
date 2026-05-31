import { useState, useEffect } from 'react'
import { checkHealth } from '../api'

type Status = 'checking' | 'ok' | 'error'

function StatusDot({ status }: { status: Status }) {
  return (
    <span className={`inline-block w-2 h-2 rounded-full flex-shrink-0 ${
      status === 'ok' ? 'bg-teal' :
      status === 'error' ? 'bg-red-400' :
      'bg-amber animate-pulse'
    }`} />
  )
}

export default function Settings() {
  const [apiStatus, setApiStatus] = useState<Status>('checking')
  const [apiUrl] = useState(import.meta.env.VITE_API_URL || '(not set)')

  useEffect(() => {
    checkHealth()
      .then(() => setApiStatus('ok'))
      .catch(() => setApiStatus('error'))
  }, [])

  return (
    <div className="px-4 py-6 sm:px-6 space-y-5 animate-fade-in">
      <div>
        <h1 className="font-sora font-extrabold text-white text-2xl sm:text-3xl">Settings</h1>
        <p className="text-white/40 text-sm font-inter mt-0.5">Connection & configuration</p>
      </div>

      {/* API connection */}
      <div className="bg-surface border border-white/5 rounded-2xl p-5 space-y-4">
        <h2 className="font-sora font-semibold text-white text-sm">Pipeline API</h2>
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-white/50 font-inter text-sm">Status</span>
            <div className="flex items-center gap-2">
              <StatusDot status={apiStatus} />
              <span className={`font-sora font-semibold text-sm ${
                apiStatus === 'ok' ? 'text-teal' :
                apiStatus === 'error' ? 'text-red-400' :
                'text-amber'
              }`}>
                {apiStatus === 'checking' ? 'Checking…' : apiStatus === 'ok' ? 'Connected' : 'Unreachable'}
              </span>
            </div>
          </div>
          <div className="flex items-start justify-between gap-4">
            <span className="text-white/50 font-inter text-sm">URL</span>
            <span className="text-white/70 font-mono text-xs text-right break-all">{apiUrl}</span>
          </div>
        </div>
        <button
          onClick={() => {
            setApiStatus('checking')
            checkHealth()
              .then(() => setApiStatus('ok'))
              .catch(() => setApiStatus('error'))
          }}
          className="text-teal font-sora font-semibold text-sm hover:underline transition-all"
        >
          Re-check connection
        </button>
      </div>

      {/* Environment info */}
      <div className="bg-surface border border-white/5 rounded-2xl p-5 space-y-3">
        <h2 className="font-sora font-semibold text-white text-sm">Configuration</h2>
        <p className="text-white/40 font-inter text-sm leading-relaxed">
          Set environment variables in Cloudflare Pages → Settings → Environment variables:
        </p>
        <div className="space-y-2">
          {[
            ['VITE_API_URL', 'http://YOUR_SERVER_IP:8000', 'Pipeline API base URL'],
            ['VITE_DASHBOARD_SECRET', 'your-secret-here', 'Auth token for API calls'],
          ].map(([key, example, desc]) => (
            <div key={key} className="bg-bg border border-white/8 rounded-xl p-3 space-y-1">
              <div className="flex items-center gap-2">
                <code className="text-teal font-mono text-xs">{key}</code>
              </div>
              <p className="text-white/30 font-inter text-xs">{desc}</p>
              <p className="text-white/20 font-mono text-xs">e.g. {example}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Legal + compliance */}
      <div className="bg-surface border border-amber/10 rounded-2xl p-5 space-y-2">
        <h2 className="font-sora font-semibold text-amber text-sm">PECR Compliance</h2>
        <p className="text-white/50 font-inter text-sm leading-relaxed">
          Every outbound email includes your real name, trading name (Brightwick),
          postal address, and a one-click opt-out. Only active UK Ltd / LLP targets
          are emailed — Companies House confirmation is mandatory. Opted-out contacts
          are never re-contacted.
        </p>
        <p className="text-white/30 font-inter text-xs mt-2">
          ICO Data Protection Fee (~£40/yr) must remain active while processing personal data.
        </p>
      </div>
    </div>
  )
}
