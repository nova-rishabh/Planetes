"""D2.4 aperture photometry helpers, D4.1 spectrum rules and D4.3 typer. Offline: no network, no fake app data."""

from __future__ import annotations

import math

import numpy as np
from astropy.wcs import WCS

from planetes.contracts import SpectrumPoint
from planetes.photometry import PointFlux, _enclosed_fraction, pixel_solid_angle_sr
from planetes.spectrum import REASONS, pair_id, reject_reason, release_of, summarise
from planetes.typing import absolute_j_mag, fit_type, load_standards, spt_number

OBS = "ivo://irsa.ipac/spherex_qr2?2025W33_2C_0321_1/D6"


def _point(**kw) -> SpectrumPoint:
    base = dict(
        obs_id=OBS,
        mjd=60902.86,
        detector=3,
        wavelength_um=1.5,
        bandwidth_um=0.03,
        flux_ujy=100.0,
        flux_err_ujy=5.0,
        snr=20.0,
        flags=0,
        saturated=False,
        used=True,
        reject_reason=None,
        pair_id=None,
        method="aperture",
        ra=331.0,
        dec=-56.8,
    )
    base.update(kw)
    return SpectrumPoint(**base)


def test_pair_id_links_simultaneous_detectors() -> None:
    assert pair_id(OBS, 6) == "2025W33_2C_0321_1/D36"
    assert pair_id(OBS.replace("/D6", "/D3"), 3) == pair_id(OBS, 6)
    assert pair_id("no-exposure-id", 1) is None


def test_reject_reasons_in_order() -> None:
    assert reject_reason(PointFlux(None, None, 0, problem="outside")) == REASONS["outside"]
    assert reject_reason(PointFlux(10.0, 1.0, 1, ["OVERFLOW"], saturated=True)) == REASONS["saturated"]
    assert "TRANSIENT" in (reject_reason(PointFlux(10.0, 1.0, 2, ["SOURCE", "TRANSIENT"])) or "")
    assert reject_reason(PointFlux(2.0, 1.0, 0)) == REASONS["faint"]
    assert reject_reason(PointFlux(30.0, 1.0, 4, ["SOURCE"])) is None  # SOURCE is information, not a defect


def test_summary_and_release() -> None:
    pts = [_point(), _point(detector=6, used=False, reject_reason="x"), _point(obs_id=OBS.replace("qr2", "qr3"))]
    s = summarise(pts)
    assert (s.n_points, s.n_used, s.n_rejected) == (3, 2, 1)
    assert [int(d.root) if hasattr(d, "root") else int(d) for d in s.bands_covered] == [3]
    assert release_of(pts) in ("QR2", "QR3")


def test_enclosed_fraction_and_solid_angle() -> None:
    psf = np.zeros((101, 101))
    psf[50, 50] = 1.0
    assert _enclosed_fraction(psf, 10, 3.0) == 1.0
    w = WCS(naxis=2)
    w.wcs.ctype = ["RA---TAN", "DEC--TAN"]
    w.wcs.cdelt = [-6.15 / 3600, 6.15 / 3600]
    w.wcs.crval = [331.0, -56.8]
    w.wcs.crpix = [30, 30]
    expected = (math.radians(6.15 / 3600)) ** 2
    assert abs(pixel_solid_angle_sr(w, 29, 29) / expected - 1) < 1e-3


def test_typer_recovers_a_standard_from_its_own_spectrum() -> None:
    # Points sampled from the real T6 standard at SPHEREx-like wavelengths: the fit must pick T6 (or a neighbour).
    w, f = load_standards()["T6"]
    lam = np.linspace(0.8, 2.4, 60)
    flux = np.interp(lam, w, f) * 5000.0
    pts = [
        _point(wavelength_um=float(x), bandwidth_um=0.0, flux_ujy=float(y), flux_err_ujy=50.0)
        for x, y in zip(lam, flux, strict=True)
    ]
    fit = fit_type(pts)
    assert fit is not None and abs(spt_number(fit.spt) - spt_number("T6")) <= 1


def test_absolute_magnitude_relation_range() -> None:
    assert absolute_j_mag(spt_number("M0")) is None  # outside Dupuy & Liu 2012 (M6-T9)
    mj_t1, mj_t8 = absolute_j_mag(spt_number("T1")), absolute_j_mag(spt_number("T8"))
    assert mj_t1 is not None and mj_t8 is not None and 13 < mj_t1 < mj_t8 < 18
