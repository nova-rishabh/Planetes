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
| Render (API) | `ALLOWED_ORIGINS` | Comma-separated site origins: `https://planetes.xyz` plus the Vercel default URL. Unset = no cross-origin access |
| Render (API) | `PYTHON_VERSION` | `3.11.9` (from `render.yaml`) |
| Render (API) | `MAX_FRAMES`, `IRSA_CONCURRENCY`, `CACHE_DIR` | `60`, `8`, `/tmp/planetes-cache` (from `render.yaml`; read by the API from D1.2 on) |
| Render (API) | `GIT_COMMIT` (optional) | Overrides `RENDER_GIT_COMMIT` for `code_version` |

Secrets go only in the Vercel/Render dashboards, never in the repo.

## Custom domain (planetes.xyz)

1. Vercel → project → Settings → Domains → add `planetes.xyz` (and `www.planetes.xyz`, redirected to the apex).
2. At the domain registrar, create exactly the DNS records Vercel shows (usually an `A` record for the apex and a `CNAME` for `www`). Remove any old `A`/`AAAA`/`CNAME` records for those names.
3. Wait until Vercel shows "Valid Configuration" and has issued the certificate. Check `https://planetes.xyz` in incognito.
4. Add `https://planetes.xyz` to `ALLOWED_ORIGINS` on Render, then redeploy the API.
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
