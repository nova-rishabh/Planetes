"""D4.5 Planet X Reality Check: physics for the calculator (docs/04 §6).

Pure functions, no data access. Every output is a scenario for chosen inputs (size, albedo, distance,
internal temperature), never a prediction that SPHEREx sees a planet. Based on Amish's Role 4 draft (Nov 12),
with the brightness scaling corrected (see reflected_visual_magnitude).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

H_J_S = 6.62607015e-34
C_M_S = 299792458.0
K_B_J_K = 1.380649e-23
JY_SI = 1e-26  # W m^-2 Hz^-1
AU_M = 149597870700.0
AB_ZERO_JY = 3631.0
SUN_TEMPERATURE_K = 5772.0  # IAU 2015 nominal
SUN_RADIUS_M = 6.957e8  # IAU 2015 nominal
NEPTUNE_RADIUS_KM = 24622.0  # mean radius (NASA planetary fact sheet)
NEPTUNE_GEOMETRIC_ALBEDO = 0.41  # Fortney et al. 2016, as in docs/04 §6
NEPTUNE_V_AT_29_AU = 7.8  # docs/04 §6 reference point
ARCSEC_PER_RAD = 206264.806
SPHEREX_SINGLE_VISIT_AB = (18.5, 19.0)  # docs/04 §6, short wavelengths
DEFAULT_BANDS_UM = (1.0, 2.0, 3.0, 3.5, 4.0, 4.5, 5.0)


def reflected_visual_magnitude(
    radius_km: float,
    geometric_albedo: float,
    heliocentric_distance_au: float,
    geocentric_distance_au: float | None = None,
) -> float:
    """V magnitude scaled from Neptune (V 7.8 at 29 AU).

    Reflected flux goes as R^2 p / (r^2 Delta^2), so
    V = 7.8 - 5 log10(R/R_N) - 2.5 log10(p/p_N) + 5 log10(r Delta / 29^2).
    (Doubling the distance makes it 16x fainter: +3.0 mag.)
    """
    delta = heliocentric_distance_au if geocentric_distance_au is None else geocentric_distance_au
    if radius_km <= 0 or not 0 < geometric_albedo <= 1 or heliocentric_distance_au <= 0 or delta <= 0:
        raise ValueError("radius and distances must be positive; albedo in (0, 1]")
    return (
        NEPTUNE_V_AT_29_AU
        - 5.0 * math.log10(radius_km / NEPTUNE_RADIUS_KM)
        - 2.5 * math.log10(geometric_albedo / NEPTUNE_GEOMETRIC_ALBEDO)
        + 5.0 * math.log10(heliocentric_distance_au * delta / 29.0**2)
    )


def _planck_nu(wavelength_um: float, temperature_k: float) -> float:
    """Planck B_nu in W m^-2 Hz^-1 sr^-1."""
    lam = wavelength_um * 1e-6
    nu = C_M_S / lam
    x = H_J_S * nu / (K_B_J_K * temperature_k)
    if x > 700:
        return 0.0
    return 2.0 * H_J_S * nu**3 / C_M_S**2 / math.expm1(x)


def reflected_flux_ujy(
    wavelength_um: float,
    radius_km: float,
    geometric_albedo: float,
    heliocentric_distance_au: float,
    geocentric_distance_au: float | None = None,
) -> float:
    """Reflected sunlight at full phase, flat albedo, Sun as a 5772 K blackbody. In microjansky."""
    delta = heliocentric_distance_au if geocentric_distance_au is None else geocentric_distance_au
    sun_at_1au = math.pi * _planck_nu(wavelength_um, SUN_TEMPERATURE_K) * (SUN_RADIUS_M / AU_M) ** 2
    planet = sun_at_1au / heliocentric_distance_au**2 * geometric_albedo * (radius_km * 1e3 / (delta * AU_M)) ** 2
    return planet / JY_SI * 1e6


def internal_heat_flux_ujy(
    wavelength_um: float, radius_km: float, geocentric_distance_au: float, internal_temperature_k: float
) -> float:
    """Glow from internal heat, as a blackbody of the given temperature (model-dependent). In microjansky."""
    if internal_temperature_k <= 0:
        return 0.0
    solid = math.pi * (radius_km * 1e3 / (geocentric_distance_au * AU_M)) ** 2
    return _planck_nu(wavelength_um, internal_temperature_k) * solid / JY_SI * 1e6


def ab_magnitude(flux_ujy: float) -> float:
    return math.inf if flux_ujy <= 0 else -2.5 * math.log10(flux_ujy * 1e-6 / AB_ZERO_JY)


def stacked_depth_ab(single_visit_depth_ab: float, n_visits: int) -> float:
    """Depth after stacking N equal visits: noise falls as sqrt(N), i.e. +1.25 log10 N magnitudes."""
    if n_visits < 1:
        raise ValueError("n_visits must be >= 1")
    return single_visit_depth_ab + 1.25 * math.log10(n_visits)


def six_month_shift_arcsec(heliocentric_distance_au: float) -> float:
    """Apparent jump between epochs six months apart (Earth on opposite sides of the Sun): ~2 x 206265 / r."""
    return 2.0 * ARCSEC_PER_RAD / heliocentric_distance_au


@dataclass(frozen=True)
class Scenario:
    v_mag: float
    ab_mag_by_um: dict[float, float]
    internal_share_by_um: dict[float, float]
    depth_ab: float
    brighter_than_depth_by_um: dict[float, bool]
    six_month_shift_arcsec: float


def evaluate(
    radius_km: float,
    geometric_albedo: float,
    distance_au: float,
    internal_temperature_k: float = 0.0,
    n_visits: int = 1,
    single_visit_depth_ab: float = SPHEREX_SINGLE_VISIT_AB[0],
    bands_um: tuple[float, ...] = DEFAULT_BANDS_UM,
) -> Scenario:
    """One what-if: how bright such a planet would be in SPHEREx bands vs SPHEREx's depth, and how far it jumps."""
    depth = stacked_depth_ab(single_visit_depth_ab, n_visits)
    mags: dict[float, float] = {}
    share: dict[float, float] = {}
    for lam in bands_um:
        refl = reflected_flux_ujy(lam, radius_km, geometric_albedo, distance_au)
        heat = internal_heat_flux_ujy(lam, radius_km, distance_au, internal_temperature_k)
        mags[lam] = ab_magnitude(refl + heat)
        share[lam] = heat / (refl + heat) if refl + heat > 0 else 0.0
    return Scenario(
        v_mag=reflected_visual_magnitude(radius_km, geometric_albedo, distance_au),
        ab_mag_by_um=mags,
        internal_share_by_um=share,
        depth_ab=depth,
        brighter_than_depth_by_um={lam: m <= depth for lam, m in mags.items()},
        six_month_shift_arcsec=six_month_shift_arcsec(distance_au),
    )
