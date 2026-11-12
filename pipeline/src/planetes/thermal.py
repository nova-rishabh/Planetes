"""D4.2 Asteroid thermometer: distance range from the D6/D3 colour of a moving object.

Close to the Sun an asteroid is warm, and its own heat glow adds to reflected sunlight in D6 (4.4-5.0 um) but not
much in D3 (1.6-2.4 um). So the D6/D3 flux ratio, from the same exposure (D3 and D6 see the same sky at the same
moment), rises steeply as the asteroid gets closer to the Sun. Comparing the measured ratio with a model over a
range of albedos and beaming parameters gives a range of possible distances from the Sun.

Model: NEATM (Harris 1998, Icarus 131, 291), integrated numerically over the visible disk, plus reflected sunlight
(Sun as a 5772 K blackbody, H-G phase law, flat albedo). sbpy 0.6.0's `thermal.NEATM` has no flux method yet, so the
integral is written here. Based on Amish's Role 4 draft (Nov 12); changed to use SPHEREx's real viewing geometry:
SPHEREx looks ~90 deg from the Sun, never at opposition, so each trial distance gets its own observer distance and
phase angle from the measured solar elongation, and the model is evaluated at the measured wavelengths.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import astropy.units as u
import numpy as np
from astropy.coordinates import SkyCoord, get_sun
from astropy.time import Time

from .contracts import Distance, SpectrumOpinion, SpectrumPoint

H_J_S = 6.62607015e-34
C_M_S = 299792458.0
K_B_J_K = 1.380649e-23
SIGMA_SB = 5.670374419e-8
AU_M = 149597870700.0
JY_SI = 1e-26
SOLAR_CONSTANT_W_M2 = 1361.0  # Kopp & Lean 2011
SUN_TEMPERATURE_K = 5772.0  # IAU 2015 nominal
SUN_RADIUS_M = 6.957e8  # IAU 2015 nominal
EMISSIVITY = 0.9
PHASE_SLOPE_G = 0.15
SYSTEMATIC_FRAC = 0.10  # floor on the ratio error: flat-albedo colour and model simplifications
MIN_PAIRS = 2

PV_GRID = np.linspace(0.03, 0.50, 6)  # geometric albedo prior
ETA_GRID = np.linspace(0.8, 2.5, 6)  # NEATM beaming parameter prior
R_GRID_AU = np.concatenate([np.arange(1.1, 6.0, 0.1), np.arange(6.0, 40.5, 0.5)])


@dataclass(frozen=True)
class ThermalFit:
    lo_au: float
    hi_au: float
    best_au: float
    observed_ratio: float
    ratio_err: float
    elongation_deg: float
    d3_um: float
    d6_um: float
    n_pairs: int
    quality: str


def _planck_nu(wavelength_um: float, temperature_k: np.ndarray | float) -> np.ndarray:
    """B_nu in W m^-2 Hz^-1 sr^-1."""
    nu = C_M_S / (wavelength_um * 1e-6)
    t = np.maximum(np.asarray(temperature_k, dtype=float), 1e-6)
    x = np.minimum(H_J_S * nu / (K_B_J_K * t), 700.0)
    return 2.0 * H_J_S * nu**3 / C_M_S**2 / np.expm1(x)


def subsolar_temperature_k(r_au: float, pv: float, eta: float) -> float:
    q = 0.290 + 0.684 * PHASE_SLOPE_G  # phase integral (Bowell et al. 1989)
    bond = min(0.95, q * pv)
    return float((SOLAR_CONSTANT_W_M2 * (1 - bond) / r_au**2 / (eta * EMISSIVITY * SIGMA_SB)) ** 0.25)


def _hg_phase(alpha_deg: float) -> float:
    t = math.tan(math.radians(min(max(alpha_deg, 0.0), 179.0)) / 2)
    if t == 0:
        return 1.0
    return (1 - PHASE_SLOPE_G) * math.exp(-3.33 * t**0.63) + PHASE_SLOPE_G * math.exp(-1.87 * t**1.22)


_LAT = np.linspace(-math.pi / 2, math.pi / 2, 25)
_LON = np.linspace(0, 2 * math.pi, 48, endpoint=False)
_LATG, _LONG = np.meshgrid(_LAT, _LON, indexing="ij")
_DAREA = np.cos(_LATG) * (math.pi / (len(_LAT) - 1)) * (2 * math.pi / len(_LON))  # per unit radius^2


def thermal_flux_ujy(
    wavelength_um: float, diameter_km: float, r_au: float, delta_au: float, alpha_deg: float, pv: float, eta: float
) -> float:
    """NEATM thermal F_nu: T = T_ss cos(i)^(1/4) on the day side, 0 at night; visible hemisphere only."""
    a = math.radians(alpha_deg)
    mu_obs = np.clip(np.sin(_LATG), 0, None)  # observer along +z
    mu_sun = np.clip(np.cos(_LATG) * np.cos(_LONG) * math.sin(a) + np.sin(_LATG) * math.cos(a), 0, None)
    temp = subsolar_temperature_k(r_au, pv, eta) * mu_sun**0.25
    radius_m = diameter_km * 500.0
    flux = EMISSIVITY * float(np.sum(_planck_nu(wavelength_um, temp) * (mu_sun > 0) * mu_obs * _DAREA))
    return flux * (radius_m / (delta_au * AU_M)) ** 2 / JY_SI * 1e6


def reflected_flux_ujy(
    wavelength_um: float, diameter_km: float, r_au: float, delta_au: float, alpha_deg: float, pv: float
) -> float:
    sun_1au = math.pi * float(_planck_nu(wavelength_um, SUN_TEMPERATURE_K)) * (SUN_RADIUS_M / AU_M) ** 2
    radius_m = diameter_km * 500.0
    f = sun_1au / r_au**2 * pv * _hg_phase(alpha_deg) * (radius_m / (delta_au * AU_M)) ** 2
    return f / JY_SI * 1e6


def geometry(r_au: float, elongation_deg: float) -> tuple[float, float] | None:
    """Observer distance and phase angle for an object r AU from the Sun seen at this solar elongation (Earth 1 AU)."""
    e = math.radians(elongation_deg)
    disc = r_au**2 - math.sin(e) ** 2
    if disc <= 0:
        return None
    delta = math.cos(e) + math.sqrt(disc)
    if delta <= 0:
        return None
    cos_alpha = (r_au**2 + delta**2 - 1.0) / (2 * r_au * delta)
    return delta, math.degrees(math.acos(max(-1.0, min(1.0, cos_alpha))))


def predict_ratio(r_au: float, pv: float, eta: float, elongation_deg: float, d3_um: float, d6_um: float) -> float:
    """Model D6/D3 F_nu ratio (reflected + thermal). Size cancels."""
    g = geometry(r_au, elongation_deg)
    if g is None:
        return float("nan")
    delta, alpha = g
    f3 = reflected_flux_ujy(d3_um, 1.0, r_au, delta, alpha, pv) + thermal_flux_ujy(
        d3_um, 1.0, r_au, delta, alpha, pv, eta
    )
    f6 = reflected_flux_ujy(d6_um, 1.0, r_au, delta, alpha, pv) + thermal_flux_ujy(
        d6_um, 1.0, r_au, delta, alpha, pv, eta
    )
    return f6 / f3 if f3 > 0 else float("nan")


def fit_distance(
    ratio: float, ratio_err: float, elongation_deg: float, d3_um: float, d6_um: float
) -> tuple[float, float, float] | None:
    """(lo, hi, best) heliocentric distance in AU where some albedo/beaming in the prior matches within 2 sigma."""
    best = (math.inf, math.nan)
    ok: list[float] = []
    for r in R_GRID_AU:
        chi = min(
            (
                abs(predict_ratio(float(r), float(pv), float(eta), elongation_deg, d3_um, d6_um) - ratio) / ratio_err
                for pv in PV_GRID
                for eta in ETA_GRID
            ),
            default=math.inf,
        )
        if not math.isfinite(chi):
            continue
        if chi < best[0]:
            best = (chi, float(r))
        if chi <= 2.0:
            ok.append(float(r))
    if not ok:
        return None
    return min(ok), max(ok), best[1]


def solar_elongation_deg(ra_deg: float, dec_deg: float, mjd: float) -> float:
    t = Time(mjd, format="mjd")
    sun = get_sun(t)
    return float(SkyCoord(ra_deg * u.deg, dec_deg * u.deg, frame="gcrs", obstime=t).separation(sun).deg)


def _pairs(points: list[SpectrumPoint]) -> list[tuple[SpectrumPoint, SpectrumPoint]]:
    by: dict[str, dict[int, SpectrumPoint]] = {}
    for p in points:
        if p.used and p.pair_id and p.detector in (3, 6) and p.flux_ujy and p.flux_err_ujy and p.wavelength_um:
            by.setdefault(p.pair_id, {})[p.detector] = p
    return [(d[3], d[6]) for d in by.values() if 3 in d and 6 in d and d[3].flux_ujy > 0]  # type: ignore[operator]


NO_OPINION_METHOD = "Thermometer (NEATM, D6/D3 from the same exposure)"


def thermal_opinion(points: list[SpectrumPoint]) -> tuple[SpectrumOpinion, ThermalFit | None]:
    """Spectrum opinion for a moving object from its simultaneous D3/D6 pairs; 'none' when it can't measure."""
    pairs = _pairs(points)

    def none(why: str) -> tuple[SpectrumOpinion, None]:
        return (
            SpectrumOpinion(
                kind="none",
                **{"class": None},
                temperature_k=None,
                distance=Distance(lo=None, hi=None, unit=None),
                quality="poor",
                method=f"{NO_OPINION_METHOD}: {why}",
            ),
            None,
        )

    if len(pairs) < MIN_PAIRS:
        return none(f"{len(pairs)} usable D3/D6 pairs, need {MIN_PAIRS}")
    ratios = np.array([p6.flux_ujy / p3.flux_ujy for p3, p6 in pairs])  # type: ignore[operator]
    rel = np.array(
        [
            math.hypot(p3.flux_err_ujy / p3.flux_ujy, p6.flux_err_ujy / p6.flux_ujy)  # type: ignore[operator]
            for p3, p6 in pairs
        ]
    )
    ratio = float(np.median(ratios))
    err = ratio * max(SYSTEMATIC_FRAC, float(np.median(rel)) / math.sqrt(len(pairs)))
    d3_um = float(np.median([p3.wavelength_um for p3, _ in pairs]))
    d6_um = float(np.median([p6.wavelength_um for _, p6 in pairs]))
    elong = float(np.median([solar_elongation_deg(p3.ra, p3.dec, p3.mjd) for p3, _ in pairs]))
    fit = fit_distance(ratio, err, elong, d3_um, d6_um)
    if fit is None:
        return none(f"measured D6/D3 = {ratio:.3g} matches no distance in the model range")
    lo, hi, best = fit
    width = (hi - lo) / best
    quality = "good" if width <= 0.5 else "fair" if width <= 1.0 else "poor"
    result = ThermalFit(lo, hi, best, ratio, err, elong, d3_um, d6_um, len(pairs), quality)
    opinion = SpectrumOpinion(
        kind="thermal",
        **{"class": None},
        temperature_k=None,
        distance=Distance(lo=round(lo, 2), hi=round(hi, 2), unit="au"),
        quality=quality,
        method=(
            f"{NO_OPINION_METHOD}: D6/D3 = {ratio:.3g} ± {err:.2g} from {len(pairs)} pairs at "
            f"{d3_um:.2f}/{d6_um:.2f} µm, solar elongation {elong:.0f}°; albedo 0.03–0.5, beaming 0.8–2.5"
        ),
    )
    return opinion, result
