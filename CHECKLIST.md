# Brightwick — What I Need From You

One page. Everything in order. Tick these off as you go.

---

## Stage 1 — Do this first (£0, but needs a card for identity check)

- [ ] **Sign up to Oracle Cloud** → https://www.oracle.com/cloud/free/
  - Choose home region: **UK South (London)**
  - Add a payment card — you will NOT be charged for Always Free resources
  - Card is for identity verification only
- [ ] **Follow `SETUP.md`** in this repo step by step
  - Gets you: cloud server → Docker → n8n running on your iPad
  - Estimated time: 45–60 minutes
  - Stop when you reach ✅ Checkpoint F (n8n login screen loads in Safari)
- [ ] **Tell me** when Checkpoint F is done (or where you got stuck)

---

## Stage 2 — Register & pay (before any data processing or outreach)

| ✓ | Item | Cost | Where |
|---|---|---|---|
| ☐ | **HMRC Sole Trader registration** | £0 | https://www.gov.uk/set-up-sole-trader |
| ☐ | **ICO Data Protection Fee** | ~£40/year by Direct Debit | https://ico.org.uk/registration — LEGALLY REQUIRED before processing any personal data |
| ☐ | **Domain: `brightwick.co.uk`** | ~£8/year | Namecheap or Porkbun — check it's available at checkout first |

> ⚠️ The ICO fee is not optional. You process names of company officers (scraped from Companies House). The fine for not registering is up to £4,000.

---

## Stage 3 — Free API keys (get these once your server is running)

Sign up for each, grab the key, drop it into your `.env` file on the server. All free.

| ✓ | Service | What for | Where |
|---|---|---|---|
| ☐ | **Companies House API key** | Finding UK Ltd/LLP leads | https://developer.company-information.service.gov.uk |
| ☐ | **Google AI Studio key** | Writing personalised emails (Gemini 2.5 Flash-Lite) | https://aistudio.google.com/apikey |
| ☐ | **Groq API key** | LLM fallback if Gemini hits rate limit | https://console.groq.com |
| ☐ | **Supabase project** | Remote database + dashboard data source | https://supabase.com → New project → free plan |
| | → Supabase items needed: | Project URL, Anon Key, Service Key | (all in Project Settings → API) |

---

## Stage 4 — Email setup (only when ready to start sending)

- [ ] **Cloudflare Email Routing** — forward `hello@brightwick.co.uk` to your personal Gmail (free, done after domain purchase)
- [ ] **Business mailbox for sending** — ~£5–6/month, only needed at go-live
  - Google Workspace: https://workspace.google.com (cheapest plan)
  - OR Microsoft 365 Business Basic: https://microsoft.com/en-gb/microsoft-365

> Nothing sends until this mailbox is configured. The pipeline queues emails silently until then — that's intentional.

---

## Stage 5 — Your personal details (needed in the config file)

These go into the `.env` file on your server. Required by PECR law in every email.

| Item | Example |
|---|---|
| Your full legal name | `Jane Smith` |
| Your UK postal address | `12 Example Lane, Leeds, LS1 1AA` |
| Trading name | `Brightwick` ✅ already decided |
| n8n username | (whatever you set in SETUP.md step F2) |
| n8n password | (whatever you set in SETUP.md step F2 — keep it safe) |

---

## Quick summary — what costs what and when

| Item | Cost | When |
|---|---|---|
| Oracle Cloud | £0 | Now |
| HMRC registration | £0 | Now |
| ICO fee | ~£40/yr | Before data processing |
| Domain | ~£8/yr | Before outreach |
| API keys (CH, Gemini, Groq, Supabase) | £0 | After server is running |
| Business mailbox | ~£5–6/mo | Only at go-live |

**Today's spend: £0.** First real cost is the ICO fee (~£40) before you process any data.

---

*Next step after Stage 1: tell me and I'll walk you through Stage 2 in detail.*
