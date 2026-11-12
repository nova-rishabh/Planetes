"""D4.5 Planet X calculator physics (docs/04 §6). Reference values are physical anchors, not SPHEREx data."""

import math

import pytest

from planetes.planet_x import (
    ab_magnitude,
    evaluate,
    internal_heat_flux_ujy,
    reflected_flux_ujy,
    reflected_visual_magnitude,
    six_month_shift_arcsec,
    stacked_depth_ab,
)


def test_neptune_anchor() -> None:
    assert reflected_visual_magnitude(24622, 0.41, 29) == pytest.approx(7.8)
    # the blackbody-Sun reflected flux at 0.55 um gives the same V for Neptune
    assert ab_magnitude(reflected_flux_ujy(0.55, 24622, 0.41, 29)) == pytest.approx(7.8, abs=0.1)


def test_brightness_scaling_directions() -> None:
    base = reflected_visual_magnitude(10000, 0.3, 300)
    assert reflected_visual_magnitude(20000, 0.3, 300) == pytest.approx(base - 5 * math.log10(2))  # bigger: brighter
    assert reflected_visual_magnitude(10000, 0.6, 300) == pytest.approx(base - 2.5 * math.log10(2))
    assert reflected_visual_magnitude(10000, 0.3, 600) == pytest.approx(base + 10 * math.log10(2))  # 16x fainter


def test_planet_nine_like_scenario_in_published_range() -> None:
    # ~2.6 Earth radii, albedo 0.5, 550-1000 AU: published estimates put Planet Nine at V ~ 21-25 (docs/04 §6)
    for r in (550, 700, 1000):
        assert 21 <= reflected_visual_magnitude(16600, 0.5, r) <= 25


def test_internal_heat_and_stacking() -> None:
    assert internal_heat_flux_ujy(4.5, 20000, 500, 0) == 0
    assert internal_heat_flux_ujy(4.5, 40000, 500, 60) == pytest.approx(4 * internal_heat_flux_ujy(4.5, 20000, 500, 60))
    assert stacked_depth_ab(18.5, 100) == pytest.approx(21.0)
    assert six_month_shift_arcsec(500) == pytest.approx(825.06, rel=1e-4)


def test_evaluate_reports_every_band() -> None:
    s = evaluate(16600, 0.5, 700, internal_temperature_k=40)
    assert set(s.ab_mag_by_um) == {1.0, 2.0, 3.0, 3.5, 4.0, 4.5, 5.0}
    assert not any(s.brighter_than_depth_by_um.values())  # 700 AU: below a single SPHEREx visit
