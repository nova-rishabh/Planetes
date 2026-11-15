# Planetes 03 — Data Contract & API Spec

v1.0 · **The single source of truth for how the pieces talk to each other.** Paste the relevant section into every AI coding prompt. Changes only by pull request reviewed by Rishabh.

## 1. Rules for every payload

- `schema_version` at the top of every response and baked file (start at `"1.0"`).
- **Units in the name** (`flux_ujy`, `wavelength_um`, `fov_deg`, `pm_ra_masyr`) or an explicit `unit` field. Angles in degrees unless the name says otherwise. Times as MJD (float) **and** ISO-8601 UTC string.
- **`null` means “not measured.”** Never fill a guess, a demo value or zero.
- Every measurement carries **provenance**: SPHEREx `obs_id` (the IVOA publisher DID), release (`QR2`/`QR3`), and `code_version` (git short hash).
- IDs are stable strings. Frame IDs = sha1 of `obs_id + cutout params`, first 12 hex chars.
- JSON Schemas live in `contracts/*.schema.json`. Python pydantic models and TypeScript types are **generated** from them. Never hand-edit the generated files.

## 2. Web URL parameters (shareable + embeddable)

| Param | Example | Meaning |
| --- | --- | --- |
| `target` | `barnard` | One of the baked benchmark IDs (`barnard`, `wise0855`, `epsindib`, `rwaur`, `rdra`) |
| `ra`, `dec` | `133.7951`, `-7.2451` | Degrees (ICRS). Sexagesimal is also accepted in the input box. |
| `fov` | `0.1` | Field of view in degrees (0.03–0.5) |
| `mode` | `stacks` | `exposures` \| `stacks` \| `difference` \| `sum` \| `color` |
| `det` | `1,2,6` | Detectors to include |
| `frame` | `7` | Index of the frame on screen |
| `a`,`b` | `0`,`2` | Epochs for blink / difference |
| `stretch` | `asinh` | `linear` \| `asinh` \| `log`, with optional `lo`,`hi` |
| `ov` | `gaia,allwise,flags` | Overlays on |
| `obj` | `133.7953,-7.2449` | Selected object (opens spectrum + Two Opinions) |

Routes: `/` (app), `/embed` (same params, minimal chrome, for iframes), `/about`, `/validation`, `/tour`.

## 3. API endpoints (FastAPI, base `/api`)

| Method & path | Purpose | Returns |
| --- | --- | --- |
| `GET /health` | Liveness + upstream check | `Health` |
| `GET /resolve?q=Barnard's Star` | Name → position + proper motion | `Resolved` |
| `POST /timelapse` | Start a time-lapse job | `{ job_id }` |
| `POST /spectrum` | Start a spectrum job | `{ job_id }` |
| `GET /jobs/{job_id}` | Poll job status and partial results | `Job` |
| `GET /frames/{frame_id}.webp` | Rendered frame image | image/webp |
| `GET /frames/{frame_id}/flags.png` | Flag overlay (transparent PNG) | image/png |
| `GET /overlays?ra&dec&fov_deg&mjd=…&catalogs=gaia,allwise` | Catalog sources moved to each date | `Overlays` |
| `POST /opinions` | Two Opinions for one object | `Opinions` |
| `GET /known_sso?frame_id=` (Should) | Known asteroids/comets in a frame | `KnownSSO` |

**Errors:** HTTP 4xx/5xx with `{ "error": { "code": "IRSA_TIMEOUT", "message": "…", "hint": "…" } }`. Codes: `BAD_INPUT`, `NOT_FOUND`, `NO_COVERAGE`, `IRSA_TIMEOUT`, `IRSA_ERROR`, `TOO_LARGE`, `INTERNAL`.

**Limits:** `fov_deg` ≤ 0.5; `max_frames` ≤ 120; ≤ 8 parallel IRSA requests per job; ≤ 3 concurrent jobs per client IP.

## 4. Request bodies

```json
// POST /api/timelapse
{ "ra": 269.4521, "dec": 4.6934, "fov_deg": 0.1,
  "mode": "stacks", "detectors": [1,2,3,4,5,6],
  "release": "auto",                 // auto = QR3 then QR2
  "mjd_start": null, "mjd_end": null, "max_frames": 60,
  "pm": { "pm_ra_masyr": -801.5, "pm_dec_masyr": 10362.4, "ref_epoch_jyear": 2016.0 } // optional; numbers here are illustrative, take real ones from /resolve
}

// POST /api/spectrum
{ "ra": 133.7951, "dec": -7.2451, "release": "auto", "method": "auto",   // auto = PSF, fallback aperture
  "pm": null }

// POST /api/opinions
{ "ra": 330.8, "dec": -56.8, "spectrum_job_id": "j_…", "pm": null }
```

## 5. Response shapes

```json
// Health
{ "schema_version": "1.0", "status": "ok", "code_version": "a1b2c3d",
  "irsa_tap": "ok|slow|down", "default_release": "QR3", "cache_entries": 42 }

// Resolved
{ "schema_version": "1.0", "query": "Barnard's Star", "name": "Barnard's Star",
  "ra": 269.4521, "dec": 4.6934, "ref_epoch_jyear": 2016.0,
  "pm_ra_masyr": null, "pm_dec_masyr": null, "parallax_mas": null,
  "source": "SIMBAD via CDS Sesame" }

// Job
{ "schema_version": "1.0", "job_id": "j_…", "kind": "timelapse|spectrum",
  "status": "queued|running|done|error",
  "progress": { "done": 12, "total": 48, "stage": "fetching cutouts" },
  "result": { /* TimelapseResult or SpectrumResult, partial while running */ },
  "error": null }

// TimelapseResult
{ "schema_version": "1.0",
  "request": { /* echo of the POST body */ },
  "grid": { "projection": "TAN", "crval_deg": [269.45, 4.69], "crpix": [60.5, 60.5],
            "cdelt_deg": 0.000833, "naxis": [120, 120], "north_up": true },
  "epochs": [ { "index": 0, "mjd_start": 60794.2, "mjd_end": 60801.9, "n_frames": 14 } ],
  "frames": [ {
      "id": "f_3a9c1e0b7d22", "kind": "exposure|stack|difference|sum|color",
      "obs_id": "ivo://irsa.ipac/spherex_qr2?2026W16_2A_0120_3/D1",  // null for stacks; see members
      "members": [],                       // obs_ids combined into this frame (stacks)
      "release": "QR2", "epoch_index": 0,
      "mjd": 61147.13, "utc": "2026-04-16T03:07:09Z",
      "detector": 1, "wavelength_um": 0.745, "bandwidth_um": 0.018,
      "image_url": "/api/frames/f_3a9c1e0b7d22.webp",
      "flags_url": "/api/frames/f_3a9c1e0b7d22/flags.png",
      "flagged_frac": 0.012, "saturated_near_center": false,
      "target_xy": [60.1, 59.8],           // where the (propagated) target falls on the grid
      "notes": [] } ],
  "stretch": { "method": "asinh", "lo": -0.02, "hi": 0.9, "unit": "MJy/sr" },
  "flag_legend": [ { "bit": 1, "name": "OVERFLOW", "plain": "Pixel saturated by a bright source" } ],
  "provenance": { "tap_query": "SELECT …", "generated_utc": "…", "code_version": "a1b2c3d" } }

// SpectrumResult
{ "schema_version": "1.0", "target": { "ra": 133.7951, "dec": -7.2451, "pm": null },
  "points": [ { "obs_id": "ivo://…/D6", "mjd": 61140.2, "detector": 6,
                "wavelength_um": 4.61, "bandwidth_um": 0.036,
                "flux_ujy": null, "flux_err_ujy": null,       // null until measured
                "snr": null, "flags": 0, "saturated": false, "used": true,
                "reject_reason": null, "pair_id": "p_…", "method": "psf",
                "ra": 133.7953, "dec": -7.2449 } ],
  "summary": { "n_points": 0, "n_used": 0, "n_rejected": 0, "bands_covered": [] },
  "provenance": { "release": "QR3", "code_version": "a1b2c3d" } }

// Overlays
{ "schema_version": "1.0", "catalogs": [ {
    "name": "Gaia DR3", "vizier": "I/355/gaiadr3", "ref_epoch_jyear": 2016.0,
    "sources": [ { "id": "…", "ra": 0.0, "dec": 0.0, "pm_ra_masyr": null, "pm_dec_masyr": null,
                   "mag": null, "band": "G",
                   "at_mjd": { "61147.13": [0.0, 0.0] } } ] } ] }

// Opinions
{ "schema_version": "1.0", "object": { "ra": 0.0, "dec": 0.0 },
  "motion": { "kind": "proper_motion|sso_rate|static|unknown",
              "value": null, "unit": "arcsec/yr|arcsec/hr", "err": null, "pa_deg": null,
              "distance": { "lo": null, "hi": null, "unit": "pc|au" },
              "truth": { "value": null, "source": null },
              "quality": "good|fair|poor", "method": "…" },
  "spectrum": { "kind": "template|thermal|none", "class": null,
                "temperature_k": null, "distance": { "lo": null, "hi": null, "unit": "pc|au" },
                "quality": "good|fair|poor", "method": "…" },
  "verdict": { "label": "agree|disagree|cant_tell", "class": "nearby_star|brown_dwarf|asteroid|variable|artifact|unknown",
               "confidence": null, "reasons": [] } }
```

The numbers inside these examples only show the shape. They are **not results** and must never be copied into the app.

## 6. Baked static files (web/public/data)

```
data/index.json                         # list of baked targets + build info
data/targets/{id}/target.json           # Resolved + description + links
data/targets/{id}/timelapse_{mode}.json # TimelapseResult, image_url pointing to ./frames/
data/targets/{id}/frames/*.webp, *.png
data/targets/{id}/spectrum.json         # SpectrumResult
data/targets/{id}/overlays.json         # Overlays
data/targets/{id}/opinions.json         # Opinions
data/validation/*.json                  # inputs for the Validation page plots
```

The web app treats baked files and live API responses **identically**. Only the base URL differs.

## 7. Benchmark IDs

| ID | Name | Notes for the bake |
| --- | --- | --- |
| `barnard` | Barnard's Star | Must propagate position; saturated, show flags |
| `wise0855` | WISE 0855−0714 | Faint below \~3.5 µm; detector-6 stacks |
| `epsindib` | ε Indi Ba/Bb | Unresolved binary; bright ε Indi A \~7′ away |
| `rwaur` | RW Aurigae | Variable; doesn't move |
| `rdra` | R Draconis | Mira variable, \~245-day period; doesn't move; likely saturated |

## 8. Change log

- 1.0: first version.
