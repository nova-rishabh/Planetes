"""Automated unit & fixture tests for SPHEREx forced ePSF & aperture photometry (Deliverable D2.4)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from astropy.io import fits
from astropy.wcs import WCS

from planetes import photometry

FIXTURE_FITS = Path(__file__).parent / "data" / "barnard_d3_qr2_2025W33_2C_0321_1.fits"


def _synthetic_spherex_hdul(
    true_flux_mjy_sr: float = 10.0,
    bkg_mjy_sr: float = 1.5,
    x_star: float = 11.3,
    y_star: float = 10.7,
    saturate_center: bool = False,
) -> fits.HDUList:
    """Build an in-memory synthetic SPHEREx L2b cutout with known flux, ZODI, VARIANCE, FLAGS, and EPSF."""
    ny, nx = 23, 23
    yy, xx = np.indices((ny, nx), dtype=np.float64)

    # Create a 33x33 5x-oversampled Gaussian EPSF stamp
    ov = 5
    ey, ex = np.indices((33, 33), dtype=np.float64)
    sigma_ov = 1.1 * ov
    epsf_stamp = np.exp(-0.5 * ((ex - 16.0) ** 2 + (ey - 16.0) ** 2) / (sigma_ov**2))
    epsf_stamp /= np.sum(epsf_stamp)

    # Render star using exact pixel-integrated Gaussian at (x_star, y_star)
    sigma_pix = 1.1
    psf_pix = np.exp(-0.5 * ((xx - x_star) ** 2 + (yy - y_star) ** 2) / (sigma_pix**2))
    psf_pix /= np.sum(psf_pix)

    zodi = np.full((ny, nx), 0.8, dtype=np.float32)
    image = (zodi + bkg_mjy_sr + true_flux_mjy_sr * psf_pix).astype(np.float32)
    variance = np.full((ny, nx), 0.0025, dtype=np.float32)

    flag_hdr = fits.Header()
    flag_hdr["MSKN0001"] = "OVERFLOW"
    flag_hdr["MSKM0001"] = 4
    flags = np.zeros((ny, nx), dtype=np.int32)
    if saturate_center:
        flags[int(round(y_star)), int(round(x_star))] = 4

    w = WCS(naxis=2)
    w.wcs.crpix = [12.0, 12.0]
    w.wcs.cdelt = [-6.15 / 3600.0, 6.15 / 3600.0]
    w.wcs.crval = [180.0, 0.0]
    w.wcs.ctype = ["RA---TAN", "DEC--TAN"]
    hdr = w.to_header()
    hdr["DETECTOR"] = 2
    hdr["MJD-OBS"] = 61000.0
    hdr["OBS_ID"] = "syn_test_001"
    hdr["WAVELEN"] = 1.25
    hdr["BANDWID"] = 0.03

    col_x = fits.Column(name="XCENTER", format="E", array=np.array([1024.0], dtype=np.float32))
    col_y = fits.Column(name="YCENTER", format="E", array=np.array([1024.0], dtype=np.float32))
    col_n = fits.Column(name="NSTAR", format="J", array=np.array([25], dtype=np.int32))
    col_e = fits.Column(name="EPSF", format="1089E", dim="(33,33)", array=epsf_stamp[None, :, :].astype(np.float32))
    epsf_hdu = fits.BinTableHDU.from_columns([col_x, col_y, col_n, col_e], name="EPSF")
    epsf_hdu.header["OVSMPX"] = ov
    epsf_hdu.header["OVSMPY"] = ov

    return fits.HDUList(
        [
            fits.PrimaryHDU(),
            fits.ImageHDU(data=image, header=hdr, name="IMAGE"),
            fits.ImageHDU(data=zodi, name="ZODI"),
            fits.ImageHDU(data=variance, name="VARIANCE"),
            fits.ImageHDU(data=flags, header=flag_hdr, name="FLAGS"),
            epsf_hdu,
        ]
    )


def test_proper_motion_propagation_barnard() -> None:
    """Barnard's Star (~10.36 arcsec/yr north) should move ~270 arcsec (~0.075 deg) between J2000 and 2026."""
    ra_2000, dec_2000 = 269.45207, 4.69339
    pm = {"pm_ra_masyr": -801.55, "pm_dec_masyr": 10362.39, "ref_epoch_jyear": 2000.0}
    ra_2026, dec_2026 = photometry.propagate_position(ra_2000, dec_2000, mjd=61100.0, pm=pm)
    delta_dec_arcsec = (dec_2026 - dec_2000) * 3600.0
    assert 265.0 < delta_dec_arcsec < 275.0


def test_synthetic_epsf_flux_recovery_and_unit_conversion() -> None:
    """Forced ePSF photometry must recover injected flux within 5% and convert MJy/sr -> uJy accurately."""
    hdul = _synthetic_spherex_hdul(true_flux_mjy_sr=12.0, x_star=11.3, y_star=10.7)
    w = WCS(hdul["IMAGE"].header)
    ra_star, dec_star = w.pixel_to_world_values(11.3, 10.7)

    pt = photometry.measure_hdul_flux(hdul, ra=float(ra_star), dec=float(dec_star), method="psf")
    omega = photometry.get_pixel_solid_angle_sr(w)
    expected_ujy = 12.0 * omega * 1e12

    assert pt.used is True
    assert pt.method == "psf"
    assert pt.pair_id == "D2&D5"
    assert pt.flux_ujy is not None
    assert abs(pt.flux_ujy - expected_ujy) / expected_ujy < 0.05
    assert pt.snr is not None and pt.snr > 20.0


def test_saturated_core_rejected_cleanly() -> None:
    """Saturated target core must be marked used=False with reject_reason='saturated'."""
    hdul = _synthetic_spherex_hdul(saturate_center=True)
    w = WCS(hdul["IMAGE"].header)
    ra_star, dec_star = w.pixel_to_world_values(11.3, 10.7)

    pt = photometry.measure_hdul_flux(hdul, ra=float(ra_star), dec=float(dec_star), method="auto")
    assert pt.used is False
    assert pt.saturated is True
    assert pt.reject_reason == "saturated"


def test_out_of_bounds_target_handled_without_nan_crash() -> None:
    """Coordinates far outside the cutout WCS must return used=False ('target_out_of_bounds') without crashing."""
    hdul = _synthetic_spherex_hdul()
    pt = photometry.measure_hdul_flux(hdul, ra=10.0, dec=-75.0, method="auto")
    assert pt.used is False
    assert pt.reject_reason == "target_out_of_bounds"
    assert pt.flux_ujy is None


@pytest.mark.skipif(not FIXTURE_FITS.exists(), reason="Offline Barnard FITS fixture missing")
def test_real_barnard_fixture_photometry() -> None:
    """Measure forced photometry on the committed Barnard's Star D3 FITS fixture."""
    pm = {"pm_ra_masyr": -801.55, "pm_dec_masyr": 10362.39, "ref_epoch_jyear": 2000.0}
    res = photometry.extract_spectrum([FIXTURE_FITS], ra=269.45207, dec=4.69339, pm=pm)
    assert res.summary.n_points == 1
    pt = res.points[0]
    assert pt.detector == 3
    assert pt.pair_id == "D3&D6"
    assert pt.wavelength_um is not None and 1.6 < pt.wavelength_um < 2.5