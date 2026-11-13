"""D3.4 Known asteroids in a SPHEREx frame, via JPL's Small-Body Identification API (SBIdent).

SPHEREx orbits ~7,000 km from Earth's centre, so for nearby asteroids a ground-based or geocentric prediction can be
off by more than a pixel. Every SPHEREx IMAGE header carries the spacecraft's geocentric position and velocity at
mid-exposure (X_SC/Y_SC/Z_SC in km, VX_SC/VY_SC/VZ_SC in km/s, XYZ_SC_SYSTEM = GEOCENTER, RADESYS ICRS), and SBIdent
accepts exactly that as `xobs` (geocentric ICRF state, km and km/s), so the predictions are for SPHEREx itself.

API: https://ssd-api.jpl.nasa.gov/doc/sb_ident.html (second pass = numerically integrated orbits).
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

import numpy as np
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.wcs import WCS

from .access import get_http_session

log = logging.getLogger(__name__)

SBIDENT_URL = "https://ssd-api.jpl.nasa.gov/sb_ident.api"
STATE_KEYS = ("X_SC", "Y_SC", "Z_SC", "VX_SC", "VY_SC", "VZ_SC")


@dataclass(frozen=True)
class KnownObject:
    name: str
    ra_deg: float
    dec_deg: float
    v_mag: float | None
    ra_rate_arcsec_h: float | None  # SBIdent "RA rate" (includes cos dec, as JPL reports it)
    dec_rate_arcsec_h: float | None


def spacecraft_xobs(header: fits.Header) -> str | None:
    """SBIdent `xobs` string from a SPHEREx IMAGE header; None if the state keys are missing."""
    if str(header.get("XYZ_SC_SYSTEM", "")).strip().upper() != "GEOCENTER":
        return None
    try:
        return ",".join(f"{float(header[k]):.9E}" for k in STATE_KEYS)
    except (KeyError, TypeError, ValueError):
        return None


def _sexagesimal(value_deg: float, hours: bool) -> str:
    v = value_deg / 15.0 if hours else value_deg
    sign = "M" if v < 0 else ""
    v = abs(v)
    d = int(v)
    m = int((v - d) * 60)
    s = (v - d - m / 60) * 3600
    return f"{sign}{d:02d}-{m:02d}-{s:05.2f}"


def _parse_ra(text: str) -> float:
    h, m, s = (float(x) for x in text.split(":"))
    return 15.0 * (h + m / 60 + s / 3600)


def _parse_dec(text: str) -> float:
    m = re.match(r"([+-])(\d+)\s+(\d+)'([\d.]+)", text.strip())
    if not m:
        raise ValueError(f"unexpected SBIdent Dec {text!r}")
    sign = -1.0 if m.group(1) == "-" else 1.0
    return sign * (float(m.group(2)) + float(m.group(3)) / 60 + float(m.group(4)) / 3600)


def _num(text: str) -> float | None:
    try:
        return float(text)
    except (TypeError, ValueError):
        return None


def parse_sbident(body: dict) -> list[KnownObject]:
    """Second-pass rows of an SBIdent JSON response, using the field names the response itself lists."""
    fields: list[str] = body.get("fields_second") or []
    rows: list[list[str]] = body.get("data_second_pass") or []
    if not rows:
        return []
    col = {name: i for i, name in enumerate(fields)}
    rate_ra = next((n for n in fields if n.startswith("RA rate")), None)
    rate_dec = next((n for n in fields if n.startswith("Dec rate")), None)
    if rate_ra and "deg/s" in rate_ra:  # some responses report deg/s; keep arcsec/h everywhere
        to_arcsec_h = 3600.0 * 3600.0
    else:
        to_arcsec_h = 1.0
    out = []
    for r in rows:
        ra_rate = _num(r[col[rate_ra]]) if rate_ra else None
        dec_rate = _num(r[col[rate_dec]]) if rate_dec else None
        out.append(
            KnownObject(
                name=r[col["Object name"]],
                ra_deg=_parse_ra(r[col["Astrometric RA (hh:mm:ss)"]]),
                dec_deg=_parse_dec(r[col["Astrometric Dec (dd mm'ss\")"]]),
                v_mag=_num(r[col["Visual magnitude (V)"]]),
                ra_rate_arcsec_h=ra_rate * to_arcsec_h if ra_rate is not None else None,
                dec_rate_arcsec_h=dec_rate * to_arcsec_h if dec_rate is not None else None,
            )
        )
    return out


def known_in_frame(
    header: fits.Header, wcs: WCS, shape: tuple[int, int], vmag_max: float | None = None
) -> list[KnownObject]:
    """Known asteroids and comets predicted inside a frame at its mid-exposure time, seen from SPHEREx.

    Raises if the header has no spacecraft state (never falls back to a geocentric guess silently).
    """
    xobs = spacecraft_xobs(header)
    if xobs is None:
        raise ValueError("frame header has no geocentric spacecraft state (X_SC..VZ_SC)")
    ny, nx = shape
    centre = wcs.pixel_to_world((nx - 1) / 2, (ny - 1) / 2)
    corners = wcs.pixel_to_world(np.array([0, nx - 1, 0, nx - 1]), np.array([0, 0, ny - 1, ny - 1]))
    half = float(max(centre.separation(corners).deg)) * 1.05
    params = {
        "xobs": xobs,
        "obs-time": str(header["DATE-AVG"]).replace("T", "_")[:19],
        "fov-ra-center": _sexagesimal(centre.ra.deg, hours=True),
        "fov-dec-center": _sexagesimal(centre.dec.deg, hours=False),
        "fov-ra-hwidth": f"{half:.4f}",
        "fov-dec-hwidth": f"{half:.4f}",
        "two-pass": "true",
        "suppress-first-pass": "true",
    }
    if vmag_max is not None:
        params["vmag-lim"] = f"{vmag_max:.1f}"
    resp = get_http_session().get(SBIDENT_URL, params=params, timeout=120)
    resp.raise_for_status()
    objs = parse_sbident(resp.json())
    inside = []
    for o in objs:
        x, y = wcs.world_to_pixel(SkyCoord(o.ra_deg, o.dec_deg, unit="deg"))
        if -0.5 <= float(x) <= nx - 0.5 and -0.5 <= float(y) <= ny - 0.5:
            inside.append(o)
    return inside
