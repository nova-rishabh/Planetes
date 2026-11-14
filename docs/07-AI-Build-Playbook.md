# Planetes 07 — AI Build Playbook

How we build Planetes fast with AI coding agents without shipping wrong science.

## 1. Tools and how they read our rules

| Tool | Reads | Notes |
| --- | --- | --- |
| **Google Antigravity** | `AGENTS.md` (since IDE 1.20.5) and `GEMINI.md`; extra rules in `.agents/rules/*.md`; slash-workflows in `.agents/workflows/*.md` | Use **Planning** mode for anything non-trivial; review its implementation plan before it codes. Parallel agents: **never let two agents edit the same file** (last write wins silently). |
| **OpenAI Codex** (CLI / IDE / cloud) | `AGENTS.md`; the nearest one to the edited file wins | Use plan mode (`/plan`) for multi-step work. Cloud tasks may not have internet, so give it real fixture files in the repo. |
| **Claude Code / Cursor / others** | `AGENTS.md` (plus their own files) | Same rules apply. |

**One source of truth:** `AGENTS.md` at the repo root, plus short `pipeline/AGENTS.md` and `web/AGENTS.md`. Every time you correct an agent twice for the same thing, add a rule there.

## 2. The workflow for every deliverable

1. **Plan:** paste the deliverable's starter prompt (section 6) and ask for a plan first. Read it. Reject plans that invent APIs or skip tests.
2. **Look at real data first:** make the agent print the **actual** TAP columns, FITS extension names and header keys from a real file before writing logic.
3. **Build small:** one module or component per session. New session per phase (long sessions degrade).
4. **Test on real data:** pytest with the tiny real fixtures in `pipeline/tests/data/`; a screenshot or plot from a live run.
5. **Self-review with the checklist** in section 7.
6. **PR:** branch `name/dX.Y-short-title`, description = what/why/how to run + screenshot. Rishabh merges.

## 3. Root `AGENTS.md` (paste as-is)

```markdown
# Planetes — rules for AI coding agents

## What this is
Public web tool for NASA Space Apps 2026 "Planet X and SPHEREx": user enters RA/Dec, we show SPHEREx
images of that patch as a time-lapse (exposures, detector stacks, differences, colour), with flags,
Gaia/WISE overlays, spectra on the fly, and a "Two Opinions" verdict (motion vs spectrum).
Specs: docs/ (PRD, TRD, Data Contract, Science brief). The Data Contract in contracts/ is law.

## Layout
- pipeline/src/planetes/  Python package (science + data). Tests in pipeline/tests/.
- api/                    FastAPI app that imports planetes.
- web/                    Next.js (static export), TypeScript. Baked data in web/public/data/.
- contracts/              JSON Schemas; generated pydantic + TS types (never hand-edit generated files).

## Ownership (do not edit outside your task's area without saying so in the PR)
- web/, api/, contracts/, render.yaml, .github/, bake.py, cli.py, cache.py -> Rishabh
- access.py, frames.py, stack.py, render.py, photometry.py, spectrum.py -> Tirth
- resolve.py, overlays.py, known.py, motion.py -> Shivaansh
- thermal.py, typing.py, verdict.py, validation notebooks -> Shimaya

## Commands
- Python: `cd pipeline && pip install -e .[dev] && pytest -q`
- API: `uvicorn api.main:app --reload`
- Web: `cd web && npm ci && npm run dev` ; checks: `npm run lint && npm run typecheck && npm run test`
- Contracts: `make contracts` regenerates types; CI fails if they are stale.

## Non-negotiable rules
1. REAL DATA ONLY. Never create mock, demo, placeholder or synthetic data that could appear in the app.
   No silent fallbacks to fake values. If data is missing, return null and a reason.
2. Never invent API endpoints, table/column names, FITS keywords or library functions.
   Print the real ones from a real response/file first, then code against what you saw.
3. Units in every variable/field name or an explicit unit field (flux_ujy, wavelength_um, fov_deg).
4. Every measurement keeps provenance: SPHEREx obs_id, release (QR2/QR3), code_version.
5. All API responses and baked files must validate against contracts/. Add/adjust tests.
6. Small, reviewable changes. One module/component per task. Add tests with each change.
7. Cite every external code idea or library in docs/REFERENCES.md in the same PR.
8. No secrets in the repo. No NASA logo/insignia in the UI.
9. UI fonts: never use Inter.

## SPHEREx gotchas (read before touching data code)
- Use cutouts (?center=RA,DECd&size=DEG), never full ~70 MB files.
- Prefer TAP (spherex.artifact JOIN spherex.plane) over SIA (SIA lags ~1 day). Query QR3, fall back to QR2.
- IMAGE is MJy/sr and NOT zodi-subtracted: subtract the ZODI extension.
- FLAGS meanings come from header MP_* keys; never hard-code bit meanings.
- Wavelength per pixel: WCS(header, fobj=hdul, key="W"); set .sip = None.
- PSF: VERSION < 7 -> PSF cube (11x11 zones, 10x oversampled); VERSION >= 7 (QR3) -> EPSF table (zones, 5x).
  Choose the zone using parent-image pixels via CRPIX1A/CRPIX2A. Never feed oversampled PSF directly to a fitter.
- FITS header pixel values are 1-based; numpy/astropy are 0-based.
- Long-wavelength detectors (D4-D6) are mirrored in X vs D1-D3: always use the WCS, never assume orientation.
- Detector pairs see the same sky at the same moment: D1&D4, D2&D5, D3&D6.
- High proper-motion stars: propagate positions to each frame date (SkyCoord.apply_space_motion). Gaia epoch = 2016.0.
- Bright stars saturate (~AB 11.7 short to 9.7 long): mark saturated, never use in verdicts.
- Set astropy remote_timeout=120 and retry with backoff; cap parallel IRSA requests at 8.

## Definition of done
Tests pass; output validates against contracts; a screenshot/plot on real SPHEREx data is in the PR;
REFERENCES.md and AI_USAGE.md updated.
```

## 4. Short sub-files

```markdown
# pipeline/AGENTS.md
- Python 3.11, type hints everywhere, pydantic v2 models generated from contracts/.
- numpy float32 for images; never load full SPHEREx files.
- Every public function has a docstring stating units of inputs/outputs.
- Tests use only real fixtures in tests/data (tiny cutouts). Mark network tests with @pytest.mark.network.
```

```markdown
# web/AGENTS.md
- Next.js App Router, static export. TypeScript strict. Types come from contracts/ (generated).
- Same code path for baked files and live API (only base URL differs).
- All view state lives in the URL (see docs Data Contract §2). /embed reuses the same components.
- Accessibility: keyboard controls, focus states, alt text, contrast >= 4.5:1. No Inter font.
```

## 5. Antigravity extras

```markdown
# .agents/rules/science-integrity.md
---
trigger: always_on
---
Never fabricate data or results. If a value cannot be measured, return null with a reason.
Before writing data-access code, print real column names / FITS keywords from a live call.
```

```markdown
# .agents/workflows/verify.md
---
description: Verify a deliverable before PR
---
1. Run `pytest -q` in pipeline/ and `npm run lint && npm run typecheck` in web/.
2. Run the module on one benchmark target with real data; save a screenshot/plot to docs/evidence/.
3. Validate outputs against contracts/ (`make validate`).
4. Summarise what changed and any [VERIFY] items still open.
```

## 6. Starter prompts per deliverable

**How to use:** paste the generic header, then the deliverable block. Attach (or point to) docs 02, 03 and 04.

**Generic header:**

> You are working in the Planetes repo. Read AGENTS.md, docs/TRD, docs/DATA\_CONTRACT and docs/SCIENCE first. Produce a short plan before coding. First print the real API columns / FITS keywords you will rely on. Use only real SPHEREx data; no mock data. Add tests. Stop and ask if something in the docs conflicts with what you observe.

| Code | Starter prompt (after the header) |
| --- | --- |
| **D2.1** | “Implement `planetes/access.py`: `find_frames(ra, dec, release='auto', detectors=None, mjd_range=None)` using IRSA TAP (`spherex.artifact` JOIN `spherex.plane`, CONTAINS POINT). Try QR3 then QR2; print the real column names first. Return a list of frame records (obs\_id, release, mjd, detector, access URL). Add `group_epochs(frames, gap_days=30)` and `fetch_cutouts(frames, ra, dec, size_deg, max_workers=8)` with retries, 120 s timeout and an on-disk cache. Tests: Barnard's Star at its propagated position returns ≥ 1 frame per detector.” |
| **D2.2** | “Implement `frames.py` + `render.py`: for each cutout, IMAGE − ZODI, mask flags chosen from header `MP_*` meanings, wavelength at centre via spectral WCS key `W` (sip=None), reproject to a common north-up TAN grid (`reproject_interp`), shared asinh stretch, WebP + transparent flag PNG. Output frames matching the `TimelapseResult.frames` schema in contracts/.” |
| **D2.3** | “Implement `stack.py`: per-epoch per-detector inverse-variance-weighted stacks (exclude flagged pixels), difference (epoch B − A, same detector, propagate variance), sum, and colour composite (D1+D2 blue, D3+D4 green, D5+D6 red). Tests on real fixtures: stack noise lower than single frame.” |
| **D2.4** | “Implement `photometry.py` + `spectrum.py`: forced photometry at a (propagated) position in every frame using the correct PSF (PSF cube if VERSION<7, EPSF table if ≥7; zone chosen via CRPIX1A/2A; shift-integrate-normalise), fit amplitude + local background; aperture fallback. Convert MJy/sr → µJy (pixel solid angle; print what you use). Record pair\_id for D1&4, D2&5, D3&6. Study xcavation (MIT) for approach and credit it. Output `SpectrumResult`.” |
| **D3.1** | “Implement `resolve.py`: name → (ra, dec, pm\_ra, pm\_dec, parallax, ref\_epoch) via astroquery SIMBAD/Gaia; `position_at(mjd)` using `SkyCoord.apply_space_motion`. Tests: the 5 benchmarks resolve; Barnard's Star moves \~10.4″/yr.” |
| **D3.2** | “Implement `overlays.py`: Gaia DR3 (and AllWISE) sources within a field, each propagated to a list of MJDs; return the `Overlays` schema. Cap counts; brightest first.” |
| **D3.3** | “Implement proper-motion fitting in `motion.py`: inputs = positions with errors and epochs (SPHEREx centroids + optional Gaia/AllWISE), output μ, PA, errors, χ². Validate on Barnard's Star (V1) and ε Indi B (V2) per docs/SCIENCE.” |
| **D3.4** | “Implement `known.py`: known asteroids in a frame via JPL SBIdent (observer = SPHEREx state vector if available in header, else geocentre) and an asteroid rate → heliocentric distance range in `motion.py` (circular-orbit grid 0.8–60 AU). Validate vs JPL Horizons.” |
| **D4.1** | “Implement spectrum assembly helpers: rejection rules (flags, saturation, low S/N) with plain-language reasons, pairing D1&4/D2&5/D3&6, plot-ready series by epoch. Notebook comparing our fluxes to IRSA's Spectrophotometry Tool for 3 unsaturated stars (V4).” |
| **D4.3** | “Implement `typing.py`: load SPHEREx brown-dwarf/late-M templates (source and licence from docs), χ² match with free scale, return type ± uncertainty; photometric distance from a cited absolute-magnitude relation. Validate on ε Indi B (V5).” |
| **D4.4** | “Implement `verdict.py` exactly per docs/SCIENCE §2–§5 rules; output `Opinions.verdict` with confidence and 2–4 plain-language reasons. Unit tests for each rule branch.” |
| **D1.2** | “Build the FastAPI app per docs/DATA\_CONTRACT §3–§5: job queue (asyncio + thread pool), endpoints, CORS from `ALLOWED_ORIGINS`, limits, error format, `/health`. Responses validated by the generated pydantic models.” |
| **D1.3** | “Build the time-lapse player in web/: canvas (WebGL2 if available) showing frames from a `TimelapseResult`; play/pause/step/scrub/speed/loop, A/B blink, per-frame metadata, flag overlay with legend, smooth on mobile. Same code for baked files and live API.” |
| **D1.4** | “Add mode switcher, FOV control, URL state sync (all params in docs §2), `/embed` route, spectrum chart (error bars, colour by epoch, rejected points greyed with reason) and an Aladin Lite v3 panel with SPHEREx D1–D6 HiPS + Gaia layer.” |

## 7. Review checklist for AI output

**Science / data:**

- [ ] Did it print real column names / keywords before using them?
- [ ] Zodi subtracted? Flags read from header? Saturated points excluded from science?
- [ ] Correct PSF format for the file version? Zone chosen with CRPIX1A/2A?
- [ ] Positions propagated for moving stars? Gaia epoch 2016.0 used?
- [ ] Units correct and named? MJy/sr → µJy conversion stated?
- [ ] Any hard-coded “expected” numbers that could leak into the UI? Remove them.

**Code:**

- [ ] Tests on real fixtures pass; network tests marked.
- [ ] Output validates against contracts.
- [ ] No new dependency without a reason and a REFERENCES.md entry.
- [ ] No edits outside the task's owned files (or explained in the PR).

## 8. Typical AI mistakes on this project (watch for them)

- Inventing astroquery functions or IRSA table names that don't exist.
- Using J2000 coordinates for Barnard's Star, so the star is “missing.”
- Blinking frames without reprojection (stars jump around) or without zodi subtraction (background flickers).
- Treating the 6 detectors as the same colour.
- “Fixing” a failing test by adding fake data or loosening the assertion.
- Writing confident UI text (“discovered”, “confirmed”) that doc 04 §8 forbids.

## 9. Disclosure

Keep `docs/AI_USAGE.md` current: tool, model (if shown), what it generated, what a human checked. Include it in the submission if the 2026 guide asks (check the official guide).

## Sources

- [Antigravity reads AGENTS.md (rules guide)](https://thepromptshelf.dev/blog/google-antigravity-agents-md-rules-guide-2026)
- [Antigravity rules, skills, workflows](https://dev.to/malloc72p/antigravity-getting-the-most-out-of-agentic-coding-with-rules-skills-and-workflows-54pb)
- [Antigravity tips (parallel agents, file boundaries)](https://dev.to/hiroki-ii-ai/10-tips-for-antigravity-20-a-beginners-guide-that-actually-works-3h5d)
- [Codex best practices (official)](https://developers.openai.com/codex/learn/best-practices)
- [Codex AGENTS.md discovery order](https://codex.danielvaughan.com/2026/04/19/openai-codex-cli-official-documentation-guide/)
