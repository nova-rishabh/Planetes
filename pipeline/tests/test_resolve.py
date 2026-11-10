"""D3.1 resolver tests. Network tests query the real SIMBAD and Gaia services."""

from __future__ import annotations

import astropy.units as u
import pytest
from astropy.coordinates import SkyCoord
from astropy.time import Time

from planetes.resolve import (
    BENCHMARK_QUERIES,
    BENCHMARKS,
    Astrometry,
    _coordinate_input,
)


def test_official_benchmark_ids() -> None:
    assert BENCHMARKS == {
        "barnard": "Barnard's Star",
        "wise0855": "WISE 0855-0714",
        "epsindib": "Epsilon Indi Ba/Bb",
        "rwaur": "RW Aurigae",
        "rdra": "R Draconis",
    }


@pytest.mark.parametrize(
    ("query", "ra", "dec"),
    [
        ("269.5, 4.7", 269.5, 4.7),
        ("0, -90", 0.0, -90.0),
        ("359.9, 90", 359.9, 90.0),
    ],
)
def test_decimal_coordinate_input(query: str, ra: float, dec: float) -> None:
    coord = _coordinate_input(query)
    assert coord is not None
    assert coord.ra.deg == pytest.approx(ra)
    assert coord.dec.deg == pytest.approx(dec)


@pytest.mark.parametrize("query", ["360, 0", "10, -91", "10, 91"])
def test_invalid_coordinates_rejected(query: str) -> None:
    with pytest.raises(ValueError):
        _coordinate_input(query)


def test_non_coordinate_name_is_not_parsed_as_coordinates() -> None:
    assert _coordinate_input("Barnard's Star") is None


def test_propagation_requires_epoch_and_both_motion_components() -> None:
    no_epoch = Astrometry("x", "x", 10, 20, None, 1, 2, 3, "test")
    with pytest.raises(ValueError, match="epoch"):
        no_epoch.position_at(61000)
    no_pm = Astrometry("x", "x", 10, 20, 2016.0, None, 2, 3, "test")
    with pytest.raises(ValueError, match="proper motion"):
        no_pm.position_at(61000)


def test_position_at_matches_astropy_space_motion() -> None:
    # Deterministic numerical test fixture; not a catalog result used by the app.
    target = Astrometry("fixture", "fixture", 269.4521, 4.6934, 2016.0, -802.8, 10362.5, 548.3, "test fixture")
    expected = SkyCoord(
        ra=269.4521 * u.deg,
        dec=4.6934 * u.deg,
        pm_ra_cosdec=-802.8 * u.mas / u.yr,
        pm_dec=10362.5 * u.mas / u.yr,
        distance=(1000 / 548.3) * u.pc,
        obstime=Time(2016.0, format="jyear"),
        frame="icrs",
    ).apply_space_motion(new_obstime=Time(2017.0, format="jyear"))
    actual = target.position_at(Time(2017.0, format="jyear").mjd)
    assert actual.separation(expected).to_value(u.mas) < 0.1


def test_barnard_scale_is_about_10_arcsec_per_year() -> None:
    # Check the documented scale independently of the resolver's network path.
    target = Astrometry("fixture", "fixture", 269.4521, 4.6934, 2016.0, -802.8, 10362.5, 548.3, "test fixture")
    start = SkyCoord(ra=target.ra_deg * u.deg, dec=target.dec_deg * u.deg, frame="icrs")
    moved = target.position_at(Time(2017.0, format="jyear").mjd)
    assert 9.5 < start.separation(moved).to_value(u.arcsec) < 11.5


def test_contract_model_matches_resolved_schema() -> None:
    target = Astrometry("target", "Target", 12.0, -4.0, 2016.0, 1.0, 2.0, 3.0, "Gaia DR3")
    payload = target.to_contract().model_dump()
    assert payload == {
        "schema_version": "1.0",
        "query": "target",
        "name": "Target",
        "ra": 12.0,
        "dec": -4.0,
        "ref_epoch_jyear": 2016.0,
        "pm_ra_masyr": 1.0,
        "pm_dec_masyr": 2.0,
        "parallax_mas": 3.0,
        "source": "Gaia DR3",
    }


@pytest.mark.network
@pytest.mark.parametrize("target_name", list(BENCHMARK_QUERIES.values()))
def test_each_benchmark_resolves_from_live_catalogs(target_name: str) -> None:
    from planetes.resolve import resolve

    result = resolve(target_name)
    assert 0.0 <= result.ra_deg < 360.0
    assert -90.0 <= result.dec_deg <= 90.0
    assert result.name
    # Catalogs legitimately omit astrometric measurements for some targets.
    result.to_contract()


@pytest.mark.network
def test_barnard_propagates_from_live_catalog_astrometry() -> None:
    from planetes.resolve import resolve

    target = resolve("Barnard's Star")
    assert target.ref_epoch_jyear is not None
    assert target.pm_ra_masyr is not None
    assert target.pm_dec_masyr is not None
    first = target.position_at(Time(target.ref_epoch_jyear, format="jyear").mjd)
    next_year = target.position_at(Time(target.ref_epoch_jyear + 1, format="jyear").mjd)
    assert 9.5 < first.separation(next_year).to_value(u.arcsec) < 11.5
