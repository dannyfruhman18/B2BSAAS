# n8n Workflows

Import these JSON files into your n8n instance:
n8n Dashboard → Workflows → Import from file

| File | Purpose | Trigger |
|---|---|---|
| `01-scrape-qualify.json` | Scrape CH + qualify batch | Manual / daily 2am cron |
| `02-personalise.json` | Generate email copy via LLM | After qualify run |
| `03-outreach.json` | Send today's emails | Daily 8am cron |
| `04-reply-detection.json` | Poll inbox, flag hot leads | Every 15 min |
| `05-hot-lead-alert.json` | Notify owner when HOT | Webhook from reply detection |
| `06-weekly-digest.json` | Monday 9am email to owner | Monday 9am cron |

All workflows call the pipeline API (http://pipeline:8000/api/...) via HTTP Request nodes.
Set the `BRIGHTWICK_API_URL` credential in n8n to match your pipeline container address.
