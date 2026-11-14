"""V9 false-alarm control (docs/04 §7): shuffle the frame dates of each benchmark field and count fake movers.

Run: .venv/Scripts/python.exe pipeline/notebooks/v9_false_alarms.py

The rule below was fixed before the first run and is not tuned afterwards.

Sources. In every SPHEREx cutout (zodiacal light subtracted), peaks at S/N >= 10 are centroided with a 2-D
Gaussian (7x7 box). A detection is dropped if any pixel in its 5x5 box carries a saturation or other bad-pixel
flag (frames.classify_flags), so saturated stars are left out of the search. Detections from all frames are
linked friends-of-friends on the sky with a 1.5 px (9.3") linking length. A linked source is tested only if it
has at most one detection per frame, at least 6 detections and detections in at least 3 survey epochs (frames
more than 60 days apart start a new epoch).

Mover. motion.fit_proper_motion on the source's positions and frame dates. It is a mover when all hold:
  mu >= 0.15"/yr (the app's own "static" limit in motion.star_motion_opinion),
  mu / sigma_mu >= 5 (sigma from the fit residuals),
  mu x baseline >= 6.2" (one SPHEREx pixel).

Positive control. With the real dates the rule must flag Barnard's Star or eps Indi B (within 30" of their
mean position); otherwise a count of zero fake movers means nothing and V9 does not pass.

Shuffle. 100 random permutations of the frame dates within each field (seed 9). A permutation that keeps every
frame in its own epoch, or maps every epoch onto the reversed epoch order, is skipped, because a straight-line
fit cannot tell those from the real order. Reported per field: worst and median number of movers over the
shuffles. Pass: worst <= 2 in every field.
"""

from __future__ import annotations

import csv
import io
import math
import warnings
from pathlib import Path

import numpy as np
from astropy.io import fits
from astropy.wcs import WCS, FITSFixedWarning
from photutils.centroids import centroid_2dg
from photutils.detection import find_peaks
from scipy.spatial import cKDTree

from planetes.access import fetch_cutouts, find_frames
from planetes.frames import classify_flags, flag_bits
from planetes.motion import fit_proper_motion

warnings.simplefilter("ignore")
warnings.simplefilter("ignore", FITSFixedWarning)

ROOT = Path(__file__).resolve().parents[2]
TARGETS = {
    "barnard": (269.44850252544, 4.73942005111),
    "epsindib": (331.07645259656, -56.79381206688),
    "wise0855": (133.81890825, -7.247048),
    "rwaur": (76.95652603458333, 30.401438173888888),
    "rdra": (248.16737836729, 66.75500674547),
}
CONTROLS = {"barnard", "epsindib"}
SIZE_DEG = 0.1
N_FRAMES = 40
PIX_ARCSEC = 6.2
SNR_MIN = 10.0
BOX = 3
LINK_ARCSEC = 1.5 * PIX_ARCSEC
EPOCH_GAP_D = 60.0
MIN_DET, MIN_EPOCHS = 6, 3
MU_MIN, SIG_MIN = 0.15, 5.0
N_SHUFFLES, SEED = 100, 9
OUT = ROOT / "docs" / "evidence" / "v9_false_alarms.csv"


def detections(ra0: float, dec0: float) -> tuple[list[dict], np.ndarray]:
    frames = find_frames(ra0, dec0, size_deg=SIZE_DEG).sort_values("mjd")
    step = max(1, len(frames) // N_FRAMES)
    frames = frames.iloc[::step].head(N_FRAMES)
    blobs = fetch_cutouts(frames, max_concurrent=8)
    dets: list[dict] = []
    mjds: list[float] = []
    for _, fr in frames.iterrows():
        data = blobs.get(f"cutouts/{fr['frame_id']}.fits")
        if data is None:
            continue
        k = len(mjds)
        mjds.append(float(fr["mjd"]))
        with fits.open(io.BytesIO(data)) as h:
            img = np.asarray(h["IMAGE"].data, float) - np.asarray(h["ZODI"].data, float)
            var = np.asarray(h["VARIANCE"].data, float)
            bad = classify_flags(np.asarray(h["FLAGS"].data).astype(np.int64), flag_bits(h["FLAGS"].header))
            bad = bad.saturated | bad.other
            wcs = WCS(h["IMAGE"].header).celestial
        snr = (img - np.nanmedian(img)) / np.sqrt(np.where(var > 0, var, np.nan))
        snr = np.nan_to_num(snr, nan=0.0)
        peaks = find_peaks(snr, threshold=SNR_MIN, box_size=5, border_width=BOX + 1)
        if peaks is None:
            continue
        for p in peaks:
            xi, yi = int(p["x_peak"]), int(p["y_peak"])
            if bad[yi - 2 : yi + 3, xi - 2 : xi + 3].any():
                continue
            cut = img[yi - BOX : yi + BOX + 1, xi - BOX : xi + BOX + 1]
            if not np.all(np.isfinite(cut)):
                continue
            bkg = float(np.median(img[max(0, yi - 8) : yi + 9, max(0, xi - 8) : xi + 9]))
            cx, cy = centroid_2dg(cut - bkg)
            x, y = xi - BOX + float(cx), yi - BOX + float(cy)
            if not (abs(x - xi) < 2 and abs(y - yi) < 2):
                continue
            ra, dec = (float(v) for v in wcs.pixel_to_world_values(x, y))
            err_mas = max(0.1, 0.7 / float(p["peak_value"])) * PIX_ARCSEC * 1000
            dets.append({"frame": k, "ra": ra, "dec": dec, "err": err_mas})
    print(f"  {len(mjds)} frames, {len(dets)} unflagged detections at S/N >= {SNR_MIN:g}", flush=True)
    return dets, np.array(mjds)


def link(dets: list[dict], ra0: float, dec0: float) -> list[list[dict]]:
    if not dets:
        return []
    xy = np.array([((d["ra"] - ra0) * math.cos(math.radians(dec0)) * 3600, (d["dec"] - dec0) * 3600) for d in dets])
    parent = list(range(len(dets)))

    def root(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i, j in cKDTree(xy).query_pairs(LINK_ARCSEC):
        parent[root(i)] = root(j)
    groups: dict[int, list[dict]] = {}
    for i, d in enumerate(dets):
        groups.setdefault(root(i), []).append(d)
    return list(groups.values())


def epochs_of(mjds: np.ndarray) -> np.ndarray:
    order = np.argsort(mjds)
    ep = np.zeros(len(mjds), int)
    e = 0
    for a, b in zip(order[:-1], order[1:], strict=True):
        if mjds[b] - mjds[a] > EPOCH_GAP_D:
            e += 1
        ep[b] = e
    return ep


def testable(sources: list[list[dict]], epoch: np.ndarray) -> list[list[dict]]:
    out = []
    for s in sources:
        frames = [d["frame"] for d in s]
        if len(frames) != len(set(frames)) or len(s) < MIN_DET:
            continue
        if len({int(epoch[f]) for f in frames}) >= MIN_EPOCHS:
            out.append(s)
    return out


def movers(sources: list[list[dict]], mjds: np.ndarray) -> list[tuple[float, float, float, float]]:
    found = []
    for s in sources:
        t = [float(mjds[d["frame"]]) for d in s]
        try:
            fit = fit_proper_motion(
                t, [d["ra"] for d in s], [d["dec"] for d in s], [d["err"] for d in s], [d["err"] for d in s]
            )
        except (ValueError, np.linalg.LinAlgError):
            continue
        sig = fit.mu_arcsec_yr / fit.mu_err_arcsec_yr if fit.mu_err_arcsec_yr > 0 else 0.0
        if fit.mu_arcsec_yr >= MU_MIN and sig >= SIG_MIN and fit.mu_arcsec_yr * fit.time_baseline_yr >= PIX_ARCSEC:
            found.append(
                (float(np.mean([d["ra"] for d in s])), float(np.mean([d["dec"] for d in s])), fit.mu_arcsec_yr, sig)
            )
    return found


def main() -> None:
    rng = np.random.default_rng(SEED)
    rows = []
    for name, (ra0, dec0) in TARGETS.items():
        print(name, flush=True)
        dets, mjds = detections(ra0, dec0)
        epoch = epochs_of(mjds)
        srcs = testable(link(dets, ra0, dec0), epoch)
        real = movers(srcs, mjds)
        near = [m for m in real if math.hypot((m[0] - ra0) * math.cos(math.radians(dec0)), m[1] - dec0) * 3600 <= 30]
        counts = []
        rev = epoch.max() - epoch
        while len(counts) < N_SHUFFLES:
            perm = rng.permutation(len(mjds))
            if np.array_equal(epoch[perm], epoch) or np.array_equal(epoch[perm], rev):
                continue
            counts.append(len(movers(srcs, mjds[perm])))
        row = {
            "field": name,
            "frames": len(mjds),
            "epochs": int(epoch.max() + 1) if len(epoch) else 0,
            "sources_tested": len(srcs),
            "real_date_movers": len(real),
            "target_flagged": bool(near),
            "target_mu_arcsec_yr": round(near[0][2], 2) if near else None,
            "shuffles": len(counts),
            "false_movers_median": float(np.median(counts)),
            "false_movers_worst": int(max(counts)),
        }
        print("  ", row, flush=True)
        rows.append(row)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    control = any(r["target_flagged"] for r in rows if r["field"] in CONTROLS)
    worst = max(r["false_movers_worst"] for r in rows)
    print("positive control:", "caught" if control else "NOT caught")
    verdict = "PASS" if control and worst <= 2 else "NOT PASSED"
    print("V9", verdict, f"(worst {worst} fake movers in a field; needs <= 2)")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
