"""D3.2: Gaia DR3 and AllWISE overlays for SPHEREx fields.

Queries catalog sources around a field, propagates astrometry to each frame date
(MJD) using proper motion and parallax, and projects coordinates to pixel space
via the SPHEREx FITS IMAGE WCS.
"""

from __future__ import annotations

import logging
import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import astropy.units as u
import pandas as pd
import pyvo
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.time import Time
from astropy.wcs import WCS

from planetes.contracts import AtMjd, OverlayCatalog, Overlays, OverlaySource

log = logging.getLogger("planetes.overlays")

IRSA_TAP_URL = "https://irsa.ipac.caltech.edu/TAP"
GAIA_TABLE = "gaia_dr3_source"
ALLWISE_TABLE = "allwise_p3as_psd"

GAIA_REF_EPOCH = 2016.0
ALLWISE_REF_EPOCH = 2010.5
GAIA_VIZIER_ID = "I/355/gaiadr3"
ALLWISE_VIZIER_ID = "II/328/allwise"


@dataclass(frozen=True, slots=True)
class ProjectedSource:
    """A catalog source projected onto a FITS image."""

    source_id: str
    catalog: str
    ra_deg: float
    dec_deg: float
    mjd: float
    pixel_x: float
    pixel_y: float
    inside: bool
    mag: float | None
    band: str | None


def _clean_float(val: Any) -> float | None:
    if val is None or pd.isna(val):
        return None
    try:
        f = float(val)
        return f if math.isfinite(f) else None
    except (TypeError, ValueError):
        return None


def propagate_position(
    ra_deg: float,
    dec_deg: float,
    pm_ra_masyr: float | None,
    pm_dec_masyr: float | None,
    parallax_mas: float | None,
    ref_epoch_jyear: float,
    target_mjd: float,
) -> tuple[float, float]:
    """Propagate ICRS coordinates to target MJD using space motion."""
    if pm_ra_masyr is None or pm_dec_masyr is None or not math.isfinite(pm_ra_masyr) or not math.isfinite(pm_dec_masyr):
        return ra_deg, dec_deg

    args: dict[str, Any] = {
        "ra": ra_deg * u.deg,
        "dec": dec_deg * u.deg,
        "pm_ra_cosdec": pm_ra_masyr * u.mas / u.yr,
        "pm_dec": pm_dec_masyr * u.mas / u.yr,
        "obstime": Time(ref_epoch_jyear, format="jyear"),
        "frame": "icrs",
    }
    if parallax_mas is not None and parallax_mas > 0 and math.isfinite(parallax_mas):
        args["distance"] = (1000.0 / parallax_mas) * u.pc

    try:
        moved = SkyCoord(**args).apply_space_motion(new_obstime=Time(target_mjd, format="mjd")).icrs
        return float(moved.ra.deg), float(moved.dec.deg)
    except Exception as exc:
        log.warning("Epoch propagation failed for (%s, %s): %s", ra_deg, dec_deg, exc)
        return ra_deg, dec_deg


def query_gaia_sources(
    ra_deg: float,
    dec_deg: float,
    radius_deg: float,
    mag_limit: float = 20.0,
    max_sources: int = 500,
    tap_service: pyvo.dal.TAPService | None = None,
) -> list[dict[str, Any]]:
    """Query Gaia DR3 sources within radius_deg from IRSA TAP."""
    tap = tap_service or pyvo.dal.TAPService(IRSA_TAP_URL)
    adql = f"""
    SELECT TOP {int(max_sources)}
        source_id, ra, dec, pmra, pmdec, parallax, phot_g_mean_mag, ref_epoch
    FROM {GAIA_TABLE}
    WHERE 1 = CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS', {ra_deg:.6f}, {dec_deg:.6f}, {radius_deg:.6f}))
      AND phot_g_mean_mag <= {mag_limit:.2f}
    ORDER BY phot_g_mean_mag ASC
    """
    res = tap.run_sync(adql).to_table()
    records: list[dict[str, Any]] = []
    for row in res:
        records.append(
            {
                "id": str(row["source_id"]),
                "ra": float(row["ra"]),
                "dec": float(row["dec"]),
                "pm_ra_masyr": _clean_float(row["pmra"]),
                "pm_dec_masyr": _clean_float(row["pmdec"]),
                "parallax_mas": _clean_float(row["parallax"]),
                "mag": _clean_float(row["phot_g_mean_mag"]),
                "band": "G",
                "ref_epoch": _clean_float(row["ref_epoch"]) or GAIA_REF_EPOCH,
            }
        )
    return records


def query_allwise_sources(
    ra_deg: float,
    dec_deg: float,
    radius_deg: float,
    mag_limit: float = 17.0,
    max_sources: int = 500,
    tap_service: pyvo.dal.TAPService | None = None,
) -> list[dict[str, Any]]:
    """Query AllWISE sources within radius_deg from IRSA TAP."""
    tap = tap_service or pyvo.dal.TAPService(IRSA_TAP_URL)
    adql = f"""
    SELECT TOP {int(max_sources)}
        designation, ra, dec, pmra, pmdec, w1mpro, w2mpro
    FROM {ALLWISE_TABLE}
    WHERE 1 = CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS', {ra_deg:.6f}, {dec_deg:.6f}, {radius_deg:.6f}))
      AND w1mpro <= {mag_limit:.2f}
    ORDER BY w1mpro ASC
    """
    res = tap.run_sync(adql).to_table()
    records: list[dict[str, Any]] = []
    for row in res:
        records.append(
            {
                "id": str(row["designation"]).strip(),
                "ra": float(row["ra"]),
                "dec": float(row["dec"]),
                "pm_ra_masyr": _clean_float(row["pmra"]),
                "pm_dec_masyr": _clean_float(row["pmdec"]),
                "parallax_mas": None,
                "mag": _clean_float(row["w1mpro"]),
                "band": "W1",
                "ref_epoch": ALLWISE_REF_EPOCH,
            }
        )
    return records


def build_overlay_catalog(
    name: str,
    vizier_id: str | None,
    ref_epoch: float | None,
    records: list[dict[str, Any]],
    mjds: Sequence[float],
) -> OverlayCatalog:
    """Build an OverlayCatalog object with source positions computed at each MJD."""
    sources: list[OverlaySource] = []
    for r in records:
        at_mjd_dict: dict[str, AtMjd] = {}
        for mjd in mjds:
            mjd_str = f"{mjd:.6f}".rstrip("0").rstrip(".")
            moved_ra, moved_dec = propagate_position(
                ra_deg=r["ra"],
                dec_deg=r["dec"],
                pm_ra_masyr=r.get("pm_ra_masyr"),
                pm_dec_masyr=r.get("pm_dec_masyr"),
                parallax_mas=r.get("parallax_mas"),
                ref_epoch_jyear=r.get("ref_epoch") or ref_epoch or 2016.0,
                target_mjd=mjd,
            )
            at_mjd_dict[mjd_str] = AtMjd([round(moved_ra, 7), round(moved_dec, 7)])

        sources.append(
            OverlaySource(
                id=str(r["id"]),
                ra=float(r["ra"]),
                dec=float(r["dec"]),
                pm_ra_masyr=r.get("pm_ra_masyr"),
                pm_dec_masyr=r.get("pm_dec_masyr"),
                mag=r.get("mag"),
                band=r.get("band"),
                at_mjd=at_mjd_dict,
            )
        )

    return OverlayCatalog(
        name=name,
        vizier=vizier_id,
        ref_epoch_jyear=ref_epoch,
        sources=sources,
    )


def build_overlays(
    gaia_records: list[dict[str, Any]],
    allwise_records: list[dict[str, Any]],
    mjds: Sequence[float],
) -> Overlays:
    """Produce the contract-validated Overlays data structure."""
    catalogs: list[OverlayCatalog] = []
    if gaia_records:
        catalogs.append(build_overlay_catalog("Gaia DR3", GAIA_VIZIER_ID, GAIA_REF_EPOCH, gaia_records, mjds))
    if allwise_records:
        catalogs.append(build_overlay_catalog("AllWISE", ALLWISE_VIZIER_ID, ALLWISE_REF_EPOCH, allwise_records, mjds))
    return Overlays(schema_version="1.0", catalogs=catalogs)


def project_sources_to_wcs(
    catalog: OverlayCatalog,
    header: fits.Header | dict[str, Any],
    mjd: float,
    image_shape: tuple[int, int] | None = None,
) -> list[ProjectedSource]:
    """Project catalog sources at MJD onto image pixels using the FITS WCS header."""
    w = WCS(header)
    ny, nx = image_shape or (
        int(header.get("NAXIS2", 100)),
        int(header.get("NAXIS1", 100)),
    )

    projected: list[ProjectedSource] = []
    mjd_str = f"{mjd:.6f}".rstrip("0").rstrip(".")

    for src in catalog.sources:
        # Check if pre-propagated position exists
        pos = src.at_mjd.get(mjd_str)
        if pos is not None:
            ra, dec = pos.root[0], pos.root[1]
        else:
            ra, dec = propagate_position(
                ra_deg=src.ra,
                dec_deg=src.dec,
                pm_ra_masyr=src.pm_ra_masyr,
                pm_dec_masyr=src.pm_dec_masyr,
                parallax_mas=None,
                ref_epoch_jyear=catalog.ref_epoch_jyear or 2016.0,
                target_mjd=mjd,
            )

        px, py = w.all_world2pix(ra, dec, 0)
        px_f, py_f = float(px), float(py)
        inside = 0 <= px_f < nx and 0 <= py_f < ny

        projected.append(
            ProjectedSource(
                source_id=src.id,
                catalog=catalog.name,
                ra_deg=ra,
                dec_deg=dec,
                mjd=mjd,
                pixel_x=px_f,
                pixel_y=py_f,
                inside=inside,
                mag=src.mag,
                band=src.band,
            )
        )

    return projected


def aladin_catalog_config(catalog_name: str) -> dict[str, Any]:
    """Return Aladin Lite layer configuration options for the catalog."""
    if catalog_name.lower().startswith("gaia"):
        return {
            "name": "Gaia DR3",
            "color": "#388bfd",
            "shape": "circle",
            "sourceSize": 12,
            "lineWidth": 1.5,
        }
    elif catalog_name.lower().startswith("allwise") or "wise" in catalog_name.lower():
        return {
            "name": "AllWISE",
            "color": "#f0883e",
            "shape": "square",
            "sourceSize": 14,
            "lineWidth": 1.5,
        }
    return {
        "name": catalog_name,
        "color": "#7ee787",
        "shape": "cross",
        "sourceSize": 10,
        "lineWidth": 1.0,
    }
