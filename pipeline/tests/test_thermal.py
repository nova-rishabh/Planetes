"""D4.2 thermometer model tests. These check the physics; V7 (real asteroids vs JPL distances) is separate."""

import math

import pytest

from planetes.contracts import SpectrumPoint
from planetes.thermal import (
    fit_distance,
    geometry,
    predict_ratio,
    subsolar_temperature_k,
    thermal_flux_ujy,
    thermal_opinion,
)


def test_subsolar_temperature_scale() -> None:
    t1 = subsolar_temperature_k(1.0, 0.1, 1.0)
    assert 370 < t1 < 410  # ~394 K for a dark rock at 1 AU
    assert subsolar_temperature_k(4.0, 0.1, 1.0) == pytest.approx(t1 / 2)


def test_quadrature_geometry() -> None:
    delta, alpha = geometry(2.0, 90.0)  # type: ignore[misc]
    assert delta == pytest.approx(math.sqrt(3))
    assert alpha == pytest.approx(30.0)
    assert geometry(0.9, 90.0) is None  # inside Earth's orbit, can't be seen at 90 deg


def test_flux_falls_with_observer_distance() -> None:
    near = thermal_flux_ujy(4.7, 1.0, 2.5, 1.5, 20.0, 0.1, 1.2)
    far = thermal_flux_ujy(4.7, 1.0, 2.5, 3.0, 20.0, 0.1, 1.2)
    assert near > 0 and far == pytest.approx(near / 4)


def test_ratio_rises_closer_to_sun() -> None:
    ratios = [predict_ratio(r, 0.1, 1.2, 90.0, 2.0, 4.7) for r in (1.5, 2.5, 4.0)]
    assert ratios[0] > ratios[1] > ratios[2]


def test_fit_recovers_model_distance() -> None:
    truth = predict_ratio(2.5, 0.15, 1.2, 90.0, 2.0, 4.7)
    lo, hi, _ = fit_distance(truth, 0.1 * truth, 90.0, 2.0, 4.7)  # type: ignore[misc]
    assert lo <= 2.5 <= hi


def _pt(det: int, flux: float, pair: str, wl: float) -> SpectrumPoint:
    return SpectrumPoint(
        obs_id=f"ivo://irsa.ipac/spherex_qr2?{pair}/D{det}",
        mjd=61000.0,
        detector=det,
        wavelength_um=wl,
        bandwidth_um=0.05,
        flux_ujy=flux,
        flux_err_ujy=flux * 0.02,
        snr=50.0,
        flags=0,
        saturated=False,
        used=True,
        reject_reason=None,
        pair_id=f"{pair}/D36",
        method="aperture",
        ra=30.0,
        dec=12.0,
    )


def test_opinion_needs_two_simultaneous_pairs() -> None:
    op, fit = thermal_opinion([_pt(3, 100.0, "2025W38_1A_0001_1", 2.0), _pt(6, 300.0, "2025W38_1A_0001_1", 4.7)])
    assert op.kind == "none" and fit is None and "1 usable" in op.method
