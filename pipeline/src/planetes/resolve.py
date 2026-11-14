"""D3.1: resolve astronomical targets and propagate ICRS positions.

Coordinates are ICRS degrees; proper motions and parallax are mas/year and
mas respectively; epochs are Julian years; ``position_at`` accepts MJD days.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import astropy.units as u
import pyvo
from astropy.coordinates import SkyCoord
from astropy.time import Time
from astropy.utils import data as astropy_data
from astroquery.simbad import Simbad

from planetes.contracts import Resolved

GAIA_EPOCH_JYEAR = 2016.0
astropy_data.conf.remote_timeout = 120

# Official benchmark IDs/names from docs/03 and web/src/lib/benchmarks.ts.
BENCHMARKS: dict[str, str] = {
    "barnard": "Barnard's Star",
    "wise0855": "WISE 0855-0714",
    "epsindib": "Epsilon Indi Ba/Bb",
    "rwaur": "RW Aurigae",
    "rdra": "R Draconis",
}
# Identifiers SIMBAD resolves for each benchmark (checked; the display names above do not all resolve).
BENCHMARK_QUERIES: dict[str, str] = {
    "barnard": "Barnard's Star",
    "wise0855": "WISE J085510.83-071442.5",
    "epsindib": "eps Ind B",
    "rwaur": "RW Aur",
    "rdra": "R Dra",
}
# CDS first, then the Harvard mirror (CDS SIMBAD returned 404 at the time). Same database.
SIMBAD_SERVERS = ("simbad.cds.unistra.fr", "simbad.harvard.edu")
# SIMBAD gives ICRS coordinates at epoch J2000.
SIMBAD_EPOCH_JYEAR = 2000.0


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

        return SkyCoord(**args).apply_space_motion(new_obstime=Time(float(mjd), format="mjd")).icrs


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


def _simbad_resolve(name: str) -> tuple[SkyCoord, dict[str, float | None], str, int | None]:
    """Identity, J2000 position, proper motion, parallax and Gaia DR3 id from SIMBAD.

    astroquery 0.4.11 (checked): `ra`/`dec` are float degrees; fields are `pmra`, `pmdec`,
    `plx_value`, `ids` (the old `pm` and `coo_epoch` no longer exist).
    """
    last_error: Exception | None = None
    for server in SIMBAD_SERVERS:
        try:
            simbad = Simbad()
            simbad.server = server
            simbad.add_votable_fields("pmra", "pmdec", "plx_value", "ids")
            result = simbad.query_object(name)
        except Exception as exc:  # server down (setup also contacts it): try the mirror
            last_error = exc
            continue
        if result is None or len(result) == 0:
            raise LookupError(f"SIMBAD did not resolve {name!r}")
        row = result[0]
        ra, dec = _value(row, "ra"), _value(row, "dec")
        if ra is None or dec is None:
            raise LookupError(f"SIMBAD returned no usable coordinates for {name!r}")
        ids = _string(row, "ids") or ""
        gaia = [i.split()[-1] for i in ids.split("|") if i.startswith("Gaia DR3 ")]
        values = {
            "epoch": SIMBAD_EPOCH_JYEAR,
            "pmra": _value(row, "pmra"),
            "pmdec": _value(row, "pmdec"),
            "parallax": _value(row, "plx_value"),
        }
        coord = SkyCoord(ra=ra * u.deg, dec=dec * u.deg, frame="icrs")
        return coord, values, _string(row, "main_id") or name, int(gaia[0]) if gaia else None
    raise LookupError(f"SIMBAD unreachable: {last_error}")


# Gaia DR3 via IRSA's copy (`gaia_dr3_source`, same values as ESA; checked when ESA's archive returned 503
# and astroquery.gaia failed on ESA's archive release 3.15). IRSA is already our SPHEREx source.
IRSA_TAP_URL = "https://irsa.ipac.caltech.edu/TAP"
GAIA_TABLE = "gaia_dr3_source"
GAIA_COLUMNS = ("source_id", "ra", "dec", "pmra", "pmdec", "parallax", "ref_epoch")


@lru_cache(maxsize=1)
def _irsa() -> pyvo.dal.TAPService:
    return pyvo.dal.TAPService(IRSA_TAP_URL)


def _gaia_by_id(source_id: int) -> dict[str, float | None] | None:
    """Gaia DR3 astrometry for one source_id (the id SIMBAD lists for the object)."""
    adql = f"SELECT {', '.join(GAIA_COLUMNS)} FROM {GAIA_TABLE} WHERE source_id = {int(source_id)}"
    rows = _irsa().run_sync(adql).to_table()
    if len(rows) == 0:
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
    """Resolve a star name, or decimal-degree ``'RA, Dec'``, to astrometry.

    Names: SIMBAD gives identity and its Gaia DR3 id; Gaia DR3 astrometry (epoch 2016.0) is used when that id
    exists, otherwise SIMBAD's own values (epoch J2000). Coordinates: kept exactly as typed, with no motion
    (matching a typed position to the nearest catalogue star could pick the wrong object). Missing stays None.
    """
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query must be a non-empty name or 'RA, Dec'")
    query = query.strip()

    coord = _coordinate_input(query)
    if coord is not None:
        return Astrometry(
            query=query,
            name=None,
            ra_deg=float(coord.ra.deg),
            dec_deg=float(coord.dec.deg),
            ref_epoch_jyear=None,
            pm_ra_masyr=None,
            pm_dec_masyr=None,
            parallax_mas=None,
            source="User-supplied ICRS coordinates",
        )

    coord, values, name, gaia_id = _simbad_resolve(query)
    source = "SIMBAD"
    if gaia_id is not None:
        gaia = _gaia_by_id(gaia_id)
        if gaia is not None and gaia["ra"] is not None and gaia["dec"] is not None:
            coord = SkyCoord(ra=gaia["ra"] * u.deg, dec=gaia["dec"] * u.deg, frame="icrs")
            values = gaia
            source = f"SIMBAD + Gaia DR3 {gaia_id}"

    return Astrometry(
        query=query,
        name=name,
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
