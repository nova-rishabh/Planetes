# Decisions

One line each: date, decision, reason. Newest last. Source doc in brackets.

| Date | Decision | Reason |
|---|---|---|
| 2026-11-07 | "Two Opinions" (motion vs spectrum) is our differentiator [01] | None of the 10+ public repos for this challenge combines both into one cross-checked verdict |
| 2026-11-07 | Real data only; missing values are `null` with a reason [01, 03] | Validity is judged; one fake number undermines every real one |
| 2026-11-07 | No discovery claims; wording "consistent with" [04] | SPHEREx is not expected to see a classic Planet Nine; honest limits score better |
| 2026-11-07 | TAP over SIA for finding frames [02] | SIA lags ingestion by about a day; TAP is immediate |
| 2026-11-07 | Query QR3 first, fall back to QR2 [02] | Newest data first (consideration C1) without breaking when QR3 lacks a field |
| 2026-11-07 | Cutouts only, never full files [02] | Full files are about 70 MB each, 6 per pointing |
| 2026-11-07 | Bake the 5 benchmarks into `web/public/data` [02] | They must load instantly even if IRSA or the API is slow during judging |
| 2026-11-07 | Same code path for baked files and live API [03] | One thing to test; only the base URL differs |
| 2026-11-07 | No parallax claim from SPHEREx alone [04] | Parallax of the benchmarks is under 0.1 SPHEREx pixel |
| 2026-11-08 | Website on Vercel Hobby (free) [02] | Best Next.js host, global CDN, preview link per PR |
| 2026-11-08 | API on Render Starter, not Vercel functions [02] | Never sleeps; long jobs exceed Vercel function time limits |
| 2026-11-08 | JSON Schemas in `contracts/` generate pydantic and TS types [03] | One source of truth; CI catches drift |
| 2026-11-08 | Internal deadline Sun 15, 18:00 IST; cut order fixed in advance [05] | Leaves buffer before the official deadline; no arguing under pressure |
| 2026-11-08 | No AI attribution outside docs/AI_USAGE.md [AGENTS.md] | One honest disclosure place instead of noise in every commit |
| 2026-11-08 | IBM Plex superfamily; Space Grotesk dropped [09] | Space Grotesk is one of the most common AI-site fonts |
| 2026-11-08 | Light theme: printed-journal look, sky frames on a dark plate [09] | Dark space UIs look AI-generated |
| 2026-11-08 | Palette C "Plate Archive" is the default; team vote open [09] | Passes WCAG AA; neutral paper lets the frames and the accent stand out |
| 2026-11-08 | Custom domain planetes.divergit.com, Vercel URL as fallback [09, 02] | Another team named "Planetes" is on the same challenge; a direct link avoids mix-ups. planetes.xyz was not available |
| 2026-11-08 | Persistent cache in Google Cloud Storage (`planetes-cache`, asia-south1); Render's disk is wiped on deploy [02] | GCS over R2: team already has Google Cloud credit |
| 2026-11-08 | Camber for bakes and validation V4–V7 [02] | Keeps heavy batch work off the 512 MB API instance |
| 2026-11-09 | Camber: only Rishabh, on his Student Pack plan; validation runs on laptops [02] | Free; teammates need no extra account; bakes are Rishabh's (`bake.py`) |
| 2026-11-08 | Sentry student tier for monitoring (Should) [02] | See live errors during judging without digging through Render logs |
| 2026-11-09 | Palette C "Plate Archive" locked; A and B dropped [09] | Team vote; already in `web/src/styles/tokens.css`, so no UI change |
