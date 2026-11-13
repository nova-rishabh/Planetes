"""D3.4 known asteroids: header -> SBIdent observer state, and parsing a saved real SBIdent response (offline)."""

import json
from pathlib import Path

import pytest
from astropy.io import fits

from planetes.known import _parse_dec, _parse_ra, _sexagesimal, parse_sbident, spacecraft_xobs

DATA = Path(__file__).parent / "data"


def _header() -> fits.Header:
    # Values copied from a real QR2 cutout IMAGE header (2025W38_1A_0738_1, mid-exposure state).
    h = fits.Header()
    h["XYZ_SC_SYSTEM"] = "GEOCENTER"
    for k, v in {
        "X_SC": 1056.0309398360487,
        "Y_SC": 4879.707216822218,
        "Z_SC": 4936.222202749717,
        "VX_SC": 0.3607384895986599,
        "VY_SC": -5.394747644515335,
        "VZ_SC": 5.2518884215119925,
    }.items():
        h[k] = v
    return h


def test_xobs_from_header() -> None:
    xobs = spacecraft_xobs(_header())
    assert xobs is not None
    parts = [float(p) for p in xobs.split(",")]
    assert len(parts) == 6
    assert parts[0] == pytest.approx(1056.0309398, rel=1e-8)
    assert 6000 < (parts[0] ** 2 + parts[1] ** 2 + parts[2] ** 2) ** 0.5 < 8000  # SPHEREx ~7,000 km from Earth's centre


def test_xobs_missing_state_is_none() -> None:
    h = _header()
    del h["VZ_SC"]
    assert spacecraft_xobs(h) is None
    h2 = _header()
    h2["XYZ_SC_SYSTEM"] = "HELIOCENTER"
    assert spacecraft_xobs(h2) is None


def test_sexagesimal_round_trip() -> None:
    assert _sexagesimal(30.0, hours=True) == "02-00-00.00"
    assert _sexagesimal(-7.25, hours=False) == "M07-15-00.00"
    assert _parse_ra("02:00:00.00") == pytest.approx(30.0)
    assert _parse_dec("-07 15'00.0\"") == pytest.approx(-7.25)


def test_parse_real_sbident_response() -> None:
    body = json.loads((DATA / "sbident_xobs_2025-09-18.json").read_text(encoding="utf-8"))
    objs = parse_sbident(body)
    assert len(objs) == body["n_second_pass"]
    first = objs[0]
    assert first.name == body["data_second_pass"][0][0]
    assert 29.8 < first.ra_deg < 30.2 and 12.0 < first.dec_deg < 12.4
    assert first.v_mag is not None and first.ra_rate_arcsec_h is not None
