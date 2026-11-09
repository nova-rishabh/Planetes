"""Time-lapse job: POST /api/timelapse -> planetes.access (find + download) -> planetes.frames (align) ->
planetes.render (shared stretch, WebP, flag overlay) -> files in the cache and a TimelapseResult.

Only single exposures exist so far; stacks, differences, sums and colour come with D2.3. Cutouts are
downloaded and processed in small batches so a 60-frame job stays inside the 512 MB API instance.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime

import astropy.units as u
import numpy as np
import pandas as pd
from astropy.coordinates import SkyCoord
from astropy.time import Time

from planetes import access, frames, render
from planetes.cache import Cache
from planetes.contracts import Epoch, Provenance, TimelapseRequest, TimelapseResult

from .jobs import JobContext, JobError

BATCH = 8
MAX_GRID_PX = 300


def pick_evenly(df: pd.DataFrame, k: int) -> pd.DataFrame:
    """At most k rows spread evenly through time (df is sorted by mjd)."""
    if len(df) <= k:
        return df
    idx = np.unique(np.linspace(0, len(df) - 1, k).round().astype(int))
    return df.iloc[idx]


def target_positions(req: TimelapseRequest, mjds: list[float]) -> list[tuple[float, float]]:
    """The target at each frame date: moved for proper motion when the request carries one, else fixed."""
    if req.pm is None:
        return [(req.ra, req.dec)] * len(mjds)
    star = SkyCoord(
        ra=req.ra * u.deg,
        dec=req.dec * u.deg,
        pm_ra_cosdec=req.pm.pm_ra_masyr * u.mas / u.yr,
        pm_dec=req.pm.pm_dec_masyr * u.mas / u.yr,
        obstime=Time(req.pm.ref_epoch_jyear, format="jyear"),
    )
    moved = star.apply_space_motion(new_obstime=Time(mjds, format="mjd"))
    return [(float(r), float(d)) for r, d in zip(moved.ra.deg, moved.dec.deg, strict=True)]


def _search(ra: float, dec: float, req: TimelapseRequest) -> pd.DataFrame:
    """Frames covering (ra, dec) with the request's detector and date filters; cutouts centred on (ra, dec)."""
    try:
        found = access.find_frames(ra, dec, size_deg=req.fov_deg, release=req.release)
    except RuntimeError as exc:
        raise JobError("IRSA_ERROR", "NASA's archive (IRSA) did not answer the search", str(exc)) from exc
    detectors = [int(d.root) for d in req.detectors]
    found = found[found["detector"].isin(detectors)]
    if req.mjd_start is not None:
        found = found[found["mjd"] >= req.mjd_start]
    if req.mjd_end is not None:
        found = found[found["mjd"] <= req.mjd_end]
    if found.empty:
        raise JobError("NO_COVERAGE", "SPHEREx has no images of this spot for the chosen detectors and dates")
    return found


def run_timelapse(
    req: TimelapseRequest,
    ctx: JobContext,
    cache: Cache,
    code_version: str,
    concurrency: int = 8,
) -> TimelapseResult:
    if req.mode != "exposures":
        raise JobError(
            "BAD_INPUT",
            f"The '{req.mode}' view is not ready yet; single exposures are.",
            "Choose 'Single exposures'. Stacks and differences arrive with the next pipeline step.",
        )

    ctx.progress(0, None, "asking NASA's archive which images cover this spot")
    found = _search(req.ra, req.dec, req)
    center = (req.ra, req.dec)
    if req.pm is not None:
        # A moving star is not at its catalogue position during the SPHEREx years: centre the cutouts and the
        # grid on where it is at the middle of the matching dates, then search again from there.
        center = target_positions(req, [float(found["mjd"].median())])[0]
        found = _search(center[0], center[1], req)
    chosen = pick_evenly(found.sort_values("mjd").reset_index(drop=True), req.max_frames)

    size_px = min(MAX_GRID_PX, math.ceil(req.fov_deg / frames.SPHEREX_PIXEL_SCALE_DEG))
    ref_wcs, grid = frames.make_reference_grid(center[0], center[1], size_pixels=size_px)
    targets = target_positions(req, chosen["mjd"].astype(float).tolist())

    prepared: list[frames.PreparedFrame] = []
    total = len(chosen)
    for start in range(0, total, BATCH):
        batch = chosen.iloc[start : start + BATCH]
        ctx.progress(start, total, "downloading and aligning images")
        data = access.fetch_cutouts(batch, max_concurrent=concurrency, cache=cache)
        for i, (_, row) in enumerate(batch.iterrows()):
            blob = data.get(f"cutouts/{row['frame_id']}.fits")
            if blob is None:
                continue  # download failed after retries; the frame is left out, not faked
            prepared.append(
                frames.prepare_frame(blob, row.to_dict(), ref_wcs, (size_px, size_px), target_coord=targets[start + i])
            )
        del data

    if not prepared:
        raise JobError("IRSA_ERROR", "None of the images could be downloaded", "Try again in a few minutes.")

    ctx.progress(total, total, "drawing frames")
    stretch = render.shared_stretch([p.image for p in prepared])
    if stretch is None:
        raise JobError("NO_COVERAGE", "The images cover this spot but contain no valid pixels")
    for p in prepared:
        cache.put(f"frames/{p.frame.id}.webp", render.to_webp(p.image, stretch), "image/webp")
        cache.put(f"frames/{p.frame.id}_flags.png", render.render_flag_mask_png(p.masks), "image/png")

    by_epoch: dict[int, list[float]] = {}
    for p in prepared:
        by_epoch.setdefault(p.frame.epoch_index, []).append(p.frame.mjd)
    epochs = [Epoch(index=i, mjd_start=min(m), mjd_end=max(m), n_frames=len(m)) for i, m in sorted(by_epoch.items())]
    skipped = total - len(prepared)
    if skipped:
        prepared[0].frame.notes.append(f"{skipped} image(s) could not be downloaded and are left out")

    return TimelapseResult(
        schema_version="1.0",
        request=req.model_copy(update={"schema_version": "1.0"}),
        grid=grid,
        epochs=epochs,
        frames=[p.frame for p in prepared],
        stretch=stretch,
        flag_legend=frames.flag_legend(prepared[-1].bits, prepared[-1].descriptions),
        provenance=Provenance(tap_query=None, generated_utc=datetime.now(UTC), code_version=code_version),
    )
