# Rishabh's setup guide

Nov 9, 2026 · Every account and tool only Rishabh can set up, in order. Tick each box when done and tell the agent so it can update STATUS.md. Secrets (keys, passwords) go only in the Render/Vercel dashboards, never in the repo or the group chat.

## 1. Today (needed for G1, Tue 23:00)

### Google Cloud Storage cache (15 min)
First check Render → `planetes-api` → Settings → **Region**. Singapore → bucket region `asia-south1`. Oregon → `us-west1`.
- [ ] console.cloud.google.com → project dropdown → **New Project** `planetes` → select it. Billing shows the $300 trial credit.
- [ ] ☰ Cloud Storage → Buckets → **+ Create**: name `planetes-cache`, Location type **Region** (as above), class **Standard**, access **Uniform**, keep **Enforce public access prevention** ticked → Create.
- [ ] Bucket → **Lifecycle** → Add a rule → **Delete object**, Age **30** days.
- [ ] ☰ IAM & Admin → Service Accounts → **+ Create**: `planetes-cache-writer` → **skip roles** → Done.
- [ ] Bucket → **Permissions** → Grant access → paste the service account email → role **Storage Object Admin** → Save.
- [ ] Service account → **Keys** → Add key → JSON. Render → `planetes-api` → Environment: paste the whole file as `GCP_SERVICE_ACCOUNT_JSON`, keep `GCS_BUCKET=planetes-cache` → Save. **Delete the downloaded file.**
- [ ] ☰ Billing → Budgets & alerts → **Create budget**: project `planetes`, $20, alerts at 50/90/100 %.
- [ ] Check: Render → Logs shows `Cache: local /tmp/planetes-cache + GCS bucket planetes-cache`.

### Custom domain planetes.divergit.com (10 min + DNS wait)
- [ ] Vercel → `web` project → Settings → Domains → Add `planetes.divergit.com`.
- [ ] At the DNS host of divergit.com add exactly what Vercel shows (usually CNAME `planetes` → `cname.vercel-dns.com`; on Cloudflare set **DNS only**). Touch nothing else.
- [ ] Vercel shows **Valid Configuration**; the site opens in incognito.
- [ ] Render → Environment → `ALLOWED_ORIGINS` = `https://planetes.divergit.com,https://web-gamma-flame-16.vercel.app` → Save.

### GitHub: reviewing teammates' pull requests
- [ ] Repo → **Pull requests** → open one → **Files changed**. The agent reviews each PR when you say "review PR #n" and drafts your comment.
- [ ] Merge only when CI is green and the PR shows a real-data screenshot. Teammates working from a fork (Tirth: `t-valand/Planetes`) is fine.
- [ ] Optional: Settings → Branches → add rule for `main` → **Require a pull request** + **Require status checks (CI)**, so nothing lands unchecked.

## 2. Space Apps team page
- [ ] Send Tirth the private message (PM_PLAYBOOK §8): turn on joining, approve requests, make you Team Owner.
- [ ] Once owner: change "starry discoveries" in the About text (no discovery claims).
- [ ] Nov 13: read the Resources tab and Submission/Judging guides; tell the agent what they say.

## 3. Camber (not urgent; needed from Thu for bakes and validation V4–V7)
Facts from docs.cambercloud.com (checked Nov 9): every user gets **100 free credits** on sign-up (1 credit = $1). A small CPU node (XXSMALL, 4 cores, 16 GB) costs 0.16 credits/hour, so the free credits cover our bakes many times. Team Leaders add members by email on the Team page, but the docs don't say whether members share the credits; creating a team goes through info@cambercloud.com.
- [ ] Sign up at app.cambercloud.com (Sign Up, top right).
- [ ] Decide: **each teammate signs up with their own free credits** (agent's recommendation: no shared account or money needed), or you ask info@cambercloud.com for a team.
- [ ] Tell the agent; it closes the docs/02 [VERIFY] and writes the bake job steps.

## 4. Later (Should, from Thu)
- [ ] Sentry: free account at sentry.io, one project for the API and one for the web; DSNs go into Render/Vercel env vars (the agent adds the code).

## No account needed
IRSA/SPHEREx data, SIMBAD, Gaia, VizieR and JPL are public. Teammates need only GitHub, Python 3.11 and their AI tool.
