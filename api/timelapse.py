"""Time-lapse job: POST /api/timelapse -> planetes.access (find + download) -> planetes.frames (align) ->
planetes.stack (coadd / difference / sum / color) -> planetes.render (shared stretch, WebP, flag overlay) ->
files in the cache and a TimelapseResult.
"""

from __future__ import annotations

import hashlib
import math
from datetime import UTC, datetime

import astropy.units as u
import numpy as np
import pandas as pd
from astropy.coordinates import SkyCoord
from astropy.time import Time

from planetes import access, frames, render, stack
from planetes.cache import Cache
from planetes.contracts import Detector, Epoch, Frame, Provenance, TimelapseRequest, TimelapseResult

from .jobs import JobContext, JobError

BATCH = 8
MAX_GRID_PX = 300


def _derived_frame_id(tag: str) -> str:
    """Deterministic f_<12-hex> id matching FRAME_ID_RE in api/main.py."""
    digest = hashlib.sha256(tag.encode("utf-8")).hexdigest()[:12]
    return f"f_{digest}"


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
    ctx.progress(0, None, "asking NASA's archive which images cover this spot")
    found = _search(req.ra, req.dec, req)
    center = (req.ra, req.dec)
    if req.pm is not None:
        center = target_positions(req, [float(found["mjd"].median())])[0]
        found = _search(center[0], center[1], req)
    chosen = pick_evenly(found.sort_values("mjd").reset_index(drop=True), req.max_frames)

    size_px = min(MAX_GRID_PX, math.ceil(req.fov_deg / frames.SPHEREX_PIXEL_SCALE_DEG))
    ref_wcs, grid = frames.make_reference_grid(center[0], center[1], size_pixels=size_px)
    targets = target_positions(req, chosen["mjd"].astype(float).tolist())

    prepared: list[frames.PreparedFrame] = []
    var_maps: list[np.ndarray] = []
    good_masks: list[np.ndarray] = []

    total = len(chosen)
    for start in range(0, total, BATCH):
        batch = chosen.iloc[start : start + BATCH]
        ctx.progress(start, total, "downloading and aligning images")
        data = access.fetch_cutouts(batch, max_concurrent=concurrency, cache=cache)
        for i, (_, row) in enumerate(batch.iterrows()):
            blob = data.get(f"cutouts/{row['frame_id']}.fits")
            if blob is None:
                continue
            pf = frames.prepare_frame(blob, row.to_dict(), ref_wcs, (size_px, size_px), target_coord=targets[start + i])
            prepared.append(pf)
            if req.mode != "exposures":
                _, r_var, r_good = stack.prepare_reprojected_variance(blob, ref_wcs, (size_px, size_px))
                var_maps.append(r_var)
                good_masks.append(r_good)
        del data

    if not prepared:
        raise JobError("IRSA_ERROR", "None of the images could be downloaded", "Try again in a few minutes.")

    by_epoch: dict[int, list[float]] = {}
    for p in prepared:
        by_epoch.setdefault(p.frame.epoch_index, []).append(p.frame.mjd)
    epochs = [Epoch(index=i, mjd_start=min(m), mjd_end=max(m), n_frames=len(m)) for i, m in sorted(by_epoch.items())]
    legend = frames.flag_legend(prepared[-1].bits, prepared[-1].descriptions)

    if req.mode == "exposures":
        ctx.progress(total, total, "drawing frames")
        stretch = render.shared_stretch([p.image for p in prepared])
        if stretch is None:
            raise JobError("NO_COVERAGE", "The images cover this spot but contain no valid pixels")
        for p in prepared:
            cache.put(f"frames/{p.frame.id}.webp", render.to_webp(p.image, stretch, p.masks.saturated), "image/webp")
            cache.put(f"frames/{p.frame.id}_flags.png", render.render_flag_mask_png(p.masks), "image/png")

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
            flag_legend=legend,
            provenance=Provenance(tap_query=None, generated_utc=datetime.now(UTC), code_version=code_version),
        )

    # --- D2.3 Derived Modes: stacks, difference, sum, color ---
    ctx.progress(total, total, f"computing {req.mode} products")
    blank_flags = render.render_flag_mask_png(
        frames.FlagMasks(
            saturated=np.zeros((size_px, size_px), dtype=bool),
            cosmic=np.zeros((size_px, size_px), dtype=bool),
            other=np.zeros((size_px, size_px), dtype=bool),
            outside=np.zeros((size_px, size_px), dtype=bool),
        )
    )

    # Group by (epoch_index, detector) -> per-epoch per-detector inverse-variance stacks
    grouped: dict[tuple[int, int], list[int]] = {}
    for idx, p in enumerate(prepared):
        grouped.setdefault((p.frame.epoch_index, int(p.frame.detector.root)), []).append(idx)

    epoch_det_coadds: dict[tuple[int, int], tuple[stack.CoaddResult, list[str]]] = {}
    for (ep_idx, det_num), idxs in sorted(grouped.items()):
        coadd = stack.inverse_variance_stack(
            images=[prepared[i].image for i in idxs],
            variances=[var_maps[i] for i in idxs],
            good_masks=[good_masks[i] for i in idxs],
            detector=det_num,
            epoch_index=ep_idx,
            mjds=[prepared[i].frame.mjd for i in idxs],
            wavelengths=[prepared[i].frame.wavelength_um for i in idxs],
        )
        members = [prepared[i].frame.obs_id for i in idxs]
        epoch_det_coadds[(ep_idx, det_num)] = (coadd, members)

    out_frames: list[Frame] = []
    out_images: list[np.ndarray] = []

    if req.mode == "stacks":
        coadd_list = list(epoch_det_coadds.items())
        stretch = render.shared_stretch([c.image for _, (c, _) in coadd_list])
        if stretch is None:
            raise JobError("NO_COVERAGE", "Stacked images contain no valid pixels")
        for (ep_idx, det_num), (coadd, members) in coadd_list:
            mjd_mid = 0.5 * (coadd.mjd_start + coadd.mjd_end)
            fid = _derived_frame_id(f"stack:{req.release}:{center}:{ep_idx}:{det_num}:{members}")
            cache.put(f"frames/{fid}.webp", render.to_webp(coadd.image, stretch), "image/webp")
            cache.put(f"frames/{fid}_flags.png", blank_flags, "image/png")
            t_pos = target_positions(req, [mjd_mid])[0]
            out_frames.append(
                Frame(
                    id=fid,
                    kind="stack",
                    obs_id=f"stack_e{ep_idx}_d{det_num}",
                    members=members,
                    release=req.release,
                    epoch_index=ep_idx,
                    mjd=mjd_mid,
                    utc=frames.mjd_to_utc(mjd_mid),
                    detector=Detector(det_num),
                    wavelength_um=coadd.wavelength_um,
                    bandwidth_um=None,
                    image_url=f"/api/frames/{fid}.webp",
                    flags_url=f"/api/frames/{fid}/flags.png",
                    flagged_frac=float(np.mean(coadd.coverage == 0)),
                    saturated_near_center=False,
                    target_xy=frames.compute_target_xy(t_pos[0], t_pos[1], ref_wcs),
                    notes=[f"Inverse-variance coadd of {coadd.n_frames} frame(s)"],
                )
            )
            out_images.append(coadd.image)

    elif req.mode == "difference":
        by_det: dict[int, list[tuple[int, stack.CoaddResult, list[str]]]] = {}
        for (ep_idx, det_num), (coadd, members) in sorted(epoch_det_coadds.items()):
            by_det.setdefault(det_num, []).append((ep_idx, coadd, members))

        diffs: list[tuple[int, stack.CoaddResult, list[str]]] = []
        for det_num, items in sorted(by_det.items()):
            if len(items) < 2:
                continue
            ep_a_idx, coadd_a, mem_a = items[0]
            for ep_b_idx, coadd_b, mem_b in items[1:]:
                diff_coadd = stack.difference_coadds(coadd_a, coadd_b)
                diffs.append((det_num, diff_coadd, mem_a + mem_b))

        if not diffs:
            raise JobError(
                "NO_COVERAGE",
                "Need at least 2 epochs on the same detector to compute a difference image",
                "Widen the date range or select more frames.",
            )

        stretch = render.shared_stretch([d.image for _, d, _ in diffs])
        for det_num, diff_coadd, members in diffs:
            mjd_mid = diff_coadd.mjd_end
            fid = _derived_frame_id(f"diff:{req.release}:{center}:{det_num}:{members}")
            cache.put(f"frames/{fid}.webp", stack.difference_to_webp(diff_coadd), "image/webp")
            cache.put(f"frames/{fid}_flags.png", blank_flags, "image/png")
            t_pos = target_positions(req, [mjd_mid])[0]
            out_frames.append(
                Frame(
                    id=fid,
                    kind="difference",
                    obs_id=f"diff_d{det_num}",
                    members=members,
                    release=req.release,
                    epoch_index=diff_coadd.epoch_index or 0,
                    mjd=mjd_mid,
                    utc=frames.mjd_to_utc(mjd_mid),
                    detector=Detector(det_num),
                    wavelength_um=diff_coadd.wavelength_um,
                    bandwidth_um=None,
                    image_url=f"/api/frames/{fid}.webp",
                    flags_url=f"/api/frames/{fid}/flags.png",
                    flagged_frac=float(np.mean(diff_coadd.coverage == 0)),
                    saturated_near_center=False,
                    target_xy=frames.compute_target_xy(t_pos[0], t_pos[1], ref_wcs),
                    notes=[f"Epoch difference (MJD {diff_coadd.mjd_end:.1f} - {diff_coadd.mjd_start:.1f})"],
                )
            )
            out_images.append(diff_coadd.image)

    elif req.mode == "sum":
        by_det_sum: dict[int, list[tuple[stack.CoaddResult, list[str]]]] = {}
        for (_, det_num), (coadd, members) in sorted(epoch_det_coadds.items()):
            by_det_sum.setdefault(det_num, []).append((coadd, members))

        summed: list[tuple[int, stack.CoaddResult, list[str]]] = []
        for det_num, items in sorted(by_det_sum.items()):
            deep = stack.sum_coadds([c for c, _ in items])
            all_mem = [m for _, mem in items for m in mem]
            summed.append((det_num, deep, all_mem))

        stretch = render.shared_stretch([s.image for _, s, _ in summed])
        if stretch is None:
            raise JobError("NO_COVERAGE", "Summed images contain no valid pixels")
        for det_num, deep, members in summed:
            mjd_mid = 0.5 * (deep.mjd_start + deep.mjd_end)
            fid = _derived_frame_id(f"sum:{req.release}:{center}:{det_num}:{members}")
            cache.put(f"frames/{fid}.webp", render.to_webp(deep.image, stretch), "image/webp")
            cache.put(f"frames/{fid}_flags.png", blank_flags, "image/png")
            t_pos = target_positions(req, [mjd_mid])[0]
            out_frames.append(
                Frame(
                    id=fid,
                    kind="sum",
                    obs_id=f"sum_d{det_num}",
                    members=members,
                    release=req.release,
                    epoch_index=0,
                    mjd=mjd_mid,
                    utc=frames.mjd_to_utc(mjd_mid),
                    detector=Detector(det_num),
                    wavelength_um=deep.wavelength_um,
                    bandwidth_um=None,
                    image_url=f"/api/frames/{fid}.webp",
                    flags_url=f"/api/frames/{fid}/flags.png",
                    flagged_frac=float(np.mean(deep.coverage == 0)),
                    saturated_near_center=False,
                    target_xy=frames.compute_target_xy(t_pos[0], t_pos[1], ref_wcs),
                    notes=[f"Multi-epoch deep sum of {deep.n_frames} frame(s)"],
                )
            )
            out_images.append(deep.image)

    elif req.mode == "color":
        det_coadds: dict[int, stack.CoaddResult] = {}
        all_members: list[str] = []
        for det_num in sorted({d for _, d in epoch_det_coadds}):
            items = [c for (_, d), (c, _) in epoch_det_coadds.items() if d == det_num]
            det_coadds[det_num] = stack.sum_coadds(items)
            for (_, d), (_, mem) in epoch_det_coadds.items():
                if d == det_num:
                    all_members.extend(mem)

        rgb = stack.colour_composite(det_coadds)
        mjd_mid = float(np.median([p.frame.mjd for p in prepared]))
        fid = _derived_frame_id(f"color:{req.release}:{center}:{all_members}")
        cache.put(f"frames/{fid}.webp", stack.colour_to_webp(rgb), "image/webp")
        cache.put(f"frames/{fid}_flags.png", blank_flags, "image/png")
        t_pos = target_positions(req, [mjd_mid])[0]
        stretch = render.shared_stretch([c.image for c in det_coadds.values()])
        rep_det = sorted(det_coadds.keys())[0]
        out_frames.append(
            Frame(
                id=fid,
                kind="color",
                obs_id="color_rgb",
                members=all_members,
                release=req.release,
                epoch_index=0,
                mjd=mjd_mid,
                utc=frames.mjd_to_utc(mjd_mid),
                detector=Detector(rep_det),
                wavelength_um=None,
                bandwidth_um=None,
                image_url=f"/api/frames/{fid}.webp",
                flags_url=f"/api/frames/{fid}/flags.png",
                flagged_frac=0.0,
                saturated_near_center=False,
                target_xy=frames.compute_target_xy(t_pos[0], t_pos[1], ref_wcs),
                notes=["3-band RGB composite: Blue=D1+D2, Green=D3+D4, Red=D5+D6"],
            )
        )

    return TimelapseResult(
        schema_version="1.0",
        request=req.model_copy(update={"schema_version": "1.0"}),
        grid=grid,
        epochs=epochs,
        frames=out_frames,
        stretch=stretch,
        flag_legend=legend,
        provenance=Provenance(tap_query=None, generated_utc=datetime.now(UTC), code_version=code_version),
    )

