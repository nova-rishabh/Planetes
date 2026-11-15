"""V3: WISE 0855−0714 detection and motion in the SPHEREx frames themselves (docs/04 §7).

Pass mark (docs/04 §7): ≥ 5σ in at least one D6 frame, or an honest non-detection; if detected, μ within 20 % of
8.15″/yr.

Run: python pipeline/notebooks/v3_wise0855_motion.py   (needs IRSA's TAP search)
Output: docs/evidence/v3_wise0855_motion.csv (one row per frame) and a summary on stdout.

The rule below was fixed before the first run.
- Frames: SPHEREx D6 exposures within 0.1° of WISE 0855 (it is almost invisible below 3.5 µm).
- Blend: a Gaia DR3 star (G 16.3) sits 5–9″ from WISE 0855 during the SPHEREx year, inside one SPHEREx pixel. A frame is
  used only if no catalogued Gaia star brighter than the app's blend limit is inside the measuring circle at that
  frame's date (spectrum.blend_reason); otherwise the neighbour's light would pull the centroid.
- Position: motion.measure_position with a 5σ peak threshold around the catalogue-predicted pixel for each date.
- Motion: fitted only if ≥ 3 unblended detections span ≥ 0.5 yr; then compared with 8.15″/yr (pass if within 20 %).
- Otherwise the result is reported as a detection without a usable motion, or as a non-detection. Both are allowed
  outcomes and are written down as they come out.
"""

from __future__ import annotations

import csv
from pathlib import Path

from planetes.access import fetch_cutouts, find_frames
from planetes.motion import fit_proper_motion, measure_position
from planetes.resolve import position_at, resolve
from planetes.spectrum import blend_reason, neighbours_near

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "evidence" / "v3_wise0855_motion.csv"
TRUTH_ARCSEC_YR = 8.15
PASS_FRAC = 0.20
MIN_DETECTIONS = 3
MIN_BASELINE_YR = 0.5


def main() -> None:
    target = resolve("WISE J085510.83-071442.5")
    mid = position_at(target, 61000.0)
    neighbours = neighbours_near(float(mid.ra.deg), float(mid.dec.deg))
    frames = find_frames(float(mid.ra.deg), float(mid.dec.deg), size_deg=0.1)
    frames = frames[frames["detector"] == 6]
    blobs = fetch_cutouts(frames, max_concurrent=4)
    rows, detections = [], []
    for _, fr in frames.sort_values("mjd").iterrows():
        data = blobs.get(f"cutouts/{fr['frame_id']}.fits")
        if data is None:
            continue
        pred = position_at(target, float(fr["mjd"]))
        blend = blend_reason(float(pred.ra.deg), float(pred.dec.deg), neighbours)
        m = (
            None
            if blend
            else measure_position(data, float(fr["mjd"]), float(pred.ra.deg), float(pred.dec.deg), min_snr=5.0)
        )
        rows.append(
            {
                "obs_id": fr["obs_id"],
                "mjd": round(float(fr["mjd"]), 5),
                "blended": blend or "",
                "detected_5sigma": m is not None,
                "ra_deg": None if m is None else round(m.ra_deg, 7),
                "dec_deg": None if m is None else round(m.dec_deg, 7),
                "offset_from_prediction_px": None if m is None else round(m.offset_px, 3),
            }
        )
        if m is not None:
            detections.append(m)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]) if rows else ["obs_id"])
        w.writeheader()
        w.writerows(rows)

    n_blend = sum(1 for r in rows if r["blended"])
    print(f"D6 frames: {len(rows)}, blended with a Gaia star: {n_blend}, unblended 5σ detections: {len(detections)}")
    if not detections:
        print("V3: honest non-detection in unblended D6 frames (allowed outcome; no motion claimed)")
    elif len(detections) < MIN_DETECTIONS:
        print("V3: detected, but too few unblended detections to fit a motion (no motion claimed)")
    else:
        fit = fit_proper_motion(
            [m.mjd for m in detections], [m.ra_deg for m in detections], [m.dec_deg for m in detections]
        )
        err = abs(fit.mu_arcsec_yr - TRUTH_ARCSEC_YR) / TRUTH_ARCSEC_YR
        print(
            f"mu = {fit.mu_arcsec_yr:.2f} ± {fit.mu_err_arcsec_yr:.2f} ″/yr, PA {fit.pa_deg:.1f}°, "
            f"baseline {fit.time_baseline_yr:.2f} yr; reference 8.15 ″/yr -> difference {100 * err:.1f} %"
        )
        ok = fit.time_baseline_yr >= MIN_BASELINE_YR and err < PASS_FRAC
        print("V3 motion", "PASS" if ok else "NOT PASSED")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
