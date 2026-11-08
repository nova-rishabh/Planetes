# AI usage disclosure

| Date | Person | Tool (and model if shown) | What it generated | What a human checked |
|---|---|---|---|---|
| 2026-11-07 | Rishabh | Claude | Planning docs 00–08 (drafts) | Reviewed by Rishabh |
| 2026-11-08 | Rishabh | Claude Code (Claude Opus 5.5) | D1.1 scaffold: contract JSON Schemas (docs/03 §3-§5 + JobCreated) and generators (pydantic models, TS types, `make contracts`, `make validate`); `planetes` package skeleton and contract tests; FastAPI `GET /api/health` with live IRSA TAP probe, CORS and docs/03 error format; Next.js static page with live API status badge; CI workflow; README run instructions; AGENTS.md rule 10 (no AI attribution) | Approved the plan before coding; checked schemas against docs/03; ran `make contracts` (no diff), `make validate`, `pytest -q` (incl. live IRSA test), ruff, web lint/typecheck/test/build locally; saw the real `/api/health` JSON validate; checked the badge in a browser against the local API in both ok and unreachable states (screenshot in docs/evidence/) |
