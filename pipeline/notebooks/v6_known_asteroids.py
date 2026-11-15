"""V6: do known asteroids appear in real SPHEREx frames where JPL predicts, seen from SPHEREx itself?

Run: python pipeline/notebooks/v6_known_asteroids.py [ra_deg dec_deg]
Output: docs/evidence/v6_known_asteroids.csv (one row per predicted asteroid) and a summary on stdout.

For each real frame on an ecliptic field: JPL SBIdent with the spacecraft state from the frame header (known.py),
then a 2-D Gaussian centroid in a 7x7 box around each prediction on the zodi-subtracted image. A match is a centroid
within 1 pixel of the prediction with a peak at least 5 sigma above the local background (pass mark: >= 10 matched,
docs/04 §7 V6). Asteroids fainter than V 17.5 are skipped (below a single SPHEREx visit at short wavelengths).
"""

from __future__ import annotations

import csv
import io
import math
import sys
import warnings
from pathlib import Path

import numpy as np
from astropy.io import fits
from astropy.wcs import WCS, FITSFixedWarning
from photutils.centroids import centroid_2dg

from planetes.access import fetch_cutouts, find_frames
from planetes.known import known_in_frame

warnings.simplefilter("ignore", FITSFixedWarning)


def _ecliptic_dec(ra_deg: float) -> float:
    """Declination of the ecliptic at this RA (obliquity 23.44 deg)."""
    return math.degrees(math.atan(math.sin(math.radians(ra_deg)) * math.tan(math.radians(23.44))))


# Ten fields spread along the ecliptic (or one field given on the command line).
FIELDS = (
    [(float(sys.argv[1]), float(sys.argv[2]))]
    if len(sys.argv) > 2
    else [(ra, round(_ecliptic_dec(ra), 3)) for ra in range(15, 360, 36)]
)
SIZE_DEG = 0.4
N_FRAMES = 25  # per field
VMAX = 17.5
BOX = 3  # half-size of the centroid box (7x7)
OUT = Path(__file__).resolve().parents[2] / "docs" / "evidence" / "v6_known_asteroids.csv"


def main() -> None:
    rows = []
    for ra, dec in FIELDS:
        rows += field_rows(ra, dec)
    report(rows)


def field_rows(ra: float, dec: float) -> list[dict]:
    frames = find_frames(ra, dec, size_deg=SIZE_DEG)
    frames = frames[frames["detector"].isin([1, 2, 3])].sort_values("mjd")
    step = max(1, len(frames) // N_FRAMES)
    frames = frames.iloc[::step].head(N_FRAMES)
    print(f"{len(frames)} frames (D1-D3) around RA {ra}, Dec {dec}", flush=True)
    blobs = fetch_cutouts(frames, max_concurrent=8)
    rows = []
    for _, fr in frames.iterrows():
        data = blobs.get(f"cutouts/{fr['frame_id']}.fits")
        if data is None:
            continue
        with fits.open(io.BytesIO(data)) as h:
            hd = h["IMAGE"].header
            img = np.asarray(h["IMAGE"].data, float) - np.asarray(h["ZODI"].data, float)
            var = np.asarray(h["VARIANCE"].data, float)
            wcs = WCS(hd).celestial
            try:
                objs = known_in_frame(hd, wcs, img.shape, vmag_max=VMAX)
            except Exception as exc:  # report and move on; never invent a match
                print("  SBIdent failed for", fr["obs_id"], exc)
                continue
            for o in objs:
                x, y = (float(v) for v in wcs.world_to_pixel_values(o.ra_deg, o.dec_deg))
                xi, yi = int(round(x)), int(round(y))
                ny, nx = img.shape
                row = {
                    "obs_id": fr["obs_id"],
                    "mjd": round(float(fr["mjd"]), 5),
                    "detector": int(fr["detector"]),
                    "name": o.name,
                    "v_mag": o.v_mag,
                    "pred_x": round(x, 2),
                    "pred_y": round(y, 2),
                    "cen_x": None,
                    "cen_y": None,
                    "offset_px": None,
                    "peak_snr": None,
                    "matched": False,
                }
                if BOX <= xi < nx - BOX and BOX <= yi < ny - BOX:
                    cut = img[yi - BOX : yi + BOX + 1, xi - BOX : xi + BOX + 1]
                    vcut = var[yi - BOX : yi + BOX + 1, xi - BOX : xi + BOX + 1]
                    if np.all(np.isfinite(cut)) and np.all(np.isfinite(vcut)):
                        bkg = float(np.median(img[max(0, yi - 8) : yi + 9, max(0, xi - 8) : xi + 9]))
                        cx, cy = centroid_2dg(cut - bkg)
                        cx, cy = xi - BOX + float(cx), yi - BOX + float(cy)
                        snr = float((cut.max() - bkg) / math.sqrt(max(float(np.median(vcut)), 1e-30)))
                        off = math.hypot(cx - x, cy - y)
                        row.update(
                            cen_x=round(cx, 2),
                            cen_y=round(cy, 2),
                            offset_px=round(off, 3),
                            peak_snr=round(snr, 1),
                            matched=bool(off <= 1.0 and snr >= 5.0),
                        )
                rows.append(row)
    return rows


def report(rows: list[dict]) -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]) if rows else ["obs_id"])
        w.writeheader()
        w.writerows(rows)
    matched = [r for r in rows if r["matched"]]
    names = sorted({r["name"] for r in matched})
    offs = [r["offset_px"] for r in matched]
    print(f"predicted (V<={VMAX}): {len(rows)} detections of {len({r['name'] for r in rows})} asteroids")
    print(f"matched within 1 px and >=5 sigma: {len(matched)} detections of {len(names)} asteroids")
    if offs:
        print(f"median offset {np.median(offs):.2f} px, max {max(offs):.2f} px")
    print("V6", "PASS" if len(names) >= 10 else "NOT PASSED", "(needs >= 10 asteroids)")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
