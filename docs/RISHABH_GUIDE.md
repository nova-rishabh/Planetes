# Rishabh's setup guide

Nov 9, 2026 · Every account and tool only Rishabh can set up, in order. Tick each box when done and tell the agent so it can update STATUS.md. Secrets (keys, passwords) go only in the Render/Vercel dashboards, never in the repo or the group chat.

## 1. Today (needed for G1, Tue 23:00)

### Google Cloud Storage cache (15 min)
Bucket region: `us-west1` (Oregon), the same region as the Render API. The agent did the ticked steps with the gcloud CLI on Nov 9 (budget is ₹1,800 ≈ $20, since the billing account is in INR).
- [x] console.cloud.google.com → project dropdown → **New Project** `planetes` → select it. Billing shows the $300 trial credit.
- [x] ☰ Cloud Storage → Buckets → **+ Create**: name `planetes-cache`, Location type **Region** (as above), class **Standard**, access **Uniform**, keep **Enforce public access prevention** ticked → Create.
- [x] Bucket → **Lifecycle** → Add a rule → **Delete object**, Age **30** days.
- [x] ☰ IAM & Admin → Service Accounts → **+ Create**: `planetes-cache-writer` → **skip roles** → Done.
- [x] Bucket → **Permissions** → Grant access → paste the service account email → role **Storage Object Admin** → Save.
- [ ] Service account → **Keys** → Add key → JSON. Render → `planetes-api` → Environment: paste the whole file as `GCP_SERVICE_ACCOUNT_JSON`, keep `GCS_BUCKET=planetes-cache` → Save. **Delete the downloaded file.**
- [x] ☰ Billing → Budgets & alerts → **Create budget**: project `planetes`, $20, alerts at 50/90/100 %.
- [ ] Check: Render → Logs shows `Cache: local /tmp/planetes-cache + GCS bucket planetes-cache`.

### Custom domain planetes.divergit.com (10 min + DNS wait)
- [ ] Vercel → `web` project → Settings → Domains → Add `planetes.divergit.com`.
- [ ] At the DNS host of divergit.com add exactly what Vercel shows (usually CNAME `planetes` → `cname.vercel-dns.com`; on Cloudflare set **DNS only**). Touch nothing else.
- [ ] Vercel shows **Valid Configuration**; the site opens in incognito.
- [ ] Render → Environment → `ALLOWED_ORIGINS` = `https://planetes.divergit.com,https://web-gamma-flame-16.vercel.app` → Save.

### GitHub: reviewing teammates' pull requests
- [ ] Repo → **Pull requests** → open one → **Files changed**. The agent reviews each PR when you say "review PR #n" and drafts your comment.
- [ ] Merge only when CI is green and the PR shows a real-data screenshot.
- [ ] Add teammates as collaborators: repo → Settings → **Collaborators** → **Add people** → their GitHub username → role **Write**. Tirth is `t-valand`; ask the others for theirs. They accept the email invite. (Without it, PRs come from forks and you must click **Approve and run workflows** before CI runs.)
- [ ] Protect `main`: Settings → **Rules → Rulesets → New branch ruleset** → target `main` → tick **Require a pull request before merging** and **Require status checks to pass** (pick the CI jobs) → Create. Teammates then work on branches and open PRs; nobody pushes straight to `main`.

## 2. Space Apps team page
- [ ] Send Tirth the private message (PM_PLAYBOOK §8): turn on joining, approve requests, make you Team Owner.
- [ ] Once owner: change "starry discoveries" in the About text (no discovery claims).
- [ ] Nov 13: read the Resources tab and Submission/Judging guides; tell the agent what they say.

## 3. Later (Should, from Thu)
- [ ] Sentry: free account at sentry.io, one project for the API and one for the web; DSNs go into Render/Vercel env vars (the agent adds the code).

## No account needed
IRSA/SPHEREx data, SIMBAD, Gaia, VizieR and JPL are public. Teammates need only GitHub, Python 3.11 and their AI tool.
