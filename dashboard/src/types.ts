export interface PipelineStats {
  new: number
  qualified: number
  personalised: number
  outreach: number
  hot: number
  won: number
  dead: number
}

export type LeadStatus = 'new' | 'qualified' | 'personalised' | 'outreach' | 'hot' | 'won' | 'dead'

export interface Lead {
  id: string
  company_name: string
  region: string
  sic_description: string
  score: number
  status: LeadStatus
  discovered_domain: string
  weakness_summary: string
  scraped_at: string
}

export interface OutreachEvent {
  id: string
  type: 'email_sent' | 'reply_received' | 'call_scheduled' | 'call_completed' | 'note'
  summary: string
  created_at: string
}

export interface GeneratedEmail {
  subject: string
  body_text: string
  generated_at: string
  llm_used: string
  variant: number
}

export interface Qualification {
  no_website: number
  no_ssl: number
  lighthouse_mobile: number | null
  last_modified_days: number | null
  no_social: number
  low_reviews: number
}

export interface LeadDetail extends Lead {
  emails: GeneratedEmail[]
  outreach_history: OutreachEvent[]
  qualification?: Qualification
  contact_name?: string
  contact_email?: string
  monthly_value_gbp?: number
}

export interface Client {
  id: string
  company_name: string
  contact_name: string
  won_at: string
  monthly_value_gbp: number
  site_url: string
}

export interface HealthStatus {
  status: 'ok' | 'error'
  version?: string
  uptime_seconds?: number
}

export interface MarkWonPayload {
  monthly_value_gbp: number
  contact_name: string
  contact_email: string
}
