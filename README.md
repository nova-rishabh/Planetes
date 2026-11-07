# Planetes

NASA Space Apps Challenge 2026 · Challenge: **Planet X and SPHEREx** · Team Planetes

A public web tool: type sky coordinates and watch real NASA SPHEREx infrared images of that patch play as a short time-lapse. Moving and changing objects pop out, and for each one Planetes gives **two independent opinions** (how it moves, and what its 102-colour spectrum says) and shows whether they agree.

## Docs (read in this order)
| # | Doc | What it covers |
|---|---|---|
| 00 | [Team Handout](docs/00-Team-Handout.md) | SPHEREx and the challenge, for beginners |
| 01 | [PRD](docs/01-PRD.md) | What we build and why; features F1–F14 mapped to the official considerations |
| 02 | [TRD](docs/02-TRD.md) | Architecture, hosting, SPHEREx gotchas, stack |
| 03 | [Data Contract & API](docs/03-Data-Contract-API.md) | URL params, endpoints, JSON shapes (source of truth) |
| 04 | [Science & Validation](docs/04-Science-Validation.md) | Targets, Two Opinions physics, tests V1–V10 |
| 05 | [Phases & Timeline](docs/05-Phases-Timeline.md) | Phases, gates, buffer, cut rules |
| 06 | [Role Guide](docs/06-Role-Guide.md) | Who owns what; deliverables D1.x–D4.x |
| 07 | [AI Build Playbook](docs/07-AI-Build-Playbook.md) | How we use Antigravity / Codex safely; starter prompts |
| 08 | [Demo, Pitch & Submission](docs/08-Demo-Pitch-Submission.md) | Video script, Q&A, submission checklist |

Doc changes are logged in [docs/DOC_UPDATES.md](docs/DOC_UPDATES.md). **The docs in this repo are the current version.**

## Repo layout
```
AGENTS.md            rules for AI coding agents (Antigravity, Codex, Claude Code, Cursor)
.agents/             Antigravity rules + workflows
contracts/           JSON Schemas (built in D1.1 from docs/03)
pipeline/            Python package `planetes` (science + data)
api/                 FastAPI app (deployed on Render)
web/                 Next.js app (deployed on Vercel); web/public/data = baked benchmarks
docs/                specs, references, AI usage, validation
```

## Hosting
- Website: **Vercel** (project root `web/`)
- API: **Render** Web Service Starter, via `render.yaml`

## Team
Rishabh Kataria (platform, integration, frontend) · Tirth (data & imaging, pitch) · Shivaansh (motion & orbits) · Shimaya (spectral science & ML, science lead)

## Credits
Every data source, library and tool is listed in [docs/REFERENCES.md](docs/REFERENCES.md). AI tool use is disclosed in [docs/AI_USAGE.md](docs/AI_USAGE.md). This project is not endorsed by NASA.

## Licence
MIT (see LICENSE). Third-party data and code keep their own licences.
