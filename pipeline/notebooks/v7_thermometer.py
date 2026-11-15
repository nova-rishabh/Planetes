"""V7: does the asteroid thermometer put real known asteroids at their JPL distance from the Sun?

Run: .venv/Scripts/python.exe pipeline/notebooks/v7_thermometer.py
Output: docs/evidence/v7_thermometer.csv (one row per asteroid) and a summary on stdout.

The rule below was fixed before the first run and is not tuned afterwards.

Frames. Ecliptic fields (20, every 18 deg in RA), 0.4 deg cutouts, detectors D3 and D6 only. D3 and D6 of one
exposure see the same sky at the same moment (spectrum.pair_id). Up to 40 D3 exposures per field, spread in time.

Asteroids. JPL SBIdent on each D3 frame, from SPHEREx's own position (known.py), V <= 17.5 (as in V6). The same
JPL RA/Dec is used in the D6 frame of that exposure. Fluxes come from the app's own forced aperture photometry
(photometry.measure) and its own point rules (spectrum.reject_reason: no flags, not saturated, S/N >= 3); a point
is also dropped when a Gaia star brighter than the app's blend limit sits close (spectrum.blend_reason).

Test. Points are grouped by asteroid across exposures and passed to the app's own thermal.thermal_opinion, which
needs at least 2 usable D3/D6 pairs. An asteroid is tested when it has at least 2 usable pairs. For each tested
asteroid the true heliocentric distance r comes from JPL Horizons at the mean time of its pairs. A hit is r inside
the thermometer's [lo, hi] range; a 'none' opinion on a tested asteroid counts as a miss.
Pass (docs/04 §7 V7): at least 20 tested asteroids and hits >= 70 %. Fewer than 20 tested means not passed yet.
The median range width and the good/fair/poor counts are reported next to the result, so wide ranges stay visible.
"""

from __future__ import annotations

import csv
import io
import math
import re
import warnings
from collections import defaultdict
from pathlib import Path

import numpy as np
from astropy.io import fits
from astropy.time import Time
from astropy.wcs import WCS, FITSFixedWarning
from astroquery.jplhorizons import Horizons

from planetes.access import fetch_cutouts, find_frames
from planetes.contracts import SpectrumPoint
from planetes.known import known_in_frame
from planetes.photometry import measure
from planetes.spectrum import blend_reason, neighbours_near, pair_id, reject_reason
from planetes.thermal import thermal_opinion

warnings.simplefilter("ignore")
warnings.simplefilter("ignore", FITSFixedWarning)

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "evidence" / "v7_thermometer.csv"
SIZE_DEG = 0.4
N_EXPOSURES = 40
VMAX = 17.5
MIN_TESTED = 20
PASS_FRAC = 0.70


def _ecliptic_dec(ra_deg: float) -> float:
    return math.degrees(math.atan(math.sin(math.radians(ra_deg)) * math.tan(math.radians(23.44))))


FIELDS = [(float(ra), round(_ecliptic_dec(ra), 3)) for ra in range(9, 360, 18)]


def exposure(obs_id: str) -> str:
    return obs_id.split("?", 1)[-1].rsplit("/D", 1)[0]


def horizons_id(name: str) -> str:
    """'1938 Lausanna (1974 HC)' -> '1938'; '(2010 AB12)' -> '2010 AB12'."""
    m = re.match(r"^\s*(\d+)\s+\D", name)
    if m:
        return m.group(1)
    return name.strip().strip("()").split(" (")[0]


def field_points(ra: float, dec: float) -> dict[str, list[SpectrumPoint]]:
    frames = find_frames(ra, dec, size_deg=SIZE_DEG)
    frames = frames[frames["detector"].isin([3, 6])].copy()
    frames["exposure"] = frames["obs_id"].map(exposure)
    both = frames.groupby("exposure")["detector"].nunique()
    frames = frames[frames["exposure"].isin(both[both == 2].index)].sort_values("mjd")
    exps = list(dict.fromkeys(frames["exposure"]))
    step = max(1, len(exps) // N_EXPOSURES)
    keep = set(exps[::step][:N_EXPOSURES])
    frames = frames[frames["exposure"].isin(keep)]
    print(f"RA {ra} Dec {dec}: {len(keep)} D3/D6 exposures", flush=True)
    blobs = fetch_cutouts(frames, max_concurrent=8)
    by_exp = {e: {int(r["detector"]): r for _, r in g.iterrows()} for e, g in frames.groupby("exposure")}
    out: dict[str, list[SpectrumPoint]] = defaultdict(list)
    for exp, dets in by_exp.items():
        d3, d6 = blobs.get(f"cutouts/{dets[3]['frame_id']}.fits"), blobs.get(f"cutouts/{dets[6]['frame_id']}.fits")
        if d3 is None or d6 is None:
            continue
        with fits.open(io.BytesIO(d3)) as h:
            hd = h["IMAGE"].header
            try:
                objs = known_in_frame(hd, WCS(hd).celestial, h["IMAGE"].data.shape, vmag_max=VMAX)
            except Exception as exc:  # report and move on; never invent a detection
                print("  SBIdent failed for", exp, exc)
                continue
        for o in objs:
            try:
                nb = neighbours_near(o.ra_deg, o.dec_deg)
            except Exception:
                nb = None
            for det, data in ((3, d3), (6, d6)):
                row = dets[det]
                m = measure(data, o.ra_deg, o.dec_deg)
                reason = reject_reason(m)
                if reason is None and nb:
                    reason = blend_reason(o.ra_deg, o.dec_deg, nb)
                obs_id = str(row["obs_id"])
                out[o.name].append(
                    SpectrumPoint(
                        obs_id=obs_id,
                        mjd=float(row["mjd"]),
                        detector=det,
                        wavelength_um=m.wavelength_um,
                        bandwidth_um=m.bandwidth_um,
                        flux_ujy=m.flux_ujy,
                        flux_err_ujy=m.flux_err_ujy,
                        snr=m.snr,
                        flags=max(m.flags, 0),
                        saturated=m.saturated,
                        used=reason is None,
                        reject_reason=reason,
                        pair_id=pair_id(obs_id, det),
                        method="aperture" if m.flux_ujy is not None else None,
                        ra=o.ra_deg % 360.0,
                        dec=o.dec_deg,
                    )
                )
    return out


def usable_pairs(points: list[SpectrumPoint]) -> list[str]:
    by: dict[str, set[int]] = defaultdict(set)
    for p in points:
        if p.used and p.pair_id and p.flux_ujy and p.flux_ujy > 0:
            by[p.pair_id].add(p.detector)
    return [k for k, v in by.items() if v == {3, 6}]


def jpl_r_au(name: str, mjd: float) -> float | None:
    try:
        eph = Horizons(id=horizons_id(name), location="500@399", epochs=Time(mjd, format="mjd").jd).ephemerides()
        return float(eph["r"][0])
    except Exception as exc:
        print("  Horizons failed for", name, exc)
        return None


def main() -> None:
    points: dict[str, list[SpectrumPoint]] = defaultdict(list)
    for ra, dec in FIELDS:
        try:
            found = field_points(ra, dec)
        except RuntimeError as exc:  # IRSA not answering: skip the field, say so, never fill in
            print(f"RA {ra} Dec {dec}: skipped, {exc}", flush=True)
            continue
        for name, pts in found.items():
            points[name] += pts
    rows = []
    for name, pts in sorted(points.items()):
        pairs = usable_pairs(pts)
        row: dict = {"name": name, "points": len(pts), "usable_pairs": len(pairs), "tested": len(pairs) >= 2}
        if row["tested"]:
            op, fit = thermal_opinion(pts)
            used3 = [p.mjd for p in pts if p.used and p.detector == 3 and p.pair_id in pairs]
            r = jpl_r_au(name, float(np.mean(used3)))
            row.update(
                jpl_r_au=None if r is None else round(r, 3),
                lo_au=op.distance.lo,
                hi_au=op.distance.hi,
                best_au=None if fit is None else round(fit.best_au, 2),
                d6_d3=None if fit is None else round(fit.observed_ratio, 4),
                elongation_deg=None if fit is None else round(fit.elongation_deg, 1),
                quality=op.quality if fit is not None else "none",
                hit=bool(r is not None and fit is not None and fit.lo_au <= r <= fit.hi_au),
            )
            if r is None:
                row["tested"] = False  # no truth value: cannot be scored
        rows.append(row)
        print(" ", row, flush=True)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    keys = ["name", "points", "usable_pairs", "tested", "jpl_r_au", "lo_au", "hi_au", "best_au", "d6_d3"]
    keys += ["elongation_deg", "quality", "hit"]
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)

    tested = [r for r in rows if r["tested"]]
    hits = sum(r["hit"] for r in tested)
    widths = [(r["hi_au"] - r["lo_au"]) for r in tested if r.get("lo_au") is not None]
    q = {k: sum(r.get("quality") == k for r in tested) for k in ("good", "fair", "poor", "none")}
    print(f"asteroids seen: {len(rows)}, tested (>= 2 usable D3/D6 pairs + JPL r): {len(tested)}")
    if tested:
        print(f"hits: {hits}/{len(tested)} = {hits / len(tested):.0%}; quality {q}")
    if widths:
        print(f"median range width {float(np.median(widths)):.2f} au")
    ok = len(tested) >= MIN_TESTED and tested and hits / len(tested) >= PASS_FRAC
    print("V7", "PASS" if ok else "NOT PASSED")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
