"""V2: ε Indi B proper motion measured in the SPHEREx frames themselves (docs/04 §7: within 15 % of Gaia's ~4.7″/yr).

Run: python pipeline/notebooks/v2_epsindib_motion.py   (needs IRSA's TAP search to find and fetch the frames)
Output: docs/evidence/v2_epsindib_motion.csv (one row per frame) and a summary on stdout.

The rule below was fixed before the first run.
- Frames: every SPHEREx exposure IRSA lists within 0.1° of ε Indi B, all detectors.
- Position in each frame: motion.measure_position, a 2-D Gaussian centroid in a 7x7 stamp around the Gaia-predicted
  pixel for that date. Frames where the core is flagged or saturated, or the peak is under 10 sigma, are dropped.
  The Gaia prediction only says where to look; the fitted motion uses the measured positions alone.
- Fit: motion.fit_proper_motion on the measured positions (no Gaia epoch point added).
- Pass: |mu - Gaia| / Gaia < 15 %, with at least 6 measured frames spanning at least 0.5 yr.
"""

from __future__ import annotations

import csv
from pathlib import Path

from planetes.access import fetch_cutouts, find_frames
from planetes.motion import fit_proper_motion, measure_position
from planetes.resolve import position_at, resolve

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "evidence" / "v2_epsindib_motion.csv"
MIN_FRAMES = 6
MIN_BASELINE_YR = 0.5
PASS_FRAC = 0.15


def main() -> None:
    target = resolve("eps Ind B")
    truth = float(((target.pm_ra_masyr or 0.0) ** 2 + (target.pm_dec_masyr or 0.0) ** 2) ** 0.5) / 1000.0
    here = position_at(target, 61000.0)
    frames = find_frames(float(here.ra.deg), float(here.dec.deg), size_deg=0.1)
    blobs = fetch_cutouts(frames, max_concurrent=8)
    rows, measured = [], []
    for _, fr in frames.sort_values("mjd").iterrows():
        data = blobs.get(f"cutouts/{fr['frame_id']}.fits")
        if data is None:
            continue
        pred = position_at(target, float(fr["mjd"]))
        m = measure_position(data, float(fr["mjd"]), float(pred.ra.deg), float(pred.dec.deg))
        rows.append(
            {
                "obs_id": fr["obs_id"],
                "mjd": round(float(fr["mjd"]), 5),
                "detector": int(fr["detector"]),
                "measured": m is not None,
                "ra_deg": None if m is None else round(m.ra_deg, 7),
                "dec_deg": None if m is None else round(m.dec_deg, 7),
                "offset_from_prediction_px": None if m is None else round(m.offset_px, 3),
            }
        )
        if m is not None:
            measured.append(m)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]) if rows else ["obs_id"])
        w.writeheader()
        w.writerows(rows)

    print(f"frames: {len(rows)}, measured: {len(measured)}")
    if len(measured) < 2:
        print("V2 NOT PASSED: too few measured positions")
        return
    fit = fit_proper_motion([m.mjd for m in measured], [m.ra_deg for m in measured], [m.dec_deg for m in measured])
    err = abs(fit.mu_arcsec_yr - truth) / truth
    print(
        f"mu = {fit.mu_arcsec_yr:.3f} ± {fit.mu_err_arcsec_yr:.3f} ″/yr, PA {fit.pa_deg:.1f}°, "
        f"baseline {fit.time_baseline_yr:.2f} yr, reduced chi2 {fit.reduced_chi2:.2f}"
    )
    print(f"Gaia DR3: {truth:.3f} ″/yr  -> difference {100 * err:.1f} %")
    ok = len(measured) >= MIN_FRAMES and fit.time_baseline_yr >= MIN_BASELINE_YR and err < PASS_FRAC
    print("V2", "PASS" if ok else "NOT PASSED")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
