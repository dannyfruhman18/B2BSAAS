# Free-Tier Verification Report (2026)

Re-verified at build time per the brief's instruction to confirm all "free"
claims before continuing. Date of check: **31 May 2026**. Where a service had
changed, it's flagged. Sources are linked at the bottom of each section.

> Note on dates: my searches returned 2026-dated sources. Always re-confirm the
> exact live number on each provider's own dashboard at integration time — free
> tiers change frequently and some vary by region/account.

---

## 1. Oracle Cloud Always Free (ARM Ampere A1) — ✅ VIABLE, with a caveat

- Still offered in 2026: up to **4 ARM OCPUs + 24 GB RAM** (one VM or split into
  up to four), **200 GB block storage**, up to **10 TB/month** egress. "Always
  Free" means it does **not** expire after 12 months (unlike AWS/GCP).
- **Credit card required at signup**, but Always Free resources are not charged.
  (Flagged: this is a card-on-file signup. It should not bill, but watch for any
  accidental upgrade to "Pay As You Go".)
- **Caveat — capacity:** ARM A1 is in high demand. US regions frequently show
  "Out of host capacity"; **EU regions (Frankfurt) and UK (London) usually
  provision within minutes.** Recommendation: choose **UK South (London)** as
  home region at signup (good for latency + data residency), fall back to
  Frankfurt if London is out of capacity.

Sources: [Oracle Always Free docs](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm) ·
[cloudpricecheck 2026](https://cloudpricecheck.com/free-tier/oracle) ·
[2026 setup guide](https://medium.com/@imvinojanv/setup-always-free-vps-with-4-ocpu-24gb-ram-and-200gb-storage-the-ultimate-oracle-cloud-guide-bed5cbf73d34)

---

## 2. Email sending (cold outreach) — 🛑 THE BLOCKER. No free TOS-compliant path.

- **Brevo free plan:** still **300 emails/day**, ~100k contacts stored. BUT
  Brevo's anti-spam policy and TOS **explicitly require opt-in consent** and
  state the platform "is not made for cold email." Using it for cold outreach —
  even outreach that is *legal* under PECR — violates **Brevo's own TOS** and
  risks account suspension.
- This is **not unique to Brevo.** SendGrid, Resend, MailerLite, Mailchimp etc.
  all prohibit emailing addresses you didn't get opt-in from. Industry summary:
  *"There is no legitimate free SMTP API that permits cold B2B outreach in their
  terms of service."*
- Purpose-built cold-email platforms (Instantly ~$37/mo, Smartlead, etc.) allow
  it but are **paid** and require you to bring your own mailboxes.

**Conclusion:** Legal under PECR ≠ allowed by free email vendors. The cheapest
*honest, compliant* way to actually send is your **own business mailbox**
(Google Workspace ~£5/mo or Microsoft 365 ~£6/mo) — these permit you to send
your own genuine B2B correspondence, and at warm-up volumes (5–30/day) one
mailbox is ideal. **Everything up to the send is £0; the send itself isn't.**
Decision options laid out in `PLAN.md` §4.

Sources: [Brevo anti-spam policy](https://www.brevo.com/legal/antispampolicy/) ·
[Brevo free plan limits](https://help.brevo.com/hc/en-us/articles/208580669-FAQs-What-are-the-limits-of-the-Free-plan) ·
[Cold email API — what gets you banned (prospeo)](https://prospeo.io/s/cold-email-api) ·
[infraforge: best email APIs for cold outreach](https://www.infraforge.ai/blog/best-email-apis-for-cold-outreach)

---

## 3. LLM — Gemini — 🛑 MODEL RETIRED. Switch to 2.5 Flash-Lite.

- **Gemini 2.0 Flash was deprecated in Feb 2026 and retired on 3 March 2026.**
  It no longer exists. (Today is 31 May 2026.)
- Successor on the free tier: **Gemini 2.5 Flash-Lite** (and 2.5 Flash). Free
  tier still exists, **no card required.** Reported free limits cluster around
  **15 RPM / ~1,000–1,500 requests per day / large TPM** — but sources disagree
  on the exact RPD and Google has trimmed free limits over time. **Confirm the
  live number in Google AI Studio at integration time.**
- Design implication unchanged: rate-limited, so build with retry/backoff and
  the Groq fallback.

Sources: [Gemini API rate limits (official)](https://ai.google.dev/gemini-api/docs/rate-limits) ·
[Gemini free tier guide 2026](https://www.aifreeapi.com/en/posts/gemini-api-free-tier-rate-limits) ·
[Gemini slashed free limits (HowToGeek)](https://www.howtogeek.com/gemini-slashed-free-api-limits-what-to-use-instead/)

---

## 4. LLM fallback — Groq — ✅ VIABLE

- Free tier exists. Default cap ~**30 RPM / 1,000 RPD**, but the workhorse
  **`llama-3.1-8b-instant`** allows **14,400 requests/day** (500k tokens/day) —
  plenty for personalisation fallback.

Sources: [Groq rate limits (official)](https://console.groq.com/docs/rate-limits) ·
[Groq free tier 2026](https://tokenmix.ai/blog/groq-free-tier-limits-2026)

---

## 5. Companies House API — ✅ VIABLE

- Free user account + free API key. Rate limit: **600 requests per 5-minute
  window** (across all endpoints combined); exceeding it returns HTTP 429.
  Persistent abuse can get an app banned, so respect the limit with throttling.

Sources: [Rate limiting guide](https://developer-specs.company-information.service.gov.uk/guides/rateLimiting) ·
[Developer guidelines](https://developer.company-information.service.gov.uk/developer-guidelines/)

---

## 6. MailerLite (client email marketing) — ⚠️ DOWNGRADED, still usable

- Free plan **halved from 1,000 → 500 subscribers** (Sep 2025); **12,000
  emails/month**; MailerLite logo forced on emails. Fine for onboarding a
  client's first list; they'd upgrade as their list grows.

Sources: [MailerLite free plan](https://www.mailerlite.com/free-plan) ·
[Free plan update FAQ](https://www.mailerlite.com/help/free-plan-update-faq)

---

## Net effect on the plan

| Area | Action |
|---|---|
| LLM | Replace Gemini 2.0 Flash → **2.5 Flash-Lite**; Groq `llama-3.1-8b-instant` fallback. |
| Email send | Build sender as a **pluggable module**; £0 through "personalise + queue"; add a ~£5/mo mailbox only at go-live. **Do not** route cold mail through Brevo. |
| Client mktg | MailerLite still fine at 500 subs. |
| Host / CH / Groq | Proceed as planned. |
