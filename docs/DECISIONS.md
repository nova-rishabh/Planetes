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
| 2026-11-08 | Persistent cache in Google Cloud Storage (`planetes-cache`); Render's disk is wiped on deploy [02] | GCS over R2: team already has Google Cloud credit |
| 2026-11-09 | GCS bucket in `us-west1` (Oregon), not asia-south1 [02] | Same region as the Render API: faster reads, no cross-region transfer cost |
| 2026-11-08 | Camber for bakes and validation V4–V7 [02] | Keeps heavy batch work off the 512 MB API instance |
| 2026-11-09 | Camber dropped: bakes run in GitHub Actions (laptop as backup), validation on laptops [02] | The jobs are small; one less account and tool to learn; Actions is already set up and free |
| 2026-11-08 | Sentry student tier for monitoring (Should) [02] | See live errors during judging without digging through Render logs |
| 2026-11-09 | Palette C "Plate Archive" locked; A and B dropped [09] | Team vote; already in `web/src/styles/tokens.css`, so no UI change |
| 2026-11-09 | Aladin Lite loaded at runtime from jsDelivr, pinned 3.8.2, not bundled [02] | Keeps 2.4 MB of GPL/LGPL code out of our bundle; pinned so the API we checked doesn't change |
| 2026-11-09 | Sky map images from ESA ESASky, not CDS or IRSA [02] | CDS was down worldwide on Nov 9; IRSA's HiPS copies block browsers (no CORS); ESASky serves the same surveys with CORS |
| 2026-11-09 | Time-lapses use QR2 **and** QR3 frames; QR3 wins only for the same exposure [02] | Checked at Barnard's Star: the releases cover different weeks, so "QR3 only" would drop two-thirds of the frames |
| 2026-11-09 | Rishabh finished D2.2 review fixes in Tirth's files so G1 can ship; Tirth away until Wed [06] | G1 (Tue 23:00) needs live frames; the changes are listed in the PR and Tirth's commits are kept |
| 2026-11-12 | Cut D4.2 thermometer and D3.4 known asteroids; D4.5 Planet X check and D1.6 tour only Sat 10:00–18:00 if G3 is done; D2.5 kept [05, 06] | Tirth and Amish missed the Nov 12 call; Two Opinions for the 5 benchmarks (all stars/brown dwarfs) doesn't need asteroids |
| 2026-11-12 | Rishabh builds D4.1 spectrum layer and D4.3 typer, plus an interim aperture photometry in `photometry.py` (Tirth's PSF fit can replace it) [06] | Role 4 hasn't started; D2.4 not pushed; G3 Fri 23:00 needs spectra |
| 2026-11-12 | Nov 12 cuts reversed: D4.2 thermometer, D3.4 known asteroids, D4.5 + D1.6 Planet X check, D1.7 sonified blink, D3.5 mover search all back in scope; Rishabh/agent builds them one PR each [05, 06] | Rishabh: aim to win, cut nothing. Order: Planet X → known asteroids → thermometer → sonification → mover search. Stacks/difference (D2.3) and validation stay first priority |
