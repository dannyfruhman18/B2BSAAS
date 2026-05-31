# Final Plan — UK Lead Gen & Agency Fulfilment System

This is the agreed blueprint, updated with the 2026 verification findings
(`FINDINGS.md`). It supersedes the original brief where they differ. Written for
a complete beginner: technical terms are defined on first use.

---

## 0. The honest summary (read this once)

- **What's genuinely £0:** finding leads (Companies House), scoring them,
  writing personalised emails (Gemini/Groq free tiers), the dashboard, reply
  detection (for replies into a free forwarded inbox), and all client-fulfilment
  templates.
- **What costs money:** the **domain** (~£8/year), the **ICO data protection
  fee** (~£40/year, legally required — see §5), and — only when you go live with
  real sending — a **business mailbox (~£5–6/month)**. Nothing else.
- **What we will NOT do:** route cold email through Brevo/SendGrid/etc. (their
  TOS bans it), build SMS or AI voice (no free path — deferred, §8), or pretend
  any paid thing is free.

---

## 1. Who this serves & the legal target pool (compliance first)

UK **PECR** (Privacy and Electronic Communications Regulations) is the binding
constraint. *PECR = the UK law governing electronic marketing.*

- **Legal to cold-email without prior consent:** "corporate subscribers" =
  **limited companies, LLPs, Scottish partnerships, public bodies.** You must
  identify yourself and offer opt-out. **This is the only pool we target.**
- **Excluded entirely from cold email:** sole traders and English/Welsh/NI
  partnerships (treated as individuals under PECR — need consent/soft opt-in).
- **The only reliable filter:** every scraped business is cross-checked against
  the **Companies House API**. A real "limited company" or "LLP" status is the
  *only* signal that a lead is legal to email. A professional-looking address
  like `info@smithsplumbing.co.uk` proves nothing — Smith's Plumbing may be a
  sole trader. **No Companies House match → drop the lead, never email it.**
- **Every email must contain:** real sender name, trading name, a real postal
  address, and a one-click opt-out ("Reply STOP and I won't email you again").
- **Phone (if ever enabled):** screen against TPS *and* CTPS. Build the schema,
  don't implement until voice is funded (§8).

---

## 2. Identity & trading name

You'll register as a **sole trader** (the simplest UK business structure: you
*are* the business, declared via HMRC Self Assessment) under a **trading name**
(a brand you trade as, while invoices/legal use your real name).

**Five trading-name options** (all to be checked for `.co.uk` availability at
Namecheap/Porkbun before you commit — I'll do that once you shortlist):

1. **Highstreet Studio** — speaks directly to local UK SMEs; says who you serve.
2. **Kerbside Digital** — grounded, local, British spelling; approachable.
3. **Brightwick** — invented, warm, distinctly British "-wick" suffix; brandable.
4. **Foxglove Digital** — a native wildflower; memorable, friendly, non-techy.
5. **Gable Digital** — "gable" = rooftops/buildings; evokes solid local trades.

---

## 3. Tech stack (all verified — see FINDINGS.md)

| Layer | Choice | Notes |
|---|---|---|
| Host | Oracle Cloud Always Free ARM A1 (4 OCPU/24 GB/200 GB) | Region: London, fallback Frankfurt |
| Orchestration | self-hosted **n8n** via Docker Compose (ARM image) | *n8n = a visual workflow automation tool; Docker = software-in-a-box* |
| Database | **SQLite** on the VM (local file DB) + **Supabase** free (500 MB) as remote mirror | Dashboard reads Supabase |
| LLM primary | **Gemini 2.5 Flash-Lite** (free, no card) | retry/backoff; confirm live RPD |
| LLM fallback | **Groq `llama-3.1-8b-instant`** (14,400 req/day free) | |
| Lead source | **Companies House API** (free, mandatory primary) + OpenStreetMap Overpass enrichment | |
| Website audit | Lighthouse CLI + HTTP probes (SSL, last-modified, viewport) | |
| Email — receive | **Cloudflare Email Routing** (free) forwards `you@domain.co.uk` → your phone inbox | reply detection reads this |
| Email — send | **Pluggable. £0 to build; ~£5–6/mo mailbox at go-live.** See §4 | NOT Brevo |
| Client site hosting | **Cloudflare Pages** (free, static) | `clientname.pages.dev` |
| Client email mktg | **MailerLite** free (500 subs / 12k emails/mo) | |
| Your dashboard | React + Tailwind on Cloudflare Pages, reads Supabase | mobile-first |
| Domain | Namecheap or Porkbun `.co.uk` (~£8/yr) | |

---

## 4. The email-sending decision (your call — §4 of the brief, corrected)

Because **no free service permits cold email**, choose how to handle the *send*:

- **Option A — Build to £0, pay only at go-live (recommended).** Build stages
  1–3 + dashboard + fulfilment now for £0. The pipeline personalises and
  **queues** emails. When you're actually ready to send, add **one Google
  Workspace / Microsoft 365 mailbox (~£5–6/mo)** — fully compliant for genuine
  B2B mail, perfect at 5–30/day. No spend until you flip the switch.
- **Option B — Pay ~£5/mo now**, so live sending is available from day one.
- **Option C — Brevo anyway.** Technically works at 300/day but **violates their
  TOS**; account can be suspended without notice, killing deliverability. Not
  recommended; included only for honesty.

The sender is a single swappable module either way, so this decision can change
later without rework.

---

## 5. Money & legal admin to expect (flagged, not hidden)

| Item | Cost | When | Notes |
|---|---|---|---|
| `.co.uk` domain | ~£8/year | Before outreach | Card needed; I'll confirm before any purchase |
| **ICO data protection fee** | **~£40/year by Direct Debit** | Before processing personal data | **Legally required** — you process named employees' data. Non-negotiable. |
| Sole trader registration | £0 | Before trading/earning | HMRC Self Assessment |
| Business mailbox (Option A/B) | ~£5–6/month | At go-live only | Skippable until you send |

Nothing here bills without me telling you first and you confirming.

---

## 6. Architecture — the 5-stage pipeline

```
[1 SCRAPE]   Companies House (active Ltd/LLP only) + OSM enrichment
     ↓
[2 QUALIFY]  Lighthouse + HTTP probes → 0–100 score + weakness summary
     ↓
[3 PERSONALISE]  Gemini 2.5 Flash-Lite → subject + 80-word email + 2 follow-ups
     ↓
[4 OUTREACH]  queue → send (pluggable) → reply detection (IMAP on forwarded inbox)
     ↓                                          ↓
  (no reply)                              (reply detected)
  Day 4 follow-up, Day 9 final            flag HOT → notify you → you close
  Day 10 mark cold                                ↓
                                          [5 FULFIL] site, ads, SEO, social, onboarding
```

### Stage 1 — Scrape
Input: configurable **SIC codes** (*Standard Industrial Classification = UK
industry category codes*) + UK regions. Pull active companies from Companies
House; enrich address/category via OpenStreetMap. Store in SQLite + Supabase:
company number, name, registered address, SIC, incorporation date, officer names
(for personalisation), discovered domain. Domain discovery: try
`companyname.co.uk`/`.com`, confirm with a HEAD request. Throttle to ≤600 req/5min.

### Stage 2 — Qualify (0–100 weakness score)
No discoverable website **+40** · No SSL **+15** · Lighthouse mobile <50 **+20** ·
Last-modified >2 yrs **+10** · No Facebook/Instagram **+10** · <10 Google reviews
**+5**. Store a one-line `weakness_summary` for the LLM.

### Stage 3 — Personalise
Per lead, generate subject + ~80-word email + 2 follow-up variants. Must
reference the specific weakness found **and** a local detail (region, company
age, sector). Tone adapts by sector (warmer for hospitality, direct for trades,
formal for professional services). Always includes trading name, postal address,
opt-out line.

### Stage 4 — Outreach
Day 0 initial · Day 4 follow-up (different angle) · Day 9 final · Day 10 mark
cold, never contact again. Reply detection: poll the forwarded inbox every
15 min; any reply pauses the sequence and flags **HOT**. Bounce guard: 3+ hard
bounces in a day → pause sending, alert you. **Manual warm-up cadence:** week 1
= 5/day, week 2 = 15/day, week 3 = 30/day (no fake "warmup network" — honest
about that limitation).

### Stage 5 — Fulfil (after you mark a lead "won")
Website via `frontend-design` skill → deploy to Cloudflare Pages · Google/Meta
ad copy as CSV · SEO pack (title tags, meta, schema.org JSON-LD, 5-article brief)
· 30-post social calendar in a Google Sheet · onboarding sequence in MailerLite ·
auto-generated handover PDF.

---

## 7. Dashboard (mobile-first — you're on iPad/iPhone)

Pipeline view by stage · Hot-leads tab (needs your call) · Active-clients tab ·
This-week's stats · "Mark won"/"Mark dead" buttons · Monday 9am weekly digest
email. React + Tailwind on Cloudflare Pages, reading Supabase.

---

## 8. Deferred — be loud about this

- **SMS:** every UK SMS API is paid; Twilio trial only texts verified numbers.
  Build the DB schema, do **not** implement until there's revenue.
- **AI voice:** Vapi/Bland are trial-credit only; Twilio per-minute cost applies
  regardless. **No ongoing free tier exists.** Deferred, not quietly included.

---

## 9. Build order — stop after each, you test, then we continue

1. **`SETUP.md`** — Oracle Cloud signup → ARM VM → Docker → n8n. (Built after
   your §2/§4 decisions; doesn't depend on them, so it can start immediately.)
2. Sole-trader registration (HMRC) + ICO fee + pick the trading name.
3. Domain purchase + DNS (SPF/DKIM/DMARC) + email receive (Cloudflare Routing)
   + send-mailbox setup per §4 choice.
4. Companies House integration — scrape one SIC code in one region; show data.
5. Qualifier — score the pilot batch; show top 20.
6. Personaliser — 5 sample emails; you review tone before anything sends.
7. Sender + manual warm-up schedule (5 → 15 → 30/day).
8. Reply detection + hot-lead alerts.
9. Dashboard v1.
10. Fulfilment templates.
11. SMS + voice — deferred until paying clients exist.

---

## 10. Decisions made (31 May 2026)

1. **Trading name → Brightwick.** (`brightwick.co.uk` doesn't currently resolve —
   a weak positive signal; confirm availability at registrar checkout. Fallbacks:
   `brightwickdigital.co.uk`, `brightwick.studio`.)
2. **Pilot sector + region → deferred.** Kept open; we choose at the scrape stage
   (build order step 4). Aim for a limited-company-heavy sector then.
3. **Email approach → Option A** (build to £0; add a ~£5–6/mo mailbox only at
   go-live; the sender stays a swappable module).

`SETUP.md` (Phase 1) is written and ready to follow.
