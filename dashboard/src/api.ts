import type {
  PipelineStats,
  Lead,
  LeadDetail,
  Client,
  HealthStatus,
  LeadStatus,
  MarkWonPayload,
} from './types'

const BASE_URL = import.meta.env.VITE_API_URL ?? ''
const SECRET = import.meta.env.VITE_DASHBOARD_SECRET ?? ''

function authHeaders(): HeadersInit {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  }
  if (SECRET) {
    headers['Authorization'] = `Bearer ${SECRET}`
  }
  return headers
}

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      ...authHeaders(),
      ...(options?.headers ?? {}),
    },
  })
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText)
    throw new Error(`API error ${res.status}: ${text}`)
  }
  return res.json() as Promise<T>
}

export async function fetchPipelineStats(): Promise<PipelineStats> {
  return apiFetch<PipelineStats>('/api/pipeline/stats')
}

export async function fetchLeads(
  status?: LeadStatus | 'all',
  limit = 50
): Promise<Lead[]> {
  const params = new URLSearchParams()
  if (status && status !== 'all') params.set('status', status)
  params.set('limit', String(limit))
  return apiFetch<Lead[]>(`/api/leads?${params.toString()}`)
}

export async function fetchLeadDetail(id: string): Promise<LeadDetail> {
  return apiFetch<LeadDetail>(`/api/leads/${id}`)
}

export async function markLeadWon(id: string, payload: MarkWonPayload): Promise<void> {
  await apiFetch(`/api/leads/${id}/mark-won`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function markLeadDead(id: string): Promise<void> {
  await apiFetch(`/api/leads/${id}/mark-dead`, {
    method: 'POST',
  })
}

export async function fetchClients(): Promise<Client[]> {
  return apiFetch<Client[]>('/api/clients')
}

export async function fetchHealth(): Promise<HealthStatus> {
  return apiFetch<HealthStatus>('/health')
}

export const checkHealth = fetchHealth
export const fetchLead = fetchLeadDetail
export const markWon = markLeadWon
export const markDead = markLeadDead
