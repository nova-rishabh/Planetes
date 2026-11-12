"""End-to-end SPHEREx spectrum builder (Deliverable D2.4).

Orchestrates archive search (access.find_frames), parallel cutout retrieval
(access.fetch_cutouts), and parallel forced ePSF/aperture photometry (photometry.py)
to produce a validated SpectrumResult within the <90s latency budget.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC_DIR = str(Path(__file__).resolve().parents[1])
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd

from planetes import access, photometry
from planetes.cache import Cache
from planetes.contracts import (
    Detector,
    SpectrumPoint,
    SpectrumProvenance,
    SpectrumRequest,
    SpectrumResult,
    SpectrumSummary,
    SpectrumTarget,
)

CUTOUT_SIZE_DEG = 0.04  # ~23x23 px cutout, keeping download & memory footprint tiny
BATCH_SIZE = 12


def _select_frames_per_detector(df: pd.DataFrame, max_per_detector: int = 18) -> pd.DataFrame:
    """Sample frames evenly across MJD per detector so all spectral channels are covered."""
    if df.empty:
        return df
    chunks = []
    for _, grp in df.groupby("detector"):
        grp_sorted = grp.sort_values("mjd").reset_index(drop=True)
        if len(grp_sorted) <= max_per_detector:
            chunks.append(grp_sorted)
        else:
            idx = np.unique(np.linspace(0, len(grp_sorted) - 1, max_per_detector).round().astype(int))
            chunks.append(grp_sorted.iloc[idx])
    return pd.concat(chunks, ignore_index=True).sort_values("mjd").reset_index(drop=True)


def build_spectrum(
    req: SpectrumRequest,
    code_version: str = "d2.4-1.0",
    cache: Cache | None = None,
    workers: int = 8,
    progress: Callable[[int, int | None, str], None] | None = None,
    max_per_detector: int = 18,
) -> SpectrumResult:
    """Run full spectrum extraction from a SpectrumRequest."""
    if progress:
        progress(0, None, "searching SPHEREx archive for target coverage")

    found = access.find_frames(req.ra, req.dec, size_deg=CUTOUT_SIZE_DEG, release=req.release)
    if req.pm is not None and not found.empty:
        mid_mjd = float(found["mjd"].median())
        ra_mid, dec_mid = photometry.propagate_position(req.ra, req.dec, mid_mjd, pm=req.pm)
        found = access.find_frames(ra_mid, dec_mid, size_deg=CUTOUT_SIZE_DEG, release=req.release)

    if found.empty:
        return SpectrumResult(
            schema_version="1.0",
            target=SpectrumTarget(ra=req.ra, dec=req.dec, pm=req.pm),
            points=[],
            summary=SpectrumSummary(n_points=0, n_used=0, n_rejected=0, bands_covered=[]),
            provenance=SpectrumProvenance(release=req.release, code_version=code_version),
        )

    chosen = _select_frames_per_detector(found, max_per_detector=max_per_detector)
    total = len(chosen)
    points: list[SpectrumPoint] = []
    bands_covered: set[int] = set()

    for start in range(0, total, BATCH_SIZE):
        batch = chosen.iloc[start : start + BATCH_SIZE]
        if progress:
            progress(start, total, f"measuring photometry ({start}/{total} frames)")

        blobs = access.fetch_cutouts(batch, max_concurrent=workers, cache=cache)
        ordered_blobs = [blobs.get(f"cutouts/{row['frame_id']}.fits") for _, row in batch.iterrows()]
        valid_blobs = [b for b in ordered_blobs if b is not None]

        if not valid_blobs:
            continue

        def _measure_one(blob: bytes) -> SpectrumPoint | None:
            try:
                return photometry.measure_frame_flux(
                    blob,
                    ra=req.ra,
                    dec=req.dec,
                    pm=req.pm,
                    method=req.method,
                )
            except Exception:
                return None

        with ThreadPoolExecutor(max_workers=workers) as pool:
            batch_pts = list(pool.map(_measure_one, valid_blobs))

        for pt in batch_pts:
            if pt is not None:
                points.append(pt)
                if pt.used:
                    bands_covered.add(int(pt.detector))

        del blobs

    if progress:
        progress(total, total, "finalizing spectrum")

    points.sort(key=lambda pt: (pt.wavelength_um or 0.0, pt.mjd))
    n_points = len(points)
    n_used = sum(1 for pt in points if pt.used)
    n_rejected = n_points - n_used

    return SpectrumResult(
        schema_version="1.0",
        target=SpectrumTarget(ra=req.ra, dec=req.dec, pm=req.pm),
        points=points,
        summary=SpectrumSummary(
            n_points=n_points,
            n_used=n_used,
            n_rejected=n_rejected,
            bands_covered=[Detector(b) for b in sorted(bands_covered)],
        ),
        provenance=SpectrumProvenance(
            release=req.release,
            code_version=code_version,
        ),
    )


if __name__ == "__main__":
    import time

    root = Path(__file__).resolve().parents[3]
    cache = Cache(root / ".planetes-cache")

    req = SpectrumRequest(
        ra=115.8000,
        dec=-21.6785,
        release="QR2",
        method="auto",
    )

    t0 = time.perf_counter()
    res = build_spectrum(
        req,
        cache=cache,
        max_per_detector=3,
        progress=lambda done, total, msg: print(f"[{done}/{total or '?'}] {msg}"),
    )
    elapsed = time.perf_counter() - t0

    print(
        f"\nCompleted in {elapsed:.2f}s | Used {res.summary.n_used}/{res.summary.n_points} points | "
        f"Bands: {[d.root for d in res.summary.bands_covered]}"
    )
    for pt in res.points[:10]:
        wave_str = f"{pt.wavelength_um:.3f} um" if pt.wavelength_um is not None else "N/A"
        print(
            f"D{pt.detector} ({pt.pair_id}) | {wave_str} | "
            f"Flux: {pt.flux_ujy} +/- {pt.flux_err_ujy} uJy | SNR: {pt.snr} | "
            f"Method: {pt.method} | Used: {pt.used}"
        )