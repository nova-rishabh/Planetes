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

## Hosting
- web/ deploys on Vercel (project root web/). api/ deploys on Render Starter via render.yaml. Never add Vercel serverless functions for long jobs.

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
10. No AI attribution in commits, PR descriptions, code comments or docs (no Co-Authored-By,
    'Generated with …' lines). AI use is disclosed only in docs/AI_USAGE.md.
11. UI follows docs/09: tokens only (no raw hex), IBM Plex fonts,
    no Inter/Roboto/Poppins/Montserrat/Space Grotesk, nothing that looks AI-generated (see docs/09 §3c).

## SPHEREx gotchas (read before touching data code)
- Use cutouts (?center=RA,DECd&size=DEG), never full ~70 MB files.
- Prefer TAP (spherex.artifact JOIN spherex.plane) over SIA (SIA lags ~1 day). QR2 and QR3 cover different weeks: use both, prefer QR3 only for the same exposure, record the release.
- IMAGE is MJy/sr and NOT zodi-subtracted: subtract the ZODI extension.
- FLAGS meanings come from the FLAGS header: QR2 `MP_<NAME> = bit`, QR3 `MSKNnnnn` name + `MSKMnnnn` mask + `MSKDnnnn` description. Never hard-code bit meanings. Bit SOURCE (pixel on a known source) is information, not a defect.
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

## Project management
Project management rules: docs/PM_PLAYBOOK.md.
