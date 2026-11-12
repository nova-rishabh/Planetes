"""D3.3 & D3.4: Motion fitting for stars and solar system objects.

Provides linear proper motion fitting across SPHEREx and catalog epochs (stars),
apparent sky motion rate fitting (asteroids), rate-to-distance range inversion
under trial Keplerian circular orbits (docs/04 §3), and contract-valid MotionOpinion
generation for the Two Opinions engine.
"""

from __future__ import annotations

import logging
import math
from collections.abc import Sequence
from dataclasses import dataclass

import astropy.units as u
import numpy as np
from astropy.coordinates import SkyCoord, get_body_barycentric, solar_system_ephemeris
from astropy.time import Time

from planetes.contracts import Distance, MotionOpinion, MotionTruth

log = logging.getLogger("planetes.motion")

# Julian day offset for J2000
MJD_J2000 = 51544.5
DAYS_PER_YEAR = 365.25
HOURS_PER_DAY = 24.0
ARCSEC_PER_RAD = 206264.80624709636


@dataclass(frozen=True, slots=True)
class ProperMotionFit:
    """Linear proper motion fit across epochs."""

    mu_ra_cosdec_masyr: float
    mu_dec_masyr: float
    mu_masyr: float
    mu_arcsec_yr: float
    mu_err_arcsec_yr: float
    pa_deg: float
    chi2: float
    reduced_chi2: float
    n_epochs: int
    time_baseline_yr: float


@dataclass(frozen=True, slots=True)
class SSORateFit:
    """Solar System Object apparent sky rate fit."""

    rate_arcsec_hr: float
    rate_err_arcsec_hr: float
    pa_deg: float
    n_epochs: int
    time_baseline_hr: float


def mjd_to_jyear(mjd: float) -> float:
    """Convert Modified Julian Date to Julian Year."""
    return 2000.0 + (float(mjd) - MJD_J2000) / DAYS_PER_YEAR


def fit_proper_motion(
    epochs_mjd: Sequence[float],
    ra_deg: Sequence[float],
    dec_deg: Sequence[float],
    ra_err_mas: Sequence[float] | None = None,
    dec_err_mas: Sequence[float] | None = None,
) -> ProperMotionFit:
    """Fit linear proper motion (mas/yr and arcsec/yr) from epoch positions.

    Applies cos(dec) scaling to RA differences so that mu_ra_cosdec matches
    Gaia conventions (μα* = μα cos δ).
    """
    n = len(epochs_mjd)
    if n < 2:
        raise ValueError("Proper motion fit requires at least 2 epochs")
    if len(ra_deg) != n or len(dec_deg) != n:
        raise ValueError("epochs_mjd, ra_deg, and dec_deg must have identical length")

    t_arr = np.array([mjd_to_jyear(m) for m in epochs_mjd], dtype=np.float64)
    ra_arr = np.array(ra_deg, dtype=np.float64)
    dec_arr = np.array(dec_deg, dtype=np.float64)

    t_ref = np.mean(t_arr)
    dt = t_arr - t_ref
    baseline_yr = float(np.max(t_arr) - np.min(t_arr))

    mean_dec_rad = np.radians(np.mean(dec_arr))
    cos_dec = np.cos(mean_dec_rad)

    # Convert positional offsets from reference to milliarcseconds
    ra_ref = ra_arr[0]
    dec_ref = dec_arr[0]

    dx_mas = (ra_arr - ra_ref) * cos_dec * 3600.0 * 1000.0
    dy_mas = (dec_arr - dec_ref) * 3600.0 * 1000.0

    # Weights
    wx = 1.0 / (np.array(ra_err_mas, dtype=np.float64) ** 2) if ra_err_mas is not None else None
    wy = 1.0 / (np.array(dec_err_mas, dtype=np.float64) ** 2) if dec_err_mas is not None else None

    # Fit RA (X)
    p_x, cov_x = np.polyfit(dt, dx_mas, 1, w=np.sqrt(wx) if wx is not None else None, cov=True)
    mu_x = float(p_x[0])
    err_x = float(np.sqrt(cov_x[0, 0]))

    # Fit Dec (Y)
    p_y, cov_y = np.polyfit(dt, dy_mas, 1, w=np.sqrt(wy) if wy is not None else None, cov=True)
    mu_y = float(p_y[0])
    err_y = float(np.sqrt(cov_y[0, 0]))

    mu_total_mas = float(np.hypot(mu_x, mu_y))
    mu_total_arcsec = mu_total_mas / 1000.0

    if mu_total_mas > 0:
        err_total_arcsec = float(np.sqrt((mu_x * err_x) ** 2 + (mu_y * err_y) ** 2) / mu_total_mas / 1000.0)
    else:
        err_total_arcsec = float(max(err_x, err_y) / 1000.0)

    # Position Angle (degrees East of North)
    pa_deg = float(np.degrees(np.arctan2(mu_x, mu_y)) % 360.0)

    # Residuals and Chi2
    res_x = dx_mas - (p_x[0] * dt + p_x[1])
    res_y = dy_mas - (p_y[0] * dt + p_y[1])
    chi2_x = float(np.sum((res_x**2) * (wx if wx is not None else 1.0)))
    chi2_y = float(np.sum((res_y**2) * (wy if wy is not None else 1.0)))
    chi2 = chi2_x + chi2_y
    dof = max(1, 2 * n - 4)
    reduced_chi2 = chi2 / dof

    return ProperMotionFit(
        mu_ra_cosdec_masyr=mu_x,
        mu_dec_masyr=mu_y,
        mu_masyr=mu_total_mas,
        mu_arcsec_yr=mu_total_arcsec,
        mu_err_arcsec_yr=err_total_arcsec,
        pa_deg=pa_deg,
        chi2=chi2,
        reduced_chi2=reduced_chi2,
        n_epochs=n,
        time_baseline_yr=baseline_yr,
    )


def star_motion_opinion(
    fit: ProperMotionFit,
    truth_pm: float | None = None,
    truth_source: str | None = None,
    parallax_mas: float | None = None,
) -> MotionOpinion:
    """Generate a contract-conforming MotionOpinion for a star or brown dwarf."""
    # Near-zero motion (< 0.15"/yr) classified as static
    is_static = fit.mu_arcsec_yr < 0.15 or (fit.mu_err_arcsec_yr > 0 and fit.mu_arcsec_yr < 2.0 * fit.mu_err_arcsec_yr)

    kind = "static" if is_static else "proper_motion"

    # Quality estimate based on SNR and epochs
    snr = fit.mu_arcsec_yr / fit.mu_err_arcsec_yr if fit.mu_err_arcsec_yr > 0 else 0.0
    if fit.n_epochs >= 3 and (snr > 5.0 or is_static):
        quality = "good"
    elif fit.n_epochs >= 2 and snr > 2.0:
        quality = "fair"
    else:
        quality = "poor"

    # Motion alone gives no distance for a star (SPHEREx can't measure parallax, docs/04 §2), and a catalogue
    # parallax is a comparison value, not our measurement, so it never goes into the opinion.
    del parallax_mas
    dist = Distance(lo=None, hi=None, unit=None)

    method = (
        f"Linear proper motion fit across {fit.n_epochs} epochs "
        f"({fit.time_baseline_yr:.1f} yr baseline, red_chi2={fit.reduced_chi2:.2f})"
    )

    return MotionOpinion(
        kind=kind,
        value=round(fit.mu_arcsec_yr, 3),
        unit="arcsec/yr",
        err=round(fit.mu_err_arcsec_yr, 3),
        pa_deg=round(fit.pa_deg, 1),
        distance=dist,
        truth=MotionTruth(value=truth_pm, source=truth_source),
        quality=quality,
        method=method,
    )


def fit_sso_rate(
    epochs_mjd: Sequence[float],
    ra_deg: Sequence[float],
    dec_deg: Sequence[float],
) -> SSORateFit:
    """Fit apparent angular rate (arcsec/hr) across short-baseline observations."""
    n = len(epochs_mjd)
    if n < 2:
        raise ValueError("SSO rate fit requires at least 2 epochs")

    t_hr = np.array([float(m) * HOURS_PER_DAY for m in epochs_mjd], dtype=np.float64)
    dt_hr = t_hr - t_hr[0]
    total_baseline_hr = float(np.max(dt_hr))

    mean_dec = np.radians(np.mean(dec_deg))
    cos_dec = np.cos(mean_dec)

    dra_arcsec = (np.array(ra_deg, dtype=np.float64) - ra_deg[0]) * cos_dec * 3600.0
    ddec_arcsec = (np.array(dec_deg, dtype=np.float64) - dec_deg[0]) * 3600.0

    p_x, cov_x = np.polyfit(dt_hr, dra_arcsec, 1, cov=True)
    p_y, cov_y = np.polyfit(dt_hr, ddec_arcsec, 1, cov=True)

    vx = float(p_x[0])
    vy = float(p_y[0])
    err_x = float(np.sqrt(cov_x[0, 0]))
    err_y = float(np.sqrt(cov_y[0, 0]))

    rate = float(np.hypot(vx, vy))
    err = float(np.sqrt((vx * err_x) ** 2 + (vy * err_y) ** 2) / rate) if rate > 0 else float(max(err_x, err_y))
    pa = float(np.degrees(np.arctan2(vx, vy)) % 360.0)

    return SSORateFit(
        rate_arcsec_hr=rate,
        rate_err_arcsec_hr=err,
        pa_deg=pa,
        n_epochs=n,
        time_baseline_hr=total_baseline_hr,
    )


def trial_circular_orbit_rate(
    ra_deg: float,
    dec_deg: float,
    mjd: float,
    r_au: float,
) -> float | None:
    """Compute expected sky speed (arcsec/hr) for a trial circular orbit at r_au.

    Follows docs/04 §3: prograde, low-inclination circular orbit evaluated at
    observation epoch with Earth position from Astropy builtin ephemeris.
    """
    if r_au <= 0:
        return None

    t = Time(mjd, format="mjd")
    dt = 0.01  # days for velocity finite difference

    with solar_system_ephemeris.set("builtin"):
        t1 = Time(mjd - dt / 2.0, format="mjd")
        t2 = Time(mjd + dt / 2.0, format="mjd")
        e_pos1 = get_body_barycentric("earth", t1) - get_body_barycentric("sun", t1)
        e_pos2 = get_body_barycentric("earth", t2) - get_body_barycentric("sun", t2)
        e_pos = get_body_barycentric("earth", t) - get_body_barycentric("sun", t)

    r_e = np.array([e_pos.x.to_value(u.AU), e_pos.y.to_value(u.AU), e_pos.z.to_value(u.AU)])
    v_e = np.array(
        [
            (e_pos2.x - e_pos1.x).to_value(u.AU) / (dt / DAYS_PER_YEAR),
            (e_pos2.y - e_pos1.y).to_value(u.AU) / (dt / DAYS_PER_YEAR),
            (e_pos2.z - e_pos1.z).to_value(u.AU) / (dt / DAYS_PER_YEAR),
        ]
    )

    c = SkyCoord(ra=ra_deg * u.deg, dec=dec_deg * u.deg, frame="icrs")
    u_vec = np.array(
        [
            np.cos(c.dec.rad) * np.cos(c.ra.rad),
            np.cos(c.dec.rad) * np.sin(c.ra.rad),
            np.sin(c.dec.rad),
        ]
    )

    # Geocentric distance rho: solve rho^2 + 2(r_e . u) rho + (r_e^2 - r^2) = 0
    b = 2.0 * float(np.dot(r_e, u_vec))
    c_eq = float(np.dot(r_e, r_e) - r_au**2)
    disc = b**2 - 4.0 * c_eq
    if disc < 0:
        return None
    rho = (-b + math.sqrt(disc)) / 2.0
    if rho <= 0:
        return None

    r_ast = r_e + rho * u_vec
    # Circular velocity v = 2*pi / sqrt(r_au) AU/yr
    v_mag = 2.0 * math.pi / math.sqrt(r_au)

    # Low inclination near ecliptic plane
    eps = math.radians(23.43928)
    l_hat = np.array([0.0, -math.sin(eps), math.cos(eps)])
    v_dir = np.cross(l_hat, r_ast)
    norm = np.linalg.norm(v_dir)
    if norm == 0:
        return None
    v_ast = v_mag * (v_dir / norm)

    v_rel = v_ast - v_e
    v_perp = v_rel - np.dot(v_rel, u_vec) * u_vec
    omega_rad_yr = np.linalg.norm(v_perp) / rho
    omega_arcsec_hr = float(omega_rad_yr * ARCSEC_PER_RAD / (DAYS_PER_YEAR * HOURS_PER_DAY))
    return omega_arcsec_hr


def rate_to_distance_range(
    rate_arcsec_hr: float,
    rate_err_arcsec_hr: float,
    obs_time_mjd: float,
    ra_deg: float,
    dec_deg: float,
    r_min_au: float = 0.8,
    r_max_au: float = 60.0,
    n_grid: int = 120,
) -> tuple[float, float]:
    """Invert measured sky rate to heliocentric distance range [r_lo, r_hi] in AU."""
    trial_r = np.linspace(r_min_au, r_max_au, n_grid)
    model_rates: list[tuple[float, float]] = []

    for r in trial_r:
        mr = trial_circular_orbit_rate(ra_deg, dec_deg, obs_time_mjd, float(r))
        if mr is not None and math.isfinite(mr):
            model_rates.append((float(r), mr))

    if not model_rates:
        return (r_min_au, r_max_au)

    # Tolerance window (default 2 sigma, or at least 15%)
    tol = max(2.0 * rate_err_arcsec_hr, 0.15 * rate_arcsec_hr)
    matching_r = [r for r, mr in model_rates if abs(mr - rate_arcsec_hr) <= tol]

    if not matching_r:
        # If no trial matches within tol, take closest trial and ±15% bracket
        best_r = min(model_rates, key=lambda pair: abs(pair[1] - rate_arcsec_hr))[0]
        return (max(r_min_au, round(best_r * 0.85, 2)), min(r_max_au, round(best_r * 1.15, 2)))

    return (round(float(min(matching_r)), 2), round(float(max(matching_r)), 2))


def asteroid_motion_opinion(
    fit: SSORateFit,
    distance_range_au: tuple[float, float],
    truth_dist_au: float | None = None,
    truth_source: str | None = None,
) -> MotionOpinion:
    """Generate contract-conforming MotionOpinion for an asteroid or comet."""
    quality = "good" if fit.n_epochs >= 3 and fit.rate_err_arcsec_hr < 0.2 * fit.rate_arcsec_hr else "fair"
    method = (
        f"Keplerian trial circular orbit grid (0.8–60 AU) evaluated at {fit.n_epochs} epochs "
        f"({fit.time_baseline_hr:.2f} hr baseline)"
    )

    return MotionOpinion(
        kind="sso_rate",
        value=round(fit.rate_arcsec_hr, 3),
        unit="arcsec/hr",
        err=round(fit.rate_err_arcsec_hr, 3),
        pa_deg=round(fit.pa_deg, 1),
        distance=Distance(lo=distance_range_au[0], hi=distance_range_au[1], unit="au"),
        truth=MotionTruth(value=truth_dist_au, source=truth_source),
        quality=quality,
        method=method,
    )
