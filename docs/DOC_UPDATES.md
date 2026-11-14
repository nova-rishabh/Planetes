# Doc updates log

Every time a doc changes, add a line here and post in the team group.

| Doc | Change |
|---|---|
| All | First upload of docs 00–08 to the repo |
| 01, 02, 05, 06, 08 | Hosting decided: website on Vercel (free), API on Render Starter (team credits) |
| AGENTS.md | Rule 10: no AI attribution outside AI_USAGE.md |
| 09 (new), AGENTS.md, README | Added doc 09 Design & Brand; AGENTS.md rule 11 (UI follows doc 09: tokens only, IBM Plex fonts, banned fonts); headings switched to IBM Plex Sans Condensed |
| 09 | Replaced with the light theme: printed-journal look, palette options A/B/C (C "Plate Archive" default, vote open), live URL planetes.xyz |
| web/src/styles/tokens.css (new) | Palette C tokens as CSS variables, plus the dark plate for sky frames |
| web/src/app/globals.css | Light theme; colours only from tokens |
| web/src/styles/tokens.test.ts (new) | Test: every palette token defined; no raw hex outside tokens.css |
| 02 | Hosting: custom domain planetes.xyz; new subsections Persistent cache (R2), Batch compute (Camber), Monitoring (Sentry); Fonts row points to doc 09 |
| 08 | Live link set to https://planetes.xyz |
| 01 | Open item: registered under Universal Event; global deadline to confirm |
| 06 | D1.1 marked done |
| STATUS (new) | Live URLs, deliverable states, next steps, all open [VERIFY] items |
| DECISIONS (new) | Decision log with reasons, collected from docs 01–09 |
| RUNBOOK (new) | Local setup, make targets, deploy flow, env vars, custom domain, rollback, IRSA down |
| AI_USAGE | Row for the light theme and the new docs |
| DOC_UPDATES | This set of rows |
| CLAUDE.md (new) | Claude Code entry point: loads AGENTS.md, PM_PLAYBOOK and STATUS; lists /daily, /tasks, /docupdate |
| PM_PLAYBOOK (new) | Project-manager rules for the AI agent: team, rhythm, templates, open items, ready messages |
| docs/assets/planetes-palettes-light.png (new) | Palette vote image (A Lab Notebook · B Clear Sky · C Plate Archive) |
| .claude/commands/daily.md, tasks.md, docupdate.md (new) | Slash commands for standup script, nightly tasks, doc-change log |
| .agents/workflows/daily.md, tasks.md, docupdate.md (new) | Same three workflows for Antigravity |
| AGENTS.md | Added "Project management rules: docs/PM_PLAYBOOK.md" |
| 09 | Handoff copy checked: identical to the version already in the repo, no change |
| 02 | Persistent cache is Google Cloud Storage (`planetes-cache`, asia-south1), not Cloudflare R2; new env vars `GCS_BUCKET`, `GCP_SERVICE_ACCOUNT_JSON` |
| RUNBOOK | GCS setup steps (bucket, 30-day lifecycle, service account, key into Render, $20 budget alert); GCS env vars |
| DECISIONS | R2 decision replaced: GCS over R2, team already has Google Cloud credit |
| STATUS | Live Vercel and Render URLs; all PM_PLAYBOOK §7 open items; R2 [VERIFY] replaced by trial-credit expiry |
| render.yaml | Declares `GCS_BUCKET=planetes-cache` and `GCP_SERVICE_ACCOUNT_JSON` (value set in the dashboard only) |
| DOC_UPDATES | This set of rows |
| STATUS | G0 meeting time changed; daily 10:30 standup unchanged |
| 05, PM_PLAYBOOK, STATUS | For clarification: the G0 meeting is at 10:00 (not 10:30) |
| 02, 08, 09, DECISIONS, PM_PLAYBOOK, RUNBOOK, STATUS | Live URL is now planetes.divergit.com (planetes.xyz was not available); RUNBOOK domain steps rewritten for a subdomain CNAME |
| 09, DECISIONS, STATUS, PM_PLAYBOOK | Palette C "Plate Archive" locked by team vote; A/B columns removed from doc 09 |
| RUNBOOK, render.yaml | New `JOB_WORKERS` env var (default 2) for the API job queue |
| STATUS, REFERENCES, AI_USAGE | D1.2 part 1 in progress; google-cloud-storage credited; AI use logged |
| RISHABH_GUIDE (new), STATUS | Rishabh's setup checklist (GCS, domain, PR reviews, Space Apps page, Camber, Sentry); STATUS notes PR #1 and Camber facts |
| 02, DECISIONS, RISHABH_GUIDE, STATUS | Camber is Rishabh-only (Student Pack plan), validation on laptops; guide adds GitHub collaborators + `main` protection |
| 02, DECISIONS, PM_PLAYBOOK, RISHABH_GUIDE, STATUS | Camber dropped: benchmark bakes run in GitHub Actions (laptop backup), validation notebooks on laptops |
| 02, DECISIONS, RISHABH_GUIDE, RUNBOOK, STATUS | GCS bucket region is us-west1 (Oregon, same as Render); planetes.divergit.com is live |
| RUNBOOK, STATUS, RISHABH_GUIDE | GCS cache set up in project planetes-514208 (bucket, 30-day rule, service account, ₹1,800 budget); only the Render key paste is left |
| RUNBOOK, STATUS, RISHABH_GUIDE | `main` protected by a ruleset (PR + green CI, admin bypass); GCS key is in Render |
| 02, AGENTS.md, DECISIONS, STATUS | For clarification: QR2 and QR3 cover different weeks, so time-lapses use both (not QR3-only); QR3 TAP names verified; STATUS notes PR #2 |
| contracts (descriptions only), STATUS, REFERENCES, AI_USAGE | `release: auto` = QR2+QR3; `target_xy` pixel convention written down; STATUS has the D1.3 progress and Rishabh's no-dependency plan |
| STATUS, AI_USAGE | Spectrum chart and Two Opinions panel built; plan updated |
| 02, REFERENCES, DECISIONS, STATUS, AI_USAGE | Sky context panel (Aladin Lite 3.8.2 from jsDelivr; AllWISE/2MASS/DSS2); Aladin licence noted; SPHEREx/unWISE HiPS IDs still to verify |
| STATUS | CDS outage noted (checked from 4 countries); IRSA HiPS mirrors can't be used in a browser (no CORS) |
| 02, REFERENCES, DECISIONS, STATUS | Sky map images switched to ESA ESASky (CDS down, IRSA copies have no CORS) |
| AGENTS.md, STATUS, DECISIONS, AI_USAGE | QR3 flag keys (MSKN/MSKM/MSKD) and SOURCE-is-not-a-defect in the gotchas; D2.1/D2.2 done; live time-lapse wired |
| STATUS | Collaborator invites dropped; work arrives as fork PRs or zips |
| pipeline/notebooks/data | Tirth's 350-row IRSA photometry export added for V4 and D4.1, with a provenance note |
| STATUS, AI_USAGE, HANDOFF (new) | D3.1 done; handoff file for the next AI session |
| HANDOFF, contracts/validate.py | Barnard baked; target.json validated against the Resolved schema |
| STATUS, AI_USAGE, HANDOFF | D4.4 verdict engine built |
| HANDOFF | First steps for the next session; ε Indi B baked |
| STATUS, HANDOFF | All 5 benchmarks baked |
| RUNBOOK, STATUS | "Bake benchmarks" GitHub Action: re-bake any benchmark from the Actions tab |
| STATUS | After the 10 pm call: who is on what for G2, Role 4 change, About page live |
| README, SUBMISSION (new) | README: live links, what works today, Windows activate fix, team list; new submission draft for the Space Apps form |
| STATUS | /api/opinions built, submission draft, Shivaansh has GitHub access |
| VALIDATION, STATUS, REFERENCES, AI_USAGE | D3.2 done; D3.3 fitter in, V1 pass with the Gaia epoch, V2 still to run; Shivaansh's references and AI-use row |
| DECISIONS | Cuts (D4.2, D3.4; D4.5/D1.6 final-day only); D4.1/D4.3 + interim photometry taken by Rishabh |
| REFERENCES, AI_USAGE | Sources for photometry, spectrum and typer (photutils, SpeX standards via SPLAT, Dupuy & Liu 2012, Cohen 2003, 2MASS) |
| VALIDATION | V4 interim, V5 pass, V6/V7 cut; shown on the new /validation page |
| VALIDATION | V3 note: WISE 0855 blended with a G 16.3 star; blend check added, spectra re-baked |
| 04 §6, DECISIONS | Planet X brightness formula corrected; cuts reversed (all wow items back); new /planet-x page |
| VALIDATION, REFERENCES, AI_USAGE | V7 back to “not run yet”; thermometer sources and Amish's draft credited |
| REMAINING_WORK (new) | Everything left before submission, priorities, owners, hours, checkpoints |
| IMPLEMENTATION_PLAN (new) | Step-by-step plan for Rishabh's items: Tirth merge, DR1, stacks bake, homepage redesign, known asteroids, verdicts, tour, V10, sonification, submission |
| STATUS, VALIDATION | Status update (open PRs #20–#25, D3.3 pending push); V6 interim, V10 attempt (IRSA 503) |
| VALIDATION | V6 ten-field run: 8 of 10 asteroids matched (median 0.07 px); V10 passes (ε Indi B still T3, 2.55–3.69 pc, on a clean DR1 re-bake) |
| SUBMISSION, README | Feature lists brought up to date (homepage, viewer, typer/thermometer, Planet X, tour/sound, DR1, known asteroids) |
| (data) | opinions.json baked for all 5 benchmarks: spectrum opinion from measured points; all 'can't tell' until D3.3 motion is wired |
| (web) | New homepage: scroll story with real frames (blink, colour, Two Opinions, Planet X, benchmarks); viewer moved to /viewer, old links redirect |
| (web) | Guided tour on the viewer (D1.6) and sonified time-lapse (D1.7: pitch = wavelength, loudness = target brightness, tick on blink) |
| AGENTS, contracts (common) | SPHEREx DR1 added as a release (IRSA now lists DR1 + QR3, QR2 gone); DR1 > QR3 > QR2 for the same exposure |
| (data) | Stacks, difference and colour time-lapses baked for the 5 benchmarks (bake --modes) |
| 09, REFERENCES, AI_USAGE | 3D homepage: new §8 (3D rules), Igloo Inc + 100,000 Stars as references; three.js, r3f, drei, GSAP, Lenis credited |
| 09, AI_USAGE | 3D homepage Phase 2: colour scene rules added to §8 |
| 09, AI_USAGE | 3D homepage Phase 3 rules added to §8 |
| 09, AI_USAGE | New §3d "Bold editorial": tokens, type, layout rules (replaces the softer Plate Archive look; still light) |
| VALIDATION | Notes cleaned for the public page (no dates, names or PR numbers); V3, V4, V6, V7 marked In progress with their partial results |
| SUBMISSION | Rewritten to the official form fields: 30 s video or ≤ 7 slides, SI options, NASA and other data link lists, DR1 DOI |
| AGENTS, all docs, code comments | Project-timeline dates removed (log tables lose their Date column; schedules become ordered steps). Science dates (observation times, Gaia epoch) stay |
| AI_USAGE | Guided tour can start from the homepage and now plays, blinks and shows stars at each stop |
| VALIDATION | V6 passed (15 known asteroids found in 20 ecliptic fields, within 1 px); V8 passed (R Dra and RW Aur labelled Can't tell: saturated) |
| STATUS | Deliverable states brought up to the live site (tour, DR1, V6/V8 pass); Team Owner transfer ticked; team-page text moved to Rishabh |
| VALIDATION | V9 passed (at most 1 fake mover per field over 100 date shuffles; ε Indi B caught with the real dates) |
| 08-Demo-Pitch-Submission | Demo video section rewritten to the official 30 s rule with a script that matches the live site (tour, blink, ε Indi B spectrum, Validation); 2-minute cut removed |
| SUBMISSION | Gaia DR3 link now points to IRSA's copy, which the code queries (was the MAST page) |
