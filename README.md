# Planetes

NASA Space Apps Challenge 2026 · Challenge: **Planet X and SPHEREx** · Team Planetes

A public web tool: type sky coordinates and watch real NASA SPHEREx infrared images of that patch play as a short time-lapse. Moving and changing objects pop out, and for each one Planetes gives **two independent opinions** (how it moves, and what its 102-colour spectrum says) and shows whether they agree.

**Try it:** https://planetes.divergit.com · API health: https://planetes-api.onrender.com/api/health

## What works today
- **Homepage** that opens on a real SPHEREx time-lapse and walks through blink, colour, Two Opinions and Planet X with real frames and numbers.
- **Viewer** (`/viewer`): any RA/Dec → every SPHEREx exposure of that spot (IRSA: DR1 + QR3; QR2 for older bakes) as a time-lapse: play, step, scrub, blink two frames, quality flags, Gaia DR3 + AllWISE stars moved to each date, per-frame date/detector/wavelength, a sound mode and a guided tour.
- The five challenge targets (Barnard's Star, ε Indi B, WISE 0855, RW Aur, R Dra) baked from real data: time-lapse, catalogue stars, spectrum, Two Opinions.
- **Spectrum** from 0.75 to 5 µm with every rejected point explained; brown-dwarf/star **typer** (ε Indi B → T3, 2.5–3.7 pc vs 3.64 pc known) and an asteroid **thermometer** (NEATM).
- **Planet X check** (`/planet-x`), **Validation** (`/validation`), **About** (`/about`); shareable URLs and `/embed`.
- In review / landing next: detector stacks + difference images, measured motion (Two Opinions verdicts), known asteroids from JPL (V6).

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
| 09 | [Design & Brand](docs/09-Design-and-Brand.md) | Name, palette tokens, typography, layout, reference sites |
| — | [Submission draft](docs/SUBMISSION.md) | Text for the Space Apps form |

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

## How to run locally

Needs Python 3.11, Node 22 (see `web/.nvmrc`) and GNU Make. Commands run from the repo root unless noted.

**Python package + API**
```bash
python3.11 -m venv .venv            # or: uv venv --python 3.11 .venv
source .venv/bin/activate           # Windows: .venv\Scripts\activate
pip install -e "pipeline[dev]" -r api/requirements.txt
ALLOWED_ORIGINS=http://localhost:3000 uvicorn api.main:app --reload --port 8000
```
Then open http://localhost:8000/api/health (live check of the IRSA TAP service). Optional env vars:
`ALLOWED_ORIGINS` (comma-separated; unset = no cross-origin access), `GIT_COMMIT` (else Render's
`RENDER_GIT_COMMIT`, else `dev`).

**Web**
```bash
cd web
cp .env.example .env.local          # NEXT_PUBLIC_API_BASE=http://localhost:8000
npm ci
npm run dev                         # http://localhost:3000
```

**Contracts** (JSON Schemas in `contracts/` are the source of truth)
```bash
make contracts    # regenerate pipeline/src/planetes/contracts.py and web/src/types/contracts.ts (needs npm ci in web/)
make validate     # validate every JSON file in web/public/data against its schema
```

**Tests and checks**
```bash
cd pipeline && pytest -q -m "not network"   # add -m network for tests that call IRSA
ruff check pipeline api contracts
cd web && npm run lint && npm run typecheck && npm run test && npm run build
```

## Team
Rishabh Kataria (platform, integration, frontend) · Tirth (data & imaging, pitch) · Shivaansh (motion & orbits)

## Credits
Every data source, library and tool is listed in [docs/REFERENCES.md](docs/REFERENCES.md). AI tool use is disclosed in [docs/AI_USAGE.md](docs/AI_USAGE.md). This project is not endorsed by NASA.

## Licence
MIT (see LICENSE). Third-party data and code keep their own licences.
