"""D3.1: resolve astronomical targets and propagate ICRS positions.

Coordinates are ICRS degrees; proper motions and parallax are mas/year and
mas respectively; epochs are Julian years; ``position_at`` accepts MJD days.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import math
import re
from typing import Any

import astropy.units as u
from astropy.coordinates import SkyCoord
from astropy.time import Time
from astropy.utils import data as astropy_data
from astroquery.gaia import Gaia
from astroquery.simbad import Simbad

from planetes.contracts import Resolved

GAIA_EPOCH_JYEAR = 2016.0
GAIA_MATCH_RADIUS_ARCSEC = 30.0
astropy_data.conf.remote_timeout = 120

# Official benchmark IDs/names from docs/03 and web/src/lib/benchmarks.ts.
BENCHMARKS: dict[str, str] = {
    "barnard": "Barnard's Star",
    "wise0855": "WISE 0855-0714",
    "epsindib": "Epsilon Indi Ba/Bb",
    "rwaur": "RW Aurigae",
    "rdra": "R Draconis",
}


@dataclass(frozen=True, slots=True)
class Astrometry:
    """Catalog position and motion. RA/Dec are at ``ref_epoch_jyear``."""

    query: str
    name: str | None
    ra_deg: float
    dec_deg: float
    ref_epoch_jyear: float | None
    pm_ra_masyr: float | None
    pm_dec_masyr: float | None
    parallax_mas: float | None
    source: str

    def to_contract(self) -> Resolved:
        """Convert this result to the repository's generated Resolved model."""
        return Resolved(
            schema_version="1.0",
            query=self.query,
            name=self.name,
            ra=self.ra_deg,
            dec=self.dec_deg,
            ref_epoch_jyear=self.ref_epoch_jyear,
            pm_ra_masyr=self.pm_ra_masyr,
            pm_dec_masyr=self.pm_dec_masyr,
            parallax_mas=self.parallax_mas,
            source=self.source,
        )

    def position_at(self, mjd: float) -> SkyCoord:
        """Return ICRS position at Modified Julian Date ``mjd``."""
        if not math.isfinite(float(mjd)):
            raise ValueError("mjd must be a finite number")
        if self.ref_epoch_jyear is None:
            raise ValueError("reference epoch is unknown; cannot propagate position")
        if self.pm_ra_masyr is None or self.pm_dec_masyr is None:
            raise ValueError("proper motion is incomplete; cannot propagate position")

        # Gaia's pmra is μα*cos(dec). Astropy names this pm_ra_cosdec.
        args: dict[str, Any] = {
            "ra": self.ra_deg * u.deg,
            "dec": self.dec_deg * u.deg,
            "pm_ra_cosdec": self.pm_ra_masyr * u.mas / u.yr,
            "pm_dec": self.pm_dec_masyr * u.mas / u.yr,
            "obstime": Time(self.ref_epoch_jyear, format="jyear"),
            "frame": "icrs",
        }
        if self.parallax_mas is not None and self.parallax_mas > 0:
            # Distance enables perspective acceleration when available.
            args["distance"] = (1000.0 / self.parallax_mas) * u.pc

        return SkyCoord(**args).apply_space_motion(
            new_obstime=Time(float(mjd), format="mjd")
        ).icrs


def position_at(target: Astrometry, mjd: float) -> SkyCoord:
    """Convenience function returning target ICRS position at MJD days."""
    return target.position_at(mjd)


def _coordinate_input(query: str) -> SkyCoord | None:
    """Parse explicit decimal-degree input as ``'RA, Dec'``."""
    match = re.fullmatch(
        r"\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+))\s*[, ]\s*"
        r"([+-]?(?:\d+(?:\.\d*)?|\.\d+))\s*",
        query,
    )
    if not match:
        return None
    ra_deg, dec_deg = map(float, match.groups())
    if not 0 <= ra_deg < 360:
        raise ValueError("RA must be in [0, 360) degrees")
    if not -90 <= dec_deg <= 90:
        raise ValueError("Dec must be in [-90, 90] degrees")
    return SkyCoord(ra=ra_deg * u.deg, dec=dec_deg * u.deg, frame="icrs")


def _value(row: Any, column: str) -> float | None:
    """Return a finite unmasked scalar from an Astropy row."""
    try:
        item = row[column]
        if item is None or bool(getattr(item, "mask", False)):
            return None
        number = float(item)
        return number if math.isfinite(number) else None
    except (KeyError, TypeError, ValueError, IndexError):
        return None


def _string(row: Any, column: str) -> str | None:
    try:
        item = row[column]
        if item is None or bool(getattr(item, "mask", False)):
            return None
        result = str(item).strip()
        return result or None
    except (KeyError, TypeError, ValueError, IndexError):
        return None


def _epoch(value: str | None) -> float | None:
    """Parse SIMBAD epochs such as J2000.0; never guess an absent epoch."""
    if value is None:
        return None
    match = re.search(r"([+-]?\d+(?:\.\d+)?)", value)
    return float(match.group(1)) if match else None


def _simbad_resolve(name: str) -> tuple[SkyCoord, dict[str, float | None], str]:
    """Resolve object identity and available astrometry through SIMBAD."""
    simbad = Simbad()
    for field in ("pm", "plx", "coo_epoch"):
        try:
            simbad.add_votable_fields(field)
        except Exception:
            # Continue; absent optional columns remain None.
            pass

    result = simbad.query_object(name)
    if result is None or len(result) == 0:
        raise LookupError(f"SIMBAD did not resolve {name!r}")

    row = result[0]
    ra_text, dec_text = _string(row, "ra"), _string(row, "dec")
    if not ra_text or not dec_text:
        raise LookupError(f"SIMBAD returned no usable coordinates for {name!r}")
    coord = SkyCoord(ra_text, dec_text, unit=(u.hourangle, u.deg), frame="icrs")
    values = {
        "epoch": _epoch(_string(row, "coo_epoch")),
        "pmra": _value(row, "pmra"),
        "pmdec": _value(row, "pmdec"),
        "parallax": _value(row, "plx_value"),
    }
    return coord, values, _string(row, "main_id") or name


@lru_cache(maxsize=1)
def _gaia_source_columns() -> frozenset[str]:
    """Inspect Gaia DR3 table metadata before using catalogue column names."""
    table = Gaia.load_table("gaiadr3.gaia_source")
    columns = frozenset(column.name.lower() for column in table.columns)
    required = {"source_id", "ra", "dec", "pmra", "pmdec", "parallax", "ref_epoch"}
    missing = required - columns
    if missing:
        raise RuntimeError(f"Gaia DR3 schema is missing required columns: {sorted(missing)}")
    return columns


def _gaia_match(coord: SkyCoord) -> dict[str, float | None] | None:
    """Nearest Gaia DR3 source within 30 arcsec of the supplied ICRS position."""
    _gaia_source_columns()  # Verify actual TAP table columns before querying.
    ra_deg, dec_deg = coord.icrs.ra.deg, coord.icrs.dec.deg
    radius_deg = GAIA_MATCH_RADIUS_ARCSEC / 3600.0
    adql = f"""
        SELECT TOP 1 source_id, ra, dec, pmra, pmdec, parallax, ref_epoch,
          DISTANCE(POINT('ICRS', ra, dec),
                   POINT('ICRS', {ra_deg:.12f}, {dec_deg:.12f})) AS angular_distance
        FROM gaiadr3.gaia_source
        WHERE 1 = CONTAINS(
          POINT('ICRS', ra, dec),
          CIRCLE('ICRS', {ra_deg:.12f}, {dec_deg:.12f}, {radius_deg:.12f})
        )
        ORDER BY angular_distance ASC
    """
    job = Gaia.launch_job_async(adql, dump_to_file=False)
    rows = job.get_results()
    if rows is None or len(rows) == 0:
        return None
    row = rows[0]
    return {
        "ra": _value(row, "ra"),
        "dec": _value(row, "dec"),
        "pmra": _value(row, "pmra"),
        "pmdec": _value(row, "pmdec"),
        "parallax": _value(row, "parallax"),
        "epoch": _value(row, "ref_epoch"),
    }


def resolve(query: str) -> Astrometry:
    """Resolve a star name or decimal-degree ``'RA, Dec'`` via SIMBAD/Gaia.

    Network access to CDS and ESA Gaia Archive is required. SIMBAD supplies
    identity/initial position; its proper motion is used to move high-motion
    cross-match centres to Gaia's epoch where available. Gaia DR3 astrometry
    is preferred when a match is found. Missing measurements stay null.
    """
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query must be a non-empty name or 'RA, Dec'")
    query = query.strip()

    coord = _coordinate_input(query)
    canonical_name: str | None = None
    simbad_values: dict[str, float | None] = {
        "epoch": None, "pmra": None, "pmdec": None, "parallax": None
    }
    source = "User-supplied ICRS coordinates"

    if coord is None:
        coord, simbad_values, canonical_name = _simbad_resolve(query)
        source = "SIMBAD"

    # SIMBAD coordinates can be at an older epoch. Move the cone centre to
    # Gaia's epoch before matching high-proper-motion targets.
    match_coord = coord
    if (
        simbad_values["epoch"] is not None
        and simbad_values["pmra"] is not None
        and simbad_values["pmdec"] is not None
    ):
        simbad_motion = SkyCoord(
            ra=coord.ra,
            dec=coord.dec,
            pm_ra_cosdec=simbad_values["pmra"] * u.mas / u.yr,
            pm_dec=simbad_values["pmdec"] * u.mas / u.yr,
            obstime=Time(simbad_values["epoch"], format="jyear"),
            frame="icrs",
        )
        match_coord = simbad_motion.apply_space_motion(
            new_obstime=Time(GAIA_EPOCH_JYEAR, format="jyear")
        )

    gaia_values = _gaia_match(match_coord)
    if gaia_values is not None:
        # Gaia coordinates and Gaia proper motions share ref_epoch.
        if gaia_values["ra"] is not None and gaia_values["dec"] is not None:
            coord = SkyCoord(
                ra=gaia_values["ra"] * u.deg,
                dec=gaia_values["dec"] * u.deg,
                frame="icrs",
            )
        values = gaia_values
        source = "SIMBAD + Gaia DR3" if canonical_name else "Gaia DR3"
    else:
        values = simbad_values

    return Astrometry(
        query=query,
        name=canonical_name,
        ra_deg=float(coord.icrs.ra.deg),
        dec_deg=float(coord.icrs.dec.deg),
        ref_epoch_jyear=values["epoch"],
        pm_ra_masyr=values["pmra"],
        pm_dec_masyr=values["pmdec"],
        parallax_mas=values["parallax"],
        source=source,
    )


def resolve_response(query: str) -> Resolved:
    """Resolve a target and return the generated API response model."""
    return resolve(query).to_contract()
