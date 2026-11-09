# Doc updates log

Every time a doc changes, add a line here and post in the team group.

| Date (IST) | Doc | Change |
|---|---|---|
| 2026-11-08 | All | First upload of docs 00–08 to the repo |
| 2026-11-08 | 01, 02, 05, 06, 08 | Hosting decided: website on Vercel (free), API on Render Starter (team credits) |
| 2026-11-08 | AGENTS.md | Rule 10: no AI attribution outside AI_USAGE.md |
| 2026-11-08 | 09 (new), AGENTS.md, README | Added doc 09 Design & Brand; AGENTS.md rule 11 (UI follows doc 09: tokens only, IBM Plex fonts, banned fonts); headings switched to IBM Plex Sans Condensed |
| 2026-11-08 | 09 | Replaced with the light theme: printed-journal look, palette options A/B/C (C "Plate Archive" default, vote open), live URL planetes.xyz |
| 2026-11-08 | web/src/styles/tokens.css (new) | Palette C tokens as CSS variables, plus the dark plate for sky frames |
| 2026-11-08 | web/src/app/globals.css | Light theme; colours only from tokens |
| 2026-11-08 | web/src/styles/tokens.test.ts (new) | Test: every palette token defined; no raw hex outside tokens.css |
| 2026-11-08 | 02 | Hosting: custom domain planetes.xyz; new subsections Persistent cache (R2), Batch compute (Camber), Monitoring (Sentry); Fonts row points to doc 09 |
| 2026-11-08 | 08 | Live link set to https://planetes.xyz |
| 2026-11-08 | 01 | Open item: registered under Universal Event; global deadline to confirm Nov 13 |
| 2026-11-08 | 06 | D1.1 marked done |
| 2026-11-08 | STATUS (new) | Live URLs, deliverable states, next steps, all open [VERIFY] items |
| 2026-11-08 | DECISIONS (new) | Dated decision log with reasons, collected from docs 01–09 |
| 2026-11-08 | RUNBOOK (new) | Local setup, make targets, deploy flow, env vars, custom domain, rollback, IRSA down |
| 2026-11-08 | AI_USAGE | Row for the light theme and the new docs |
| 2026-11-08 | DOC_UPDATES | This set of rows |
| 2026-11-08 | CLAUDE.md (new) | Claude Code entry point: loads AGENTS.md, PM_PLAYBOOK and STATUS; lists /daily, /tasks, /docupdate |
| 2026-11-08 | PM_PLAYBOOK (new) | Project-manager rules for the AI agent: team, rhythm, templates, open items, ready messages |
| 2026-11-08 | docs/assets/planetes-palettes-light.png (new) | Palette vote image (A Lab Notebook · B Clear Sky · C Plate Archive) |
| 2026-11-08 | .claude/commands/daily.md, tasks.md, docupdate.md (new) | Slash commands for standup script, nightly tasks, doc-change log |
| 2026-11-08 | .agents/workflows/daily.md, tasks.md, docupdate.md (new) | Same three workflows for Antigravity |
| 2026-11-08 | AGENTS.md | Added "Project management rules: docs/PM_PLAYBOOK.md" |
| 2026-11-08 | 09 | Handoff copy checked: identical to the version already in the repo, no change |
| 2026-11-08 | 02 | Persistent cache is Google Cloud Storage (`planetes-cache`, asia-south1), not Cloudflare R2; new env vars `GCS_BUCKET`, `GCP_SERVICE_ACCOUNT_JSON` |
| 2026-11-08 | RUNBOOK | GCS setup steps (bucket, 30-day lifecycle, service account, key into Render, $20 budget alert); GCS env vars |
| 2026-11-08 | DECISIONS | R2 decision replaced: GCS over R2, team already has Google Cloud credit |
| 2026-11-08 | STATUS | Live Vercel and Render URLs; all PM_PLAYBOOK §7 open items; R2 [VERIFY] replaced by trial-credit expiry |
| 2026-11-08 | render.yaml | Declares `GCS_BUCKET=planetes-cache` and `GCP_SERVICE_ACCOUNT_JSON` (value set in the dashboard only) |
| 2026-11-08 | DOC_UPDATES | This set of rows |
| 2026-11-08 | STATUS | G0 meeting moved to tonight Sun 8, 22:00 (was Mon 9, 10:30); daily 10:30 standup unchanged |
| 2026-11-08 | 05, PM_PLAYBOOK, STATUS | For clarification: the G0 meeting is Mon 9 at 10:00 (not 10:30, and not Sun 22:00) |
| 2026-11-08 | 02, 08, 09, DECISIONS, PM_PLAYBOOK, RUNBOOK, STATUS | Live URL is now planetes.divergit.com (planetes.xyz was not available); RUNBOOK domain steps rewritten for a subdomain CNAME |
| 2026-11-09 | 09, DECISIONS, STATUS, PM_PLAYBOOK | Palette C "Plate Archive" locked by team vote; A/B columns removed from doc 09 |
| 2026-11-09 | RUNBOOK, render.yaml | New `JOB_WORKERS` env var (default 2) for the API job queue |
| 2026-11-09 | STATUS, REFERENCES, AI_USAGE | D1.2 part 1 in progress; google-cloud-storage credited; AI use logged |
| 2026-11-09 | RISHABH_GUIDE (new), STATUS | Rishabh's setup checklist (GCS, domain, PR reviews, Space Apps page, Camber, Sentry); STATUS notes PR #1 and Camber facts |
| 2026-11-09 | 02, DECISIONS, RISHABH_GUIDE, STATUS | Camber is Rishabh-only (Student Pack plan), validation on laptops; guide adds GitHub collaborators + `main` protection |
| 2026-11-09 | 02, DECISIONS, PM_PLAYBOOK, RISHABH_GUIDE, STATUS | Camber dropped: benchmark bakes run in GitHub Actions (laptop backup), validation notebooks on laptops |
| 2026-11-09 | 02, DECISIONS, RISHABH_GUIDE, RUNBOOK, STATUS | GCS bucket region is us-west1 (Oregon, same as Render); planetes.divergit.com is live |
| 2026-11-09 | RUNBOOK, STATUS, RISHABH_GUIDE | GCS cache set up in project planetes-514208 (bucket, 30-day rule, service account, ₹1,800 budget); only the Render key paste is left |
| 2026-11-09 | RUNBOOK, STATUS, RISHABH_GUIDE | `main` protected by a ruleset (PR + green CI, admin bypass); GCS key is in Render |
| 2026-11-09 | 02, AGENTS.md, DECISIONS, STATUS | For clarification: QR2 and QR3 cover different weeks, so time-lapses use both (not QR3-only); QR3 TAP names verified; STATUS notes PR #2 |
| 2026-11-09 | contracts (descriptions only), STATUS, REFERENCES, AI_USAGE | `release: auto` = QR2+QR3; `target_xy` pixel convention written down; STATUS has the D1.3 progress and Rishabh's no-dependency plan |
