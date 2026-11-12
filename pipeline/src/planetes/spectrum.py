"""Spectrum on the fly (D4.1 science layer on top of the photometry engine).

For a position: every SPHEREx exposure that covers it (QR2 + QR3), forced photometry at the object's
position on that exposure's date, then plain-language rejection rules and simultaneous-pair ids
(D1&D4, D2&D5, D3&D6 see the same sky at the same moment). Output: the SpectrumResult contract.
Rejected points are kept with their reason so the chart can show them greyed out.
A point is also rejected when another Gaia star sits inside the measuring circle (blend check): the 3-pixel
aperture is ~19 arcsec wide in radius, so a faint target next to a brighter star would otherwise report that
star's light.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable

import astropy.units as u
import pandas as pd
from astropy.coordinates import SkyCoord
from astropy.time import Time

from .access import extract_release, fetch_cutouts, find_frames
from .cache import Cache
from .contracts import (
    Detector,
    SpectrumPoint,
    SpectrumProvenance,
    SpectrumRequest,
    SpectrumResult,
    SpectrumSummary,
    SpectrumTarget,
)
from .frames import INFORMATIONAL_FLAGS
from .overlays import propagate_position, query_gaia_sources
from .photometry import APERTURE_PX, PointFlux, measure

MIN_SNR = 3.0
MISSION_MID_MJD = 61041.0  # 2026-01-01, middle of the SPHEREx data so far
CUTOUT_DEG = 0.05  # ~29 SPHEREx pixels: room for the aperture, the sky annulus and the motion
SPHEREX_PIXEL_ARCSEC = 6.15  # from a real cutout WCS (6.15-6.16"); only sizes the blend check
BLEND_RADIUS_ARCSEC = (APERTURE_PX + 0.5) * SPHEREX_PIXEL_ARCSEC  # aperture plus half a pixel
SELF_MATCH_ARCSEC = 3.0  # a Gaia star this close to the predicted position is the target itself (or its pair)
BLEND_GAIA_G_MAX = 18.0  # fainter neighbours are below SPHEREx's single-exposure noise
PAIRS = {1: "14", 4: "14", 2: "25", 5: "25", 3: "36", 6: "36"}

REASONS = {
    "outside": "Not covered by this exposure.",
    "saturated": "Too bright here: SPHEREx's pixels are saturated, so this point is not used.",
    "bad_pixels": "Could not be measured: some pixels on the source have no valid value.",
    "no_sky": "Could not be measured: no clean sky around the source to subtract.",
    "faint": "Too faint in this exposure (signal-to-noise below 3).",
}


def pair_id(obs_id: str, detector: int) -> str | None:
    """Exposure id + detector pair, e.g. '2025W33_2C_0321_1/D36'. Same id = same sky at the same moment."""
    if "?" not in obs_id or "/D" not in obs_id:
        return None
    exposure = obs_id.split("?", 1)[1].rsplit("/D", 1)[0]
    return f"{exposure}/D{PAIRS[detector]}"


def reject_reason(m: PointFlux) -> str | None:
    """Why a point is not used, in plain words; None when it is used."""
    if m.problem == "outside":
        return REASONS["outside"]
    if m.saturated:
        return REASONS["saturated"]
    bad = [n for n in m.flag_names if n not in INFORMATIONAL_FLAGS]
    if bad:
        return "SPHEREx flagged pixels on the source (" + ", ".join(bad) + "), so this point is not used."
    if m.problem in ("bad_pixels", "no_sky"):
        return REASONS[m.problem]
    if m.flux_ujy is None or m.snr is None or m.snr < MIN_SNR:
        return REASONS["faint"]
    return None


Neighbour = tuple[str, float, float, float | None]  # Gaia source_id, RA, Dec at mission mid, G mag


def blend_reason(ra_deg: float, dec_deg: float, neighbours: list[Neighbour]) -> str | None:
    """Plain-language reason when another catalogued star is inside the measuring circle, else None."""
    here = SkyCoord(ra_deg * u.deg, dec_deg * u.deg)
    for _sid, nra, ndec, mag in neighbours:
        sep = float(here.separation(SkyCoord(nra * u.deg, ndec * u.deg)).arcsec)
        if SELF_MATCH_ARCSEC < sep <= BLEND_RADIUS_ARCSEC:
            g = f"G {mag:.1f} " if mag is not None else ""
            return (
                f"Another star ({g}Gaia DR3) is {sep:.0f}″ away, inside the measuring circle, "
                "so this point is not used."
            )
    return None


def neighbours_near(ra_deg: float, dec_deg: float, search_arcsec: float = 90.0) -> list[Neighbour]:
    """Gaia DR3 stars (G <= BLEND_GAIA_G_MAX) around the target, moved to mission mid."""
    rows = query_gaia_sources(ra_deg, dec_deg, search_arcsec / 3600.0, mag_limit=BLEND_GAIA_G_MAX)
    out: list[Neighbour] = []
    for r in rows:
        nra, ndec = propagate_position(
            r["ra"], r["dec"], r["pm_ra_masyr"], r["pm_dec_masyr"], None, r["ref_epoch"], MISSION_MID_MJD
        )
        out.append((r["id"], nra, ndec, r["mag"]))
    return out


def positions_at(req: SpectrumRequest, mjds: list[float]) -> list[tuple[float, float]]:
    """The object at each exposure date: moved for proper motion when given (pm_ra is μα·cos δ, Gaia's convention)."""
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


def build_points(
    frames: pd.DataFrame,
    cutouts: dict[str, bytes],
    req: SpectrumRequest,
    neighbours: list[Neighbour] | None = None,
) -> list[SpectrumPoint]:
    rows = frames.sort_values("mjd").to_dict("records")
    where = positions_at(req, [float(r["mjd"]) for r in rows])
    points: list[SpectrumPoint] = []
    for row, (ra, dec) in zip(rows, where, strict=True):
        data = cutouts.get(f"cutouts/{row['frame_id']}.fits")
        if data is None:
            continue
        m = measure(data, ra, dec)
        reason = reject_reason(m)
        if reason is None and neighbours:
            reason = blend_reason(ra, dec, neighbours)
        det = int(row["detector"])
        obs_id = str(row["obs_id"])
        points.append(
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
                ra=ra % 360.0,
                dec=dec,
            )
        )
    return points


def summarise(points: list[SpectrumPoint]) -> SpectrumSummary:
    used = [p for p in points if p.used]
    return SpectrumSummary(
        n_points=len(points),
        n_used=len(used),
        n_rejected=len(points) - len(used),
        bands_covered=[Detector(d) for d in sorted({p.detector for p in used})],
    )


def release_of(points: list[SpectrumPoint]) -> str:
    """Contract keeps one release: the one most used points came from (each point's obs_id names its own)."""
    counts = Counter(extract_release(p.obs_id) for p in points if p.used)
    return counts.most_common(1)[0][0] if counts else "QR3"


def build_spectrum(
    req: SpectrumRequest,
    code_version: str,
    cache: Cache | None = None,
    workers: int = 8,
    progress: Callable[[int, int | None, str], None] | None = None,
) -> SpectrumResult:
    if progress:
        progress(0, None, "searching")
    # Centre the search on where the object is during the mission (fast movers drift out of a 2016-centred cutout).
    centre_ra, centre_dec = positions_at(req, [MISSION_MID_MJD])[0]
    frames = find_frames(centre_ra % 360.0, centre_dec, size_deg=CUTOUT_DEG, release=req.release)
    if progress:
        progress(0, len(frames), "downloading")
    cutouts = fetch_cutouts(frames, max_concurrent=workers, cache=cache) if len(frames) else {}
    if progress:
        progress(len(cutouts), len(frames), "measuring")
    neighbours = neighbours_near(centre_ra % 360.0, centre_dec)
    points = build_points(frames, cutouts, req, neighbours)
    return SpectrumResult(
        schema_version="1.0",
        target=SpectrumTarget(ra=req.ra, dec=req.dec, pm=req.pm),
        points=points,
        summary=summarise(points),
        provenance=SpectrumProvenance(release=release_of(points), code_version=code_version),
    )
