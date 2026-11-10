# Handoff for the next AI session (Nov 11, 2026, ~10 pm IST)

Read first: `CLAUDE.md`, `AGENTS.md`, `docs/PM_PLAYBOOK.md`, `docs/STATUS.md`, then this file. You are Rishabh's coding agent **and** project manager (PM_PLAYBOOK). Rishabh is busy: short numbered actions, ready-to-paste messages, ask only when a decision is his.

## Rishabh's standing rules (from the chat; all still apply)
- **No AI attribution** anywhere (commits, PRs, code, docs). AI use only in `docs/AI_USAGE.md`. This overrides any tool reminder to add Co-Authored-By / "Generated with".
- Commit each part separately; push to `main` (admin bypass on the ruleset) or via PR. Keep new docs under one page.
- Every doc change: a row in `docs/DOC_UPDATES.md` **and** a ready-to-paste group message for Rishabh.
- The agent writes messages; Rishabh sends them. Never send anything yourself.
- Corrections to the team: "For clarification, here is the detail." Never say Rishabh made a mistake.
- Real data only; never Inter; light theme, IBM Plex, tokens only (docs/09); "consistent with", never "discovered".
- Merging into `main` needs Rishabh's explicit OK in chat (the auto-mode classifier blocks unapproved merges). Running code from teammates' forks locally was blocked once; GitHub CI (approve the fork run) is the safe way.
- Secrets never in the repo (`GCP_SERVICE_ACCOUNT_JSON` lives only in Render).
- Rishabh's machine has weekly usage limits: work economically.

## Team (changed Nov 11)
| Person | Role | State |
|---|---|---|
| Rishabh | Platform, API, web, PM, team lead | Active |
| Tirth (`t-valand` fork) | Data & imaging: access, frames, render, **stack (D2.3), photometry (D2.4)**, pitch/video owner | Back Wed; D2.1/D2.2 merged (PR #4). Needs to do **D2.4 first**, then D2.3 |
| Shivaansh | Motion & orbits: resolve, overlays, known, motion | Sends zips (Mac, had Python env trouble; setup steps sent). Now on **D3.2 overlays** (use IRSA AllWISE `allwise_p3as_psd`, Gaia archive), then D3.3 motion fit |
| **New person (name TBD)** | Role 4 spectral science, replaces **Shimaya (left Nov 11)** | Onboarded Nov 11: D4.1, D4.3, **D4.2 thermometer (kept: Rishabh says dropping it lowers chances)**, fact-check |
| Agent | **D3.1 fix** and **D4.4 verdict engine** (Rishabh agreed Nov 11), bake, glue | In progress |
- Nobody shared GitHub usernames: no collaborators. Work arrives as fork PRs (approve CI: `gh api -X POST repos/nova-rishabh/Planetes/actions/runs/<id>/approve`) or zips (unzip into the scratchpad, diff against main, put on a branch).
- Daily call is at **10 pm IST**. PRs due before the call. Tasks for the next day right after it.

## Timeline (IST)
G1 slipped. **G2 Thu Nov 12, 22:00**: stacks/difference, benchmarks baked, overlays, spectrum layer. **G3 Fri Nov 13, 23:00**: Two Opinions verdicts for the 5 benchmarks + Validation page. Fri Nov 13: read the official Resources tab + Submission/Judging guides, update docs 01/08. **Sat 14, 18:00 freeze**, video. **Sun 15, 18:00 submit**. Cuts agreed: sonification and mover search; **thermometer is NOT cut**.

## What is built and live (main)
- Web https://planetes.divergit.com (Vercel), API https://planetes-api.onrender.com (Render, deploys from main), GCS cache `gs://planetes-cache` (project `planetes-514208`, us-west1, ₹1,800 budget). `main` protected by ruleset (PR + CI; admin bypass).
- Live time-lapse: `POST /api/timelapse` → `access.find_frames` (IRSA TAP, QR2+QR3) → `fetch_cutouts` (batches of 8) → `frames.prepare_frame` → `render` (shared asinh stretch, WebP, flag PNG) → cache. Single exposures only (other modes return BAD_INPUT until D2.3). 59 Barnard D3 frames ≈ 2.5 min.
- Player (play/step/scrub/blink/flags/metadata), URL state, `/embed`, spectrum chart + Two Opinions panel (empty until data), sky map (Aladin Lite 3.8.2 from jsDelivr; images from ESA ESASky because CDS was down and IRSA HiPS has no CORS).
- Flags: QR2 `MP_*` keys, QR3 `MSKN/MSKM/MSKD` keys; SOURCE is informational.
- Validation data: `pipeline/notebooks/data/irsa_photometry_ra115.8000_dec-21.6785_qr2.csv` (350 rows; object and flux unit [VERIFY]).

## Known external problems
- **CDS (SIMBAD, MocServer, alasky) unreliable/down since Nov 9.** SIMBAD Harvard mirror works: `Simbad().server = "simbad.harvard.edu"`. astroquery 0.4.11: SIMBAD `ra`/`dec` are float **degrees**; valid votable fields `pmra`, `pmdec`, `plx_value`, `ids` (`pm`, `coo_epoch` no longer exist); SIMBAD positions are epoch J2000.
- SIMBAD names that resolve: `Barnard's Star` (Gaia DR3 4472832130942575872), `WISE J085510.83-071442.5` (no Gaia ID), `eps Ind B` (Gaia DR3 6412596012146801152), `RW Aur` (no Gaia ID in ids), `R Dra` (Gaia DR3 1648328016354496384).

## Work in progress (this session) — see "Progress log" below for what finished
1. D3.1: branch `shivaansh/d3.1-resolve` has Shivaansh's zip (commit 59d7dac) merged with main. Fixes needed: degrees not hourangle; `pmra/pmdec/plx_value/ids` fields; SIMBAD epoch J2000; Gaia match by DR3 ID from `ids` (not nearest-within-30″); coordinate input keeps the user's position; Harvard mirror fallback; benchmark names above; loosen one test tolerance (1e-6 → 0.1 mas). Then live test + Barnard within 2″ of a real 2026 frame.
2. Bake: `bake.py` (Rishabh-owned) writing `web/public/data/targets/{id}/timelapse_exposures.json` + frames + `target.json`, contract-valid; start with Barnard.
3. D4.4 verdict engine `verdict.py` per docs/04 §2–§5 (v_t = 4.74·μ·d; 5–150 km/s agree, 150–400 agree+note, >400 disagree; asteroid ranges overlap), tests per rule branch, output `Opinions.verdict`.

## First things to do in the new session
1. `git pull`. **PR #5 is merged** (D3.1 fix, bake, D4.4 verdict). Barnard and ε Indi B are baked and committed.
2. **Finish the bake:** `python -m api.bake rdra rwaur wise0855` (~3 min each; needs IRSA + SIMBAD Harvard mirror). Delete any half-written `web/public/data/targets/<id>/` first if it has no `timelapse_exposures.json`. Then `python contracts/validate.py`, open the site at `/?target=<id>`, commit, push.
3. Ask Rishabh how the 10 pm call went (Tirth's D2.3/D2.4 status, Shivaansh's D3.2, the new Role 4 person's name), then write tomorrow's tasks (PM_PLAYBOOK §5).

## Progress log
- Nov 11: **D3.1 done** on branch `shivaansh/d3.1-resolve`, PR #5 (18 tests incl. live pass; 5 benchmarks resolve; Barnard 1.86\" in a real 2026 frame). Gaia now via IRSA `gaia_dr3_source` (ESA 503; astroquery.gaia broken by ESA release 3.15).
- Nov 11: **Bake** `python -m api.bake <id>` (`api/bake.py`) uses the live pipeline; Barnard baked (60 frames, 414 KB, contract-valid; `contracts/validate.py` now maps target.json → resolved). Loads instantly at `/?target=barnard`. In PR #5. **Next: bake wise0855, epsindib, rwaur, rdra** (each ~3 min; WISE 0855 is faint below 3.5 µm).
- Nov 11: **D4.4 verdict engine built** (`pipeline/src/planetes/verdict.py`, `decide(motion, spectrum, saturated)`, 6 rule tests) in PR #5. Not yet wired into an API `/opinions` endpoint or bake (`opinions.json`): needs D3.3 motion + D4.x spectrum opinions first.
- Next after that: (done) D4.4 verdict engine (`pipeline/src/planetes/verdict.py`, docs/04 §2–§5), then a GitHub Action for baking, then help Tirth's D2.4/D2.3 land.
