# Planetes 06 — Role Guide & Deliverables

Nov 8, 2026 · What each person owns and hands over. Daily tasks come separately every night.

## How to read this

- **Deliverable (D-code)** = something concrete merged into the repo: code + tests + a proof screenshot on real data.
- **We build with AI coding agents** (Antigravity, Codex, Claude Code, Cursor…). For each deliverable the table says what the AI should produce and what **you** must check yourself. You're responsible for correctness, not the AI. Prompt templates are in doc 07.
- **Priority:** Must / Should / Could. **Phase:** see doc 05.
- **Files you own** = the AI may edit them freely in your branch. Anything else needs the owner's review.

## Team

| Person | Role | Also |
| --- | --- | --- |
| **Rishabh** | Roles 1+5 — Platform, Integration, Frontend & UX | Team lead, final scope calls, nightly task list |
| **Tirth** | Role 2 — Data & Imaging | **Pitch & video owner** |
| **Shivaansh** | Role 3 — Motion & Orbits | False-alarm testing |
| **Shimaya** | Role 4 — Spectral Science & ML | **Science lead**: final fact-check of every claim |

## How the work connects

```
Shivaansh: resolve + proper motion ──▶ Tirth: fetch + clean + align frames ──▶ Rishabh: API + player
                 │                                   │
                 ▼                                   ▼
     overlays + motion fits             photometry → spectrum points ──▶ Shimaya: typer / thermometer / verdict
                 └──────────────────────────── all outputs follow doc 03 ─────────────────────┘
```

---

## Rishabh — Platform, Integration, Frontend & UX

**Mission:** turn everyone's work into one fast, beautiful, trustworthy public tool, and keep it submittable at every phase.

**Files you own:** `web/`, `api/`, `contracts/`, `render.yaml`, `.github/`, `AGENTS.md`, `bake.py`, `cli.py`, `cache.py`.

| Code | Deliverable | Pri | Phase | AI produces | You verify (acceptance) |
| --- | --- | --- | --- | --- | --- |
| D1.1 | Repo, AGENTS.md, contracts (JSON Schema → pydantic + TS types), CI, Vercel (web) + Render Blueprint (API). **Done (Nov 8).** | Must | 0–1 | Scaffolding, schema files, generators, CI workflow | CI fails on an invalid payload; both services deploy from `main` |
| D1.2 | API: jobs, `/timelapse`, `/spectrum`, `/jobs`, `/frames`, `/overlays`, `/resolve`, `/health`, CORS, limits, errors | Must | 1–2 | FastAPI app wiring the `planetes` package | Every response validates against doc 03; a cold start shows a friendly message |
| D1.3 | Player: coordinate input, 5 benchmark buttons, play/step/scrub/blink, frame metadata, flag overlay + legend; bake workflow | Must | 1 | Canvas/WebGL2 player component, GitHub Action for baking | Barnard's Star motion visible; smooth on a phone; baked benchmarks load < 3 s |
| D1.4 | Mode switcher (exposures/stacks/difference/sum/colour), FOV control, URL state + `/embed`, spectrum chart, Aladin Lite panel | Must | 2 | UI components and URL sync | A copied link reproduces the exact view; the embed works in an iframe |
| D1.5 | Two Opinions panel, Validation page, About/How-it-works | Must | 3 | Components reading `Opinions` and validation JSON | A non-astronomer can explain a verdict after reading it |
| D1.6 | Guided tour + Planet X Reality Check UI | Should | 4 | Tour steps, calculator UI using D4.5 functions | Tour < 2 min; calculator matches Shimaya's test values |
| D1.7 | Accessibility + sonified blink | Could | 4 | Keyboard map, ARIA, Web Audio sonification | Lighthouse a11y ≥ 90 |
| D1.8 | Submission package | Must | 5 | README draft, references compile | Every link works in incognito; submitted by internal deadline |

---

## Tirth — Data & Imaging (+ Pitch & Video owner)

**Mission:** turn NASA's raw SPHEREx files into clean, aligned, comparable frames and trustworthy brightness measurements, live, for any coordinates.

**Files you own:** `access.py`, `frames.py`, `stack.py`, `render.py`, `photometry.py`, `spectrum.py`, `tests/data/`.

| Code | Deliverable | Pri | Phase | AI produces | You verify (acceptance) |
| --- | --- | --- | --- | --- | --- |
| D2.1 | **Access:** TAP search (QR3 → QR2), epoch grouping, parallel cutouts with retries/timeouts, cache | Must | 0–1 | `access.py` + tests | Works for all 5 benchmarks and 3 random positions; you printed the **real** TAP column names before trusting the code |
| D2.2 | **Frame processing:** IMAGE − ZODI, flag masks (meanings read from header), wavelength at centre (spectral WCS key `W`), reprojection to a common north-up grid, shared stretch, WebP + flag PNG | Must | 1 | `frames.py`, `render.py` + tests | Stars sit still when blinking; wavelength labels match IRSA's Data Explorer for 3 frames |
| D2.3 | **Modes:** detector stacks (inverse-variance weighted, per epoch), difference, sum, colour composite | Must | 2 | `stack.py` + tests | Barnard's Star difference shows a +/− pair; WISE 0855 checked in D6 stacks |
| D2.4 | **Photometry engine** for spectra on the fly: ePSF fit (PSF cube for QR2, EPSF table for QR3) + aperture fallback, MJy/sr → µJy, flags/saturation per point; fast (parallel, tiny cutouts) | Must | 2 | `photometry.py`, `spectrum.py` (reusing xcavation ideas, credited) | V4: our flux vs IRSA's tool within 10% on 3 unsaturated stars; < 90 s per spectrum |
| D2.5 | Data-quality numbers per target (frames, epochs, detectors, flagged %, saturation) | Should | 3 | Small report function | Shown on the Validation page |
| — | **Pitch & video** (shared job you lead) | Must | 3–5 | Script draft from doc 08 | Final video recorded and uploaded with English subtitles |

**Watch out:** proper-motion targets need the propagated position (get it from Shivaansh's `resolve`); X-mirrored long-wavelength detectors (always use the WCS); `CRPIX1A/2A` for cutout → parent pixels; PSF vs EPSF by file version.

**Your CSV from IRSA's tool:** great as a format reference, but its target is below the noise (median S/N ≈ 0.1), so we don't train on it.

---

## Shivaansh — Motion & Orbits

**Mission:** know where every object really is at every moment, put the right catalog stars on every frame, and produce the **motion opinion**.

**Files you own:** `resolve.py`, `overlays.py`, `known.py`, `motion.py`.

| Code | Deliverable | Pri | Phase | AI produces | You verify (acceptance) |
| --- | --- | --- | --- | --- | --- |
| D3.1 | **Resolve + propagate:** name/coords → position, proper motion, parallax (SIMBAD/Gaia) → position at any MJD | Must | 0–1 | `resolve.py` + tests | Barnard's Star lands within 2″ of its SPHEREx image in a 2026 frame |
| D3.2 | **Overlays:** Gaia DR3 + AllWISE sources for a field, moved to each frame date; Aladin layer config | Must | 1–2 | `overlays.py` | Markers sit on stars in every benchmark frame |
| D3.3 | **Proper-motion fit** from SPHEREx epoch positions + Gaia/AllWISE epochs, with errors | Must | 2 | `motion.py` (stars) | V1: Barnard within 10% and 5°; V2: ε Indi B within 15% |
| D3.4 | **Known asteroids** in a frame (JPL SBIdent with SPHEREx's position, or SkyBoT) + asteroid rate → distance range; **V9** false-alarm test | Must (rate) / Should (overlay) | 3 | `known.py`, `motion.py` (asteroids) | V6: ≥ 10 asteroids matched within 1 px; V9: ≤ 2 false movers per shuffled field |
| D3.5 | **Mover search** on 2–3 ecliptic fields + fake-object recovery test | Could | 4 | Search script + plots | Recovery curve shown; candidates labelled honestly |

**Watch out:** SPHEREx is a spacecraft, not a ground observatory. For precise asteroid positions you need its location (header keys **\[VERIFY\]**). Gaia's epoch is 2016.0, not 2000.

---

## Shimaya — Spectral Science & ML (+ Science lead)

**Mission:** turn SPHEREx spectra into the **spectrum opinion** and the final **Two Opinions verdict**, and make sure every scientific claim in the app is true.

**Files you own:** `thermal.py`, `typing.py`, `verdict.py`, `notebooks/validation_*`, `docs/VALIDATION.md`.

| Code | Deliverable | Pri | Phase | AI produces | You verify (acceptance) |
| --- | --- | --- | --- | --- | --- |
| D4.1 | **Spectrum science layer:** assemble points, link simultaneous pairs (D1&4, D2&5, D3&6), rejection rules with plain reasons, plain-language flag legend; V4 comparison with IRSA's tool | Must | 1–2 | Functions + validation notebook | Spectra for ε Indi B and 2 unsaturated stars look right; rejected points explained |
| D4.2 | **Thermometer:** reflected + NEATM (`sbpy.thermal`), TR = D6/D3 (same exposure), fit → distance range or “can't tell” | Should | 3 | `thermal.py` + tests | V7 on ≥ 20 known bright asteroids (JPL r inside range ≥ 70%) or a documented fallback |
| D4.3 | **Typer:** template χ² match → spectral type → photometric distance | Must | 3 | `typing.py` + tests | V5: ε Indi B typed as T; distance within 30% of known |
| D4.4 | **Verdict engine:** rules from doc 04 → Agree / Disagree / Can't tell + confidence + plain reasons; optional ML scorer on real labelled objects only | Must (rules) / Could (ML) | 3 | `verdict.py` + tests | Every benchmark has a sensible verdict; reasons readable by a non-expert |
| D4.5 | **Planet X Reality Check physics** (brightness vs distance, motion between epochs) with test values | Should | 4 | Pure functions + tests | Reproduces published Planet Nine brightness estimates (doc 04 §6) |
| — | **Science fact-check** of the website text, video script and submission | Must | 3–5 | — | Every claim traceable to doc 04 or a source |

**About “ML”:** the core is fitting physics models to real data; that's what makes verdicts trustworthy. ML sits on top. **Never train on made-up data.**

---

## Everyone

- Keep `docs/REFERENCES.md` updated (every library, repo, dataset, image) and `docs/AI_USAGE.md` (which AI tool, for what).
- One PR per deliverable, branch `name/d2.2-frames`, with a real-data screenshot.
- Show your work at 10:30. Stuck > 2 h → ask.

## Learning links

- [SPHEREx intro tutorial](https://caltech-ipac.github.io/irsa-tutorials/spherex-intro/)
- [Cutouts tutorial](https://caltech-ipac.github.io/irsa-tutorials/spherex-cutouts/)
- [PSF tutorial](https://caltech-ipac.github.io/irsa-tutorials/spherex-psf/)
- [Source Discovery Tool demo](https://caltech-ipac.github.io/irsa-tutorials/spherex-source-discovery-tool-demo/)
- [SPHEREx data products](https://caltech-ipac.github.io/spherex-archive-documentation/spherex-data-products/)
- [xcavation (forced photometry)](https://zenodo.org/records/22260757)
- [spxquery docs](https://spxquery.readthedocs.io/en/latest/)
- [JPL SBIdent API](https://ssd-api.jpl.nasa.gov/doc/sb_ident.html)
- [sbpy](https://sbpy.readthedocs.io/en/latest/about.html)
- [Aladin Lite API](https://aladin.cds.unistra.fr/AladinLite/doc/API)
