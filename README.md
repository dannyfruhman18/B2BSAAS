# UK Lead Gen & Agency Fulfilment System

An autonomous system that finds UK limited companies and LLPs with weak online
presence, personalises compliant cold outreach, hands warm leads to the owner
for the sales call, and (after conversion) auto-generates the client's website,
ad copy, SEO pack, social calendar, and onboarding emails.

**Owner:** UK sole trader (trading name to be chosen — see `PLAN.md` §2).
**Budget:** £0/month ongoing, beyond a ~£8/year `.co.uk` domain and the mandatory
ICO data protection fee (~£40/year). Any change to that is flagged loudly.

---

## ⚠️ Read this first — what verification changed

Before building, the "free tier" claims in the original brief were re-verified
(2026). Full report with sources: **`FINDINGS.md`**. The headlines:

| Thing | Original assumption | Reality (2026) | Impact |
|---|---|---|---|
| LLM (primary) | Gemini **2.0** Flash free | **2.0 Flash retired 3 Mar 2026.** Use Gemini **2.5 Flash‑Lite** (free tier still exists) | Swap model. No cost change. |
| Email sending | Brevo free = cold-email SMTP | **Brevo's TOS prohibits cold email.** *No* free provider permits cold outreach. | **Strategy change — see below.** |
| Client email mktg | MailerLite free 1,000 subs | Free tier **halved to 500 subs** / 12k emails per month (Sep 2025) | Smaller, still usable. |
| Host | Oracle Always Free A1 | ✅ Still available; capacity tight — pick a EU/UK region | Fine. |
| Groq fallback | Free tier | ✅ `llama-3.1-8b-instant` = 14,400 req/day free | Fine. |
| Companies House | Free key | ✅ 600 requests / 5 min | Fine. |

### The one that matters: cold email cannot be done well for £0/month

PECR **legally** lets you cold-email UK limited companies & LLPs. But **no free
email service's Terms of Service permit cold outreach** — Brevo, SendGrid,
Resend, MailerLite all ban it and will suspend accounts that do it. This is a
business-model constraint, not a bug.

**What this means in practice:**
- Everything *except the actual sending* — scraping, qualifying, personalising,
  the dashboard, and all fulfilment — is genuinely **£0**.
- Sending compliant cold email properly needs a real business mailbox
  (Google Workspace / Microsoft 365, **~£5–6/month**) once you're ready to send
  for real. At warm-up volumes (5 → 15 → 30/day) one mailbox is perfect and
  fully compliant.
- The system is built so the **send step is a pluggable module**: you can build
  and prove the entire pipeline for £0, then plug in the paid mailbox only when
  you're about to do live outreach. No spend until then.

See `PLAN.md` §4 for the three options and the recommendation.

---

## Status

- [x] Skills read, free-tier claims re-verified (`FINDINGS.md`)
- [x] Refined final plan written (`PLAN.md`)
- [x] **Decisions made:** trading name = **Brightwick** · email = **Option A**
      (build to £0, add mailbox at go-live) · pilot sector/region = **deferred**
      to the scrape stage (kept open)
- [x] `SETUP.md` — Oracle Cloud → Docker → n8n (Phase 1) — **ready for you to follow**
- [ ] You complete Phase 1 (reach Checkpoint F in `SETUP.md`)
- [ ] Phase 2: sole-trader reg + ICO fee + domain + Companies House
- [ ] Build stages 1–5 (one at a time, stop-and-test after each)

## Repo layout

```
README.md     ← you are here: status + the £0 reality check
PLAN.md       ← the final plan: architecture, compliance, build order
FINDINGS.md   ← free-tier verification report with sources
SETUP.md      ← step-by-step setup for a beginner (built after your decisions)
```
