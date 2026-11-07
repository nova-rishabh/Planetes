# Planetes 02 — TRD (Technical Design)

Nov 7, 2026 · v2 (final for build) · Read 01 PRD first. Exact JSON/API shapes live in 03 Data Contract & API Spec.

**Legend:** **\[VERIFY\]** = confirm in Phase 0 before relying on it. Everything else is backed by the sources at the bottom.

## 1. Architecture

```
            ┌──────────────────── Vercel: Hobby (always on, free)       ─────────────────────┐
 Browser ──▶ │ Next.js (static export) + TypeScript                                              │
            │  • Time-lapse player (canvas/WebGL2)   • Spectrum chart   • Two Opinions panel      │
            │  • Aladin Lite v3 context panel        • /public/data = pre-baked benchmark results  │
            └──────────────────────────────────────────┬───────────────────────────────────────┘
                                                       │ HTTPS (JSON + WebP)
            ┌───────────────── Render: Web Service Starter (Python 3.11, FastAPI) ────────────────┐
            │ /api/*  →  package `planetes` (shared with the offline bake scripts)             │
            │ resolve → epoch-propagate → TAP query → parallel cutouts → process → cache        │
            └──────┬────────────────────────────────────────────────────────────────────────┘
                   ▼                    ▼                       ▼                    ▼
          IRSA TAP / cutouts     CDS Sesame/SIMBAD       Gaia DR3 / AllWISE      JPL SBIdent/Horizons
          (SPHEREx QR3, QR2)     (name → position+PM)    (overlays)             (known asteroids, Should)
```

**Two paths, one codebase:**

- **Baked path (reliability):** a GitHub Action runs `python -m planetes bake --targets benchmarks` and commits results to `web/public/data/`. The five official targets always load instantly, even if the API is asleep or IRSA is slow during judging.
- **Live path (the challenge's core):** any coordinates → the API does the same steps on demand and streams results to the browser.

## 2. Hosting (decided)

| Piece | Host | Why |
| --- | --- | --- |
| **Website** (Next.js) | **Vercel Hobby (free)** | Best Next.js host; global CDN, always on, automatic preview link for every pull request |
| **API** (FastAPI, Python) | **Render Web Service Starter** (team has credits) | Never sleeps, 0.5 CPU / 512 MB; long-running jobs are fine (Vercel's serverless functions have time limits, so the API stays on Render) |
| Baked benchmark data | Inside the website (`web/public/data`) | Loads instantly even if the API is busy |

**Decision:** web on Vercel (free), API on Render Starter (paid from team credits, no sleep). Render's disk is temporary, so the cache is best effort (lost on redeploy). That's acceptable. If the API ever needs more memory, move to Render Standard (2 GB).

**Deploy:** `Vercel project linked to web/; one render.yaml Blueprint for the API`. API health check `/api/health`. Env vars: `ALLOWED_ORIGINS`, `MAX_FRAMES`, `IRSA_CONCURRENCY`, `CACHE_DIR`. CORS allows only our site origin.

## 3. SPHEREx facts the code depends on

- **Releases:** QR1 retired (Feb 2026). **QR2** (Oct 2025 onward) and **QR3** (Sep 2026 onward), with weekly additions. SIA collections: `spherex_qr3`, `spherex_qr2` (plus `_deep`). **Query QR3 first, fall back to QR2, and record the release on every frame.**
- **One file per detector per pointing (6 per pointing, about 70 MB each).** Some pointings lack some detectors. **Always use cutouts.**
- **Multi-extension FITS:** `IMAGE` (MJy/sr, zodi NOT subtracted), `FLAGS` (bitmap; meanings in header `MP_*` keys), `VARIANCE`, `ZODI` (model to subtract), PSF data, `WCS-WAVE` (wavelength lookup).
- **PSF format changed:** files with `VERSION` < 7.0 have a `PSF` cube (11×11 grid, 121 PSFs, 101×101, 10× oversampled). **Version ≥ 7.0 (QR3) has an `EPSF` binary table** (one row per zone, e.g. 441 zones on a 21×21 grid; 33×33 arrays, 5× oversampled; columns `XCENTER`, `YCENTER`, `CWAVE`, `EPSF`…). Pick the zone nearest the source in **parent-image** pixels, using `CRPIX1A`/`CRPIX2A` from the cutout. Don't pass the oversampled PSF straight to fitting tools: shift, integrate onto the native pixel grid, then normalise.
- **Wavelength per pixel:** `WCS(header, fobj=hdul, key="W")`, set `.sip = None`, then `pixel_to_world(x, y)` → (wavelength, bandwidth). The normal WCS (no key) gives sky position.
- **Bands / detectors:**

  | Detector | Range (µm) | R | Same sky at the same moment as |
  | --- | --- | --- | --- |
  | D1 | 0.75–1.09 | \~39 | D4 |
  | D2 | 1.10–1.62 | \~41 | D5 |
  | D3 | 1.63–2.41 | \~41 | D6 |
  | D4 | 2.42–3.82 | \~35 | D1 |
  | D5 | 3.83–4.41 | \~112 | D2 |
  | D6 | 4.42–5.00 | \~128 | D3 |
- **Geometry:** pixels about 6.15–6.2″; each detector covers 3.5°×3.5°; exposures about 112.5 s; 11.8′ steps between exposures in a group.
- **Sensitivity (single visit, 5σ, pre-launch):** about AB 18.5–19 at 0.75–3.8 µm and 16.6–18 at 3.8–5 µm.
- **Saturation:** roughly AB 11.7 (short) to 9.7 (long). Barnard's Star, R Draconis and probably RW Aurigae saturate. Show flags; never present saturated photometry as valid.
- **Coverage:** whole sky every \~6 months since May 2025, so most positions have about 3 survey passes by now, with extra visits days apart where scans overlap, and far more near the ecliptic poles.

## 4. Gotchas that break naive code (put these in every AI prompt)

1. **Proper motion:** J2000 coordinates of fast stars are wrong today. Barnard's Star moves \~10.4″/yr (about 4.5′ since 2000). Propagate positions to each frame's date with `SkyCoord.apply_space_motion`.
2. **Pixel conventions:** FITS header values are 1-based; numpy/astropy are 0-based. Cutout → parent pixel conversion uses `CRPIX1A`/`CRPIX2A`.
3. **Long-wavelength detectors are mirrored in X** relative to short-wavelength ones (`DETCOORD` note). Always go through the WCS; never assume orientation.
4. **Different orientation and wavelength per frame.** Reproject every frame to one north-up grid before blinking, and label each frame's wavelength.
5. **Subtract `ZODI`** before display, stacking or photometry.
6. **Read flag meanings from the header**, not from a hard-coded table, and keep the raw bitmask in outputs.
7. **Bright-star artifacts:** saturation cores, charge bloom rings, and an inverted “ghost” 32 rows away in Band 1. Expect fake “movers” near bright stars.
8. **SIA lags ingestion by about a day; TAP is immediate.** Use TAP for discovery.
9. **Remote reads time out:** set `astropy.utils.data.conf.remote_timeout = 120` and retry with backoff.
10. **Units:** MJy/sr → µJy needs the pixel solid angle. Prefer IRSA's solid-angle pixel map calibration product over a constant **\[VERIFY\]**.

## 5. Live request flow

1. **Resolve:** name → position and proper motion (CDS Sesame / SIMBAD via astroquery). Plain coordinates skip this.
2. **Find frames (TAP):** `spherex.artifact` JOIN `spherex.plane`, `CONTAINS(POINT(ra,dec), p.poly)`, optional detector filter `energy_bandpassname = 'SPHEREx-D{n}'`, order by `time_bounds_lower`. **\[VERIFY\]** table and column names for QR3.
3. **Plan:** group frames into **epochs** (gap > 30 days starts a new epoch) and by detector. Cap at `MAX_FRAMES` (default 60) for display. The spectrum job uses all frames.
4. **Fetch cutouts** in parallel (≤ 8 at once, retries, 120 s timeout): `…fits?center={ra},{dec}d&size={deg}`. Display FOV from the user (default 0.1° = 6′). Spectrum cutouts are tiny (\~0.02°).
5. **Process each frame:** IMAGE − ZODI → mask chosen flag bits → wavelength at centre → **reproject** onto a common north-up TAN grid (`reproject.reproject_interp`, pixel scale \~3″ for smooth display) → store float32 array + variance.
6. **Modes:**
   - exposures (as is)
   - **detector stacks** (inverse-variance-weighted mean of frames in the same epoch and detector, flagged pixels excluded)
   - **difference** (stack epoch B − stack epoch A, same detector; noise from variances)
   - **sum** (all epochs, per detector)
   - **colour** (D1+D2 → blue, D3+D4 → green, D5+D6 → red)
7. **Render:** one shared stretch per view (percentile or asinh) → WebP (Pillow). Also return a small flag-mask PNG per frame.
8. **Respond progressively:** create a job, return `job_id`, and the browser polls (or uses Server-Sent Events) and shows frames as they arrive.
9. **Cache** by hash of the request parameters (disk, best effort).

## 6. Spectra on the fly

- For the clicked position (propagated to each frame's date if the object has proper motion): tiny cutouts from every frame → **forced photometry**.
- Preferred method: fit the ePSF at the exact sub-pixel position plus a smooth background. That's the same approach IRSA's Spectrophotometry Tool uses.
- Fallback: aperture photometry (radius 2–3 px, local annulus).
- Each point records wavelength, bandwidth, flux µJy, error, time, detector, flags, and the simultaneous-pair ID (D1&4, D2&5, D3&6).
- **Reuse rather than reinvent:** `xcavation` (MIT; fast SPHEREx QR2 forced photometry, aperture + PSF, multithreaded) and the method in `obsutils.spherex`. Check that both work with QR3.
- **Cross-check:** IRSA's own Spectrophotometry Tool (it uses The Tractor, but takes minutes to hours per source) for 2–3 objects offline.

## 7. Overlays

- **Gaia DR3** (VizieR `I/355/gaiadr3` or `astroquery.gaia`) and **AllWISE** (`II/328/allwise` or IRSA TAP `allwise_p3as_psd`). Return positions moved to each frame's epoch (Gaia's epoch is 2016.0).
- **Aladin Lite v3 context panel:** HiPS `CDS/P/SPHEREx/QR2/D1` … `D6` (SPHEREx all-sky per detector), unWISE colour, DSS2 colour; VizieR catalogue layers. **\[VERIFY\]** the exact unWISE HiPS ID in Aladin's HiPS list.
- **Known asteroids/comets (Should):** JPL SBIdent using SPHEREx's own position as observer **\[VERIFY header keys\]**, or IMCCE SkyBoT with a geocentric observer for a quick approximation.

## 8. Two Opinions engine

See doc 04 for the physics and thresholds. Modules:

- `motion.py` (proper-motion fit; asteroid rate → distance range)
- `thermal.py` (reflected + NEATM via `sbpy.thermal`)
- `typing.py` (template match to SPHEREx brown-dwarf/star spectra)
- `verdict.py` (rules first, optional scikit-learn scorer trained only on real labelled objects)

## 9. Repository layout

```
planetes/
├─ AGENTS.md                 # rules for AI coding agents (see doc 07)
├─ render.yaml               # Render Blueprint: API only (web is on Vercel)
├─ contracts/                # JSON Schemas (source of truth) + generated types
├─ pipeline/                 # Python package `planetes` (pyproject.toml)
│  ├─ src/planetes/
│  │  ├─ resolve.py  access.py  frames.py  stack.py  render.py
│  │  ├─ photometry.py  spectrum.py  overlays.py  known.py
│  │  ├─ motion.py  thermal.py  typing.py  verdict.py
│  │  └─ bake.py  cli.py  cache.py
│  └─ tests/                   # pytest; small real FITS fixtures in tests/data (< 5 MB total)
├─ api/                      # FastAPI app importing `planetes`
├─ web/                      # Next.js app; web/public/data = baked outputs
├─ notebooks/                # exploration only
├─ docs/                     # REFERENCES.md, AI_USAGE.md, VALIDATION.md, DATA_NOTES.md
└─ .github/workflows/        # ci.yml (lint + tests + contract check), bake.yml (weekly + manual)
```

**Ownership** (AI agents must not edit outside their owner's area without a PR review):

| Area | Owner |
| --- | --- |
| `web/`, `api/`, `contracts/`, `render.yaml`, CI | Rishabh |
| `access.py`, `frames.py`, `stack.py`, `render.py`, `photometry.py`, `spectrum.py` | Tirth |
| `resolve.py`, `overlays.py`, `known.py`, `motion.py` | Shivaansh |
| `thermal.py`, `typing.py`, `verdict.py`, validation notebooks | Shimaya |

## 10. Tech stack

| Layer | Choice |
| --- | --- |
| Pipeline | Python 3.11, astropy, astroquery, pyvo, numpy, scipy, photutils, reproject, Pillow, sbpy, scikit-learn, pydantic v2, pytest |
| API | FastAPI + uvicorn; background jobs via asyncio + thread pool; httpx for HTTP |
| Web | Next.js (App Router, static export), TypeScript, Tailwind or CSS modules; canvas/WebGL2 player; uPlot or Observable Plot for spectra; Aladin Lite v3 from CDN |
| Fonts | **Not Inter.** E.g. Space Grotesk / IBM Plex Sans + IBM Plex Mono (design doc to follow) |
| CI/CD | GitHub Actions; Vercel auto-deploys `web/` (preview link per PR); Render auto-deploys the API from `main` |

## 11. Open-source building blocks (credit every one)

| Project | Use | License |
| --- | --- | --- |
| astropy, astroquery, photutils, reproject, pyvo | Core astronomy infrastructure | BSD-3 |
| xcavation (Brooks, Cushing, Kothari) | Fast SPHEREx forced photometry | MIT |
| spxquery (Wenke Ren) | Reference for TAP queries, cutouts, flag handling, light curves | **\[VERIFY\]** |
| obsutils `spherex` module (R. Stein) | Reference method for ePSF forced photometry | **\[VERIFY\]** |
| IRSA SPHEREx tutorials (intro, cutouts, PSF, Source Discovery Tool) | Patterns for access, PSF zones, D2−D4 red-source subtraction | **\[VERIFY\]** |
| sbpy (`sbpy.thermal`) | NEATM thermal model | BSD-3 |
| Aladin Lite v3 (CDS) | Sky context panel | **\[VERIFY\]** (GPL-3 expected) |
| CDS HiPS: SPHEREx D1–D6, unWISE, DSS2 | Context imagery | per HiPS licence (ODbL for CDS-built SPHEREx HiPS) |
| Gaia DR3, AllWISE | Overlays and proper motions | ESA / NASA open data |
| SPHEREx ultracool-dwarf templates (Gagné et al. 2026, mocadb.ca) | Brown-dwarf typing | **\[VERIFY\]** terms |

**Not reused:** code from other Space Apps 2026 teams.

## 12. Performance budgets

- Baked benchmark view: first frame < 1.5 s, full set < 3 s.
- Live view (Starter instance): first frame < 15 s, 30 frames < 60 s; progress shown throughout.
- Live spectrum: < 90 s for \~150 frames (tiny cutouts, 8 parallel); cached afterwards.
- API memory < 400 MB: process frame by frame in float32; don't hold full files.
- Each WebP ≤ 150 KB.

## 13. Testing

- **Unit (pytest):** coordinate propagation, pixel conventions, unit conversion, epoch grouping, stacking maths, difference noise, flag parsing.
- **Fixture tests on real data:** 2–3 tiny real SPHEREx cutouts committed in `tests/data`. No synthetic data pretending to be real.
- **Contract tests:** every API response and baked file validates against `/contracts`.
- **Science validation:** doc 04 lists every check and its pass threshold.
- **Web:** Playwright smoke test (five benchmarks load, URL round-trip, embed page); Lighthouse ≥ 90 for performance and accessibility.

## 14. Risks and fallbacks

| Risk | Fallback |
| --- | --- |
| IRSA slow or down during judging | Baked benchmarks; clear “NASA archive busy” message; cached results |
| API too slow under load | Already on Starter; move to Standard (2 GB) if needed; reduce `MAX_FRAMES`; lower display resolution |
| QR3 schema differences | Fall back to QR2; release-specific adapters |
| Saturated benchmarks | Show flags and explain; validate photometry on non-saturated stars instead |
| Thermometer fails on real data | Spectrum opinion falls back to “colour class only” |
| WISE 0855 too faint in single frames | Detector-6 stacks; honest “below single-frame limit” note |

## Sources

- [IRSA SPHEREx page](https://irsa.ipac.caltech.edu/Missions/spherex.html)
- [SPHEREx QR overview](https://irsa.ipac.caltech.edu/data/SPHEREx/docs/overview_qr.html)
- [SPHEREx data products (archive guide)](https://caltech-ipac.github.io/spherex-archive-documentation/spherex-data-products/)
- [Intro tutorial](https://caltech-ipac.github.io/irsa-tutorials/spherex-intro/)
- [Cutouts tutorial](https://caltech-ipac.github.io/irsa-tutorials/spherex-cutouts/)
- [PSF tutorial](https://caltech-ipac.github.io/irsa-tutorials/spherex-psf/)
- [Source Discovery Tool demo](https://caltech-ipac.github.io/irsa-tutorials/spherex-source-discovery-tool-demo/)
- [Spectrophotometry Tool docs](https://irsa.ipac.caltech.edu/onlinehelp/spherex/spherex/sp.html)
- [Cutout capabilities](https://irsa.ipac.caltech.edu/data/SPHEREx/docs/cutout_tool.html)
- [SPHEREx instrument paper](https://arxiv.org/pdf/2404.11017)
- [SPHEREx Ices overview (simultaneous pairs)](https://arxiv.org/pdf/2603.22135)
- [SPHEREx artifact bestiary](https://arxiv.org/pdf/2608.09862)
- [Saturation limits (POKEMON-DLC)](https://arxiv.org/pdf/2604.22983)
- [xcavation](https://zenodo.org/records/22260757)
- [spxquery](https://spxquery.readthedocs.io/en/latest/)
- [obsutils SPHEREx PR](https://github.com/robertdstein/obsutils/pull/4)
- [CDS SPHEREx HiPS (D1)](https://alasky.cds.unistra.fr/SPHEREx/D1/properties)
- [Aladin Lite API](https://aladin.cds.unistra.fr/AladinLite/doc/API)
- [Render free tier](https://render.com/free)
- [Render pricing (2026)](https://temps.sh/blog/render-pricing-2026)
