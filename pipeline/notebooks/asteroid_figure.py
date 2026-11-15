"""Asteroid figure for the site: two real SPHEREx frames of 1562 Gondolatsch, 3.2 hours apart (from V6).

Run: .venv/Scripts/python.exe pipeline/notebooks/asteroid_figure.py

Both frames are cut out around the midpoint of the two JPL positions, put on one north-up grid with one shared
stretch (the same functions as the time-lapse), and written to web/public/data/asteroid/. JPL positions come from
SBIdent for each frame (known.py), measured positions from a 2-D Gaussian centroid on the reprojected frame.
The script stops if the asteroid is not within 1 px of JPL in both frames, or if anything sits at its position
in the other frame.
"""

from __future__ import annotations

import io
import json
import math
import sys
import warnings
from pathlib import Path

import numpy as np
from astropy.io import fits
from astropy.wcs import WCS
from photutils.centroids import centroid_2dg

from planetes.access import fetch_cutouts, find_frames
from planetes.frames import make_reference_grid
from planetes.known import known_in_frame
from planetes.render import shared_stretch, to_webp
from planetes.stack import prepare_frame_and_variance

warnings.simplefilter("ignore")

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "web" / "public" / "data" / "asteroid"
NAME = "1562 Gondolatsch"
EXPOSURES = ("2025W48_1A_0556_3/D2", "2025W48_1A_0585_3/D1")  # from docs/evidence/v6_known_asteroids.csv
GRID = 48
BOX = 3


def snr_at(img: np.ndarray, var: np.ndarray, x: float, y: float) -> tuple[float, float, float]:
    """Centroid and peak S/N near grid pixel (x, y); NaN centroid when the box has no usable data."""
    xi, yi = int(round(x)), int(round(y))
    cut = img[yi - BOX : yi + BOX + 1, xi - BOX : xi + BOX + 1]
    vcut = var[yi - BOX : yi + BOX + 1, xi - BOX : xi + BOX + 1]
    bkg = float(np.nanmedian(img[max(0, yi - 8) : yi + 9, max(0, xi - 8) : xi + 9]))
    snr = float((np.nanmax(cut) - bkg) / math.sqrt(max(float(np.nanmedian(vcut)), 1e-30)))
    try:
        cx, cy = centroid_2dg(np.nan_to_num(cut - bkg))
        return xi - BOX + float(cx), yi - BOX + float(cy), snr
    except ValueError:
        return float("nan"), float("nan"), snr


def main() -> None:
    # 1. JPL positions from SBIdent on the original cutouts (V6 field RA 159, Dec 8.832).
    field = find_frames(159.0, 8.832, size_deg=0.4)
    field = field[field["obs_id"].str.split("?").str[-1].isin(EXPOSURES)]
    blobs = fetch_cutouts(field)
    jpl: dict[str, tuple[float, float, float]] = {}
    for _, row in field.iterrows():
        with fits.open(io.BytesIO(blobs[f"cutouts/{row['frame_id']}.fits"])) as h:
            hd = h["IMAGE"].header
            obj = [
                o
                for o in known_in_frame(hd, WCS(hd).celestial, h["IMAGE"].data.shape, vmag_max=18)
                if o.name.startswith(NAME)
            ]
        if len(obj) != 1:
            sys.exit(f"SBIdent did not return {NAME} for {row['obs_id']}")
        jpl[row["obs_id"].split("?")[-1]] = (obj[0].ra_deg, obj[0].dec_deg, float(obj[0].v_mag or float("nan")))

    ra_c = float(np.mean([v[0] for v in jpl.values()]))
    dec_c = float(np.mean([v[1] for v in jpl.values()]))
    ref_wcs, grid = make_reference_grid(ra_c, dec_c, size_pixels=GRID)

    # 2. Fresh cutouts around the midpoint, reprojected onto one grid.
    rows = find_frames(ra_c, dec_c, size_deg=0.1)
    rows = rows[rows["obs_id"].str.split("?").str[-1].isin(EXPOSURES)].sort_values("mjd")
    if len(rows) != 2:
        sys.exit("both exposures must cover the midpoint")
    blobs = fetch_cutouts(rows)
    prepared = []
    for _, row in rows.iterrows():
        pf, var, _good = prepare_frame_and_variance(
            blobs[f"cutouts/{row['frame_id']}.fits"], row.to_dict(), ref_wcs, (GRID, GRID)
        )
        prepared.append((row, pf, var))

    stretch = shared_stretch([pf.image for _, pf, _ in prepared])
    assert stretch is not None
    OUT.mkdir(parents=True, exist_ok=True)

    # 3. Measure each frame at its own JPL position, and check the other position is empty.
    xy = {k: tuple(float(v) for v in ref_wcs.world_to_pixel_values(r, d)) for k, (r, d, _) in jpl.items()}
    out_frames = []
    for i, (row, pf, var) in enumerate(prepared):
        key = row["obs_id"].split("?")[-1]
        other = EXPOSURES[1 - EXPOSURES.index(key)]
        px, py = xy[key]
        cx, cy, snr = snr_at(pf.image, var, px, py)
        _, _, snr_other = snr_at(pf.image, var, *xy[other])
        offset = math.hypot(cx - px, cy - py)
        print(f"{key}: offset {offset:.2f} px, S/N {snr:.1f}; at the other position S/N {snr_other:.1f}")
        if not (offset <= 1.0 and snr >= 5.0 and snr_other < 3.0):
            sys.exit("check failed; figure not written")
        name = f"{'ab'[i]}.webp"
        (OUT / name).write_bytes(to_webp(pf.image, stretch, pf.masks.saturated))
        f = pf.frame
        out_frames.append(
            {
                "image": f"/data/asteroid/{name}",
                "obs_id": row["obs_id"],
                "release": f.release,
                "utc": f.utc.isoformat().replace("+00:00", "Z") if hasattr(f.utc, "isoformat") else f.utc,
                "mjd": round(float(row["mjd"]), 5),
                "detector": int(row["detector"]),
                "wavelength_um": round(float(f.wavelength_um), 2) if f.wavelength_um else None,
                "jpl_xy": [round(px, 2), round(py, 2)],
                "measured_xy": [round(cx, 2), round(cy, 2)],
                "offset_px": round(offset, 2),
                "peak_snr": round(snr, 1),
            }
        )

    (ax, ay), (bx, by) = xy[EXPOSURES[0]], xy[EXPOSURES[1]]
    hours = (out_frames[1]["mjd"] - out_frames[0]["mjd"]) * 24
    shift = math.hypot(bx - ax, by - ay) * 6.2
    meta = {
        "schema_version": "1.0",
        "name": NAME,
        "source": "SPHEREx (IRSA) frames; positions from JPL Small-Body Identification (SBIdent)",
        "v_mag": jpl[EXPOSURES[0]][2],
        "grid_px": GRID,
        "pixel_arcsec": 6.2,
        "hours_apart": round(hours, 2),
        "shift_arcsec": round(shift, 0),
        "frames": out_frames,
    }
    (OUT / "asteroid.json").write_text(json.dumps(meta, indent=2), encoding="utf-8", newline="\n")
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
