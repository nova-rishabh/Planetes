"""D3.2 overlays tests: catalog propagation, WCS projection, and contract conformity."""

from __future__ import annotations

import math
import os

import astropy.units as u
import pytest
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.time import Time

import planetes.overlays as po
from planetes.contracts import Overlays

BARNARD_FITS_D3 = r"C:\Users\Lenovo\.gemini\antigravity\scratch\barnard\f_10f7ed42a99d.fits"
BARNARD_FITS_D6 = r"C:\Users\Lenovo\.gemini\antigravity\scratch\barnard\f_0b0c5ab5d4dd.fits"


def test_propagate_position_without_pm_returns_identical_coords() -> None:
    ra, dec = 269.45, 4.75
    moved_ra, moved_dec = po.propagate_position(
        ra_deg=ra,
        dec_deg=dec,
        pm_ra_masyr=None,
        pm_dec_masyr=None,
        parallax_mas=None,
        ref_epoch_jyear=2016.0,
        target_mjd=61000.0,
    )
    assert moved_ra == ra
    assert moved_dec == dec


def test_propagate_position_matches_astropy_space_motion() -> None:
    # Synthetic test fixture with known high proper motion
    ra0, dec0 = 269.4485, 4.7394
    pmra, pmdec = -801.55, 10362.4
    plx = 546.98
    ref_epoch = 2016.0
    target_mjd = Time(2026.0, format="jyear").mjd

    moved_ra, moved_dec = po.propagate_position(
        ra_deg=ra0,
        dec_deg=dec0,
        pm_ra_masyr=pmra,
        pm_dec_masyr=pmdec,
        parallax_mas=plx,
        ref_epoch_jyear=ref_epoch,
        target_mjd=target_mjd,
    )

    expected = SkyCoord(
        ra=ra0 * u.deg,
        dec=dec0 * u.deg,
        pm_ra_cosdec=pmra * u.mas / u.yr,
        pm_dec=pmdec * u.mas / u.yr,
        distance=(1000.0 / plx) * u.pc,
        obstime=Time(ref_epoch, format="jyear"),
        frame="icrs",
    ).apply_space_motion(new_obstime=Time(target_mjd, format="mjd"))

    assert math.isclose(moved_ra, float(expected.ra.deg), abs_tol=1e-5)
    assert math.isclose(moved_dec, float(expected.dec.deg), abs_tol=1e-5)

    # 10 years of motion: ~104 arcsec separation
    sep = SkyCoord(ra=ra0 * u.deg, dec=dec0 * u.deg).separation(expected).to_value(u.arcsec)
    assert 100.0 < sep < 110.0


def test_build_overlays_matches_contract_schema() -> None:
    gaia_records = [
        {
            "id": "1234567890",
            "ra": 269.45,
            "dec": 4.75,
            "pm_ra_masyr": -800.0,
            "pm_dec_masyr": 10000.0,
            "parallax_mas": 500.0,
            "mag": 8.5,
            "band": "G",
            "ref_epoch": 2016.0,
        }
    ]
    wise_records = [
        {
            "id": "J175747.94+044323.8",
            "ra": 269.449,
            "dec": 4.723,
            "pm_ra_masyr": None,
            "pm_dec_masyr": None,
            "parallax_mas": None,
            "mag": 4.4,
            "band": "W1",
            "ref_epoch": 2010.5,
        }
    ]
    mjds = [60905.85, 61269.04]
    overlays = po.build_overlays(gaia_records, wise_records, mjds)

    assert isinstance(overlays, Overlays)
    assert overlays.schema_version == "1.0"
    assert len(overlays.catalogs) == 2
    assert overlays.catalogs[0].name == "Gaia DR3"
    assert overlays.catalogs[1].name == "AllWISE"

    g_src = overlays.catalogs[0].sources[0]
    assert g_src.id == "1234567890"
    assert "60905.85" in g_src.at_mjd
    assert "61269.04" in g_src.at_mjd
    assert len(g_src.at_mjd["60905.85"].root) == 2


def test_project_sources_to_wcs_on_real_spherex_cutout() -> None:
    if not os.path.exists(BARNARD_FITS_D3):
        pytest.skip("Barnard FITS file not available")

    with fits.open(BARNARD_FITS_D3) as hdul:
        hdr = hdul["IMAGE"].header
        mjd = 60905.854749

        # Gaia position for Barnard's Star
        gaia_records = [
            {
                "id": "4472832130942575872",
                "ra": 269.44850252544,
                "dec": 4.73942005111,
                "pm_ra_masyr": -801.551,
                "pm_dec_masyr": 10362.394,
                "parallax_mas": 546.9759,
                "mag": 8.19,
                "band": "G",
                "ref_epoch": 2016.0,
            }
        ]
        cat = po.build_overlay_catalog("Gaia DR3", po.GAIA_VIZIER_ID, 2016.0, gaia_records, [mjd])
        proj = po.project_sources_to_wcs(cat, hdr, mjd, (hdul["IMAGE"].data.shape))

        assert len(proj) == 1
        p = proj[0]
        assert p.inside is True
        # Barnard is near pixel (28.78, 30.29), peak is at (28, 30)
        assert 27.5 < p.pixel_x < 30.0
        assert 29.0 < p.pixel_y < 31.5


def test_project_sources_to_wcs_on_mirrored_d6_cutout() -> None:
    if not os.path.exists(BARNARD_FITS_D6):
        pytest.skip("Barnard FITS D6 file not available")

    with fits.open(BARNARD_FITS_D6) as hdul:
        hdr = hdul["IMAGE"].header
        mjd = 60902.864715

        gaia_records = [
            {
                "id": "4472832130942575872",
                "ra": 269.44850252544,
                "dec": 4.73942005111,
                "pm_ra_masyr": -801.551,
                "pm_dec_masyr": 10362.394,
                "parallax_mas": 546.9759,
                "mag": 8.19,
                "band": "G",
                "ref_epoch": 2016.0,
            }
        ]
        cat = po.build_overlay_catalog("Gaia DR3", po.GAIA_VIZIER_ID, 2016.0, gaia_records, [mjd])
        proj = po.project_sources_to_wcs(cat, hdr, mjd, (hdul["IMAGE"].data.shape))

        assert len(proj) == 1
        p = proj[0]
        assert p.inside is True
        # Barnard on D6 is near pixel (28.55, 29.54), peak is at (28, 30)
        assert 27.0 < p.pixel_x < 30.0
        assert 28.5 < p.pixel_y < 31.0


def test_aladin_catalog_config_options() -> None:
    cfg_gaia = po.aladin_catalog_config("Gaia DR3")
    assert cfg_gaia["name"] == "Gaia DR3"
    assert cfg_gaia["shape"] == "circle"

    cfg_wise = po.aladin_catalog_config("AllWISE")
    assert cfg_wise["name"] == "AllWISE"
    assert cfg_wise["shape"] == "square"


@pytest.mark.network
def test_live_gaia_and_allwise_queries() -> None:
    gaia = po.query_gaia_sources(269.45, 4.75, 0.05, mag_limit=15.0, max_sources=10)
    assert len(gaia) > 0
    assert "id" in gaia[0]
    assert "ra" in gaia[0]
    assert "dec" in gaia[0]

    wise = po.query_allwise_sources(269.45, 4.75, 0.05, mag_limit=14.0, max_sources=10)
    assert len(wise) > 0
    assert "id" in wise[0]
