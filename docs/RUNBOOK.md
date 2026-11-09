# Runbook

Nov 8, 2026 · Owner: Rishabh · How to run, deploy and recover Planetes. Full local commands are in the README.

## Local setup

Needs Python 3.11, Node 22 (`web/.nvmrc`) and GNU Make. From the repo root:

```bash
python3.11 -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e "pipeline[dev]" -r api/requirements.txt
ALLOWED_ORIGINS=http://localhost:3000 uvicorn api.main:app --reload --port 8000
cd web && cp .env.example .env.local && npm ci && npm run dev   # http://localhost:3000
```

Checks before a PR: `pytest -q -m "not network"` (in `pipeline/`), `ruff check pipeline api contracts`, and in `web/` `npm run lint && npm run typecheck && npm run test && npm run build`.

## Make targets

| Target | Does |
|---|---|
| `make contracts` | Regenerates `pipeline/src/planetes/contracts.py` and `web/src/types/contracts.ts` from `contracts/*.schema.json` (needs `npm ci` in `web/`). CI fails if they are stale |
| `make validate` | Validates every JSON file in `web/public/data` against its schema |

## Deploy flow

Push (or merge a PR) to `main` → CI runs → **Vercel** builds `web/` (static export) and **Render** builds the API from `render.yaml` (`autoDeploy: true`). Every PR also gets a Vercel preview link. After a deploy, open `/api/health` on Render and the site, and check the status badge reads "NASA archive: ok".

## Environment variables

| Service | Variable | Value |
|---|---|---|
| Vercel (web) | `NEXT_PUBLIC_API_BASE` | Render API URL, no trailing slash. Baked in at build time, so redeploy after changing it |
| Render (API) | `ALLOWED_ORIGINS` | Comma-separated site origins: `https://planetes.divergit.com` plus the Vercel default URL. Unset = no cross-origin access |
| Render (API) | `PYTHON_VERSION` | `3.11.9` (from `render.yaml`) |
| Render (API) | `MAX_FRAMES`, `IRSA_CONCURRENCY`, `CACHE_DIR` | `60`, `8`, `/tmp/planetes-cache` (from `render.yaml`; read by the API from D1.2 on) |
| Render (API) | `JOB_WORKERS` | `2`: jobs that run at the same time; more wait in the queue (each client may have 3 unfinished jobs) |
| Render (API) | `GIT_COMMIT` (optional) | Overrides `RENDER_GIT_COMMIT` for `code_version` |
| Render (API) | `GCS_BUCKET` | `planetes-cache` |
| Render (API) | `GCP_SERVICE_ACCOUNT_JSON` | Full JSON key of the cache service account. Secret: dashboard only |

Secrets go only in the Vercel/Render dashboards, never in the repo.

## Google Cloud Storage cache (one-time)

**Done Nov 9** in project `planetes-514208`: bucket `gs://planetes-cache` (us-west1, uniform access, public access prevented, soft delete off, 30-day delete rule), service account `planetes-cache-writer` with Storage Object Admin on the bucket only, budget ₹1,800 (≈ $20; the billing account is in INR) with alerts at 50/90/100 %. Steps below are for redoing it.


1. console.cloud.google.com → create or pick the Planetes project; Billing shows the $300 trial credit.
2. Cloud Storage → Buckets → Create: name `planetes-cache`, Region `us-west1` (Oregon, same as Render), class Standard, uniform access, public access prevention on.
3. Bucket → Lifecycle → Add rule → Delete object, Age 30 days.
4. IAM & Admin → Service Accounts → Create `planetes-cache-writer`. Grant **no** project roles.
5. Bucket → Permissions → Grant access → that service account → role **Storage Object Admin** (this bucket only).
6. Service account → Keys → Add key → JSON. Paste it into Render as `GCP_SERVICE_ACCOUNT_JSON`, set `GCS_BUCKET=planetes-cache`, then delete the downloaded file.
7. Billing → Budgets & alerts → budget $20 for this project, email alerts at 50/90/100 %. (Alerts only; they don't stop spending.)

## Custom domain (planetes.divergit.com)

1. Vercel → project → Settings → Domains → add `planetes.divergit.com`.
2. In the DNS settings for divergit.com (wherever that domain is managed), add the record Vercel shows: usually `CNAME`, name `planetes`, value `cname.vercel-dns.com`. Don't touch the other divergit.com records.
3. Wait until Vercel shows "Valid Configuration" and has issued the certificate. Check `https://planetes.divergit.com` in incognito.
4. Add `https://planetes.divergit.com` to `ALLOWED_ORIGINS` on Render, then redeploy the API.
5. Record the URL in docs/STATUS.md.

## Rollback

- **Web:** Vercel → Deployments → pick the last good one → Promote to Production (instant, no rebuild).
- **API:** Render → service → Events → the last good deploy → Rollback.
- Then `git revert` the bad commit on `main` and push, so the next auto-deploy doesn't bring it back.

## If IRSA is down

1. Confirm: the badge reads "NASA archive: down/slow", or check `https://irsa.ipac.caltech.edu/TAP/availability`.
2. The baked benchmarks keep working; nothing in the demo depends on a live call.
3. Keep building on cached data and committed fixtures. Never swap in fake frames or numbers.
4. Post in the group with the time and what failed; retry later (retries already back off).
