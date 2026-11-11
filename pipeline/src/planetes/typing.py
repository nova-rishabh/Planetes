"""Spectral typer (D4.3): SPHEREx spectrum -> spectral type -> photometric distance -> SpectrumOpinion.

Templates: the SpeX Prism Library spectral standards M0-T9 (IRTF SpeX, R~120, 0.65-2.56 um), as listed in
SPLAT (Burgasser; MIT) STANDARDS_DWARF_SPEX-PRISM.csv, stored as F_nu normalised to their peak in
data/spex_standards.csv. Only SPHEREx points inside the template range (detectors D1-D3) are used.

Fit: each template is averaged over each point's bandwidth, scaled by least squares, and ranked by chi^2.
Distance: 2MASS J from the scaled template (mean F_nu over 1.11-1.39 um, zero point 1594 Jy, Cohen et al.
2003) and absolute M_J from the Dupuy & Liu (2012) polynomial (M6-T9, scatter 0.40 mag), as tabulated in SPLAT.
"""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from functools import lru_cache
from importlib import resources

import numpy as np

from .contracts import Distance, SpectrumOpinion, SpectrumPoint

# Dupuy & Liu 2012, 2MASS J: M_J = polyval(COEFF, spt - 10) with M0 = 10, L0 = 20, T0 = 30 (SPLAT convention).
DUPUY2012_2MASS_J = [-0.000000784614, 0.000100820, -0.00482973, 0.111715, -1.33053, 8.16362, -9.67994]
DUPUY2012_RANGE = (16.0, 39.0)  # M6 to T9
DUPUY2012_SCATTER_MAG = 0.40
J_ZERO_POINT_JY = 1594.0  # 2MASS J, Cohen et al. 2003
J_BAND_UM = (1.11, 1.39)
MIN_POINTS = 8


@dataclass
class TypeFit:
    spt: str
    spt_num: float
    chi2_red: float
    scale: float
    n_points: int
    acceptable: list[str]


def spt_number(spt: str) -> float:
    """'M0' -> 10, 'L0' -> 20, 'T1' -> 31 (SPLAT numbering)."""
    return {"M": 10.0, "L": 20.0, "T": 30.0}[spt[0]] + float(spt[1:])


@lru_cache(maxsize=1)
def load_standards() -> dict[str, tuple[np.ndarray, np.ndarray]]:
    text = resources.files("planetes").joinpath("data/spex_standards.csv").read_text(encoding="utf-8")
    acc: dict[str, tuple[list[float], list[float]]] = {}
    for row in csv.DictReader(text.splitlines()):
        w, f = acc.setdefault(row["spt"], ([], []))
        w.append(float(row["wavelength_um"]))
        f.append(float(row["fnu_norm"]))
    return {k: (np.array(w), np.array(f)) for k, (w, f) in acc.items()}


def _band_average(w: np.ndarray, f: np.ndarray, centre: float, width: float) -> float:
    lo, hi = centre - width / 2.0, centre + width / 2.0
    inside = (w >= lo) & (w <= hi)
    if inside.sum() >= 2:
        return float(f[inside].mean())
    return float(np.interp(centre, w, f))


def usable_points(points: list[SpectrumPoint]) -> list[SpectrumPoint]:
    lo, hi = 0.70, 2.50
    return [
        p
        for p in points
        if p.used and p.flux_ujy is not None and p.flux_err_ujy and p.wavelength_um and lo <= p.wavelength_um <= hi
    ]


def fit_type(points: list[SpectrumPoint]) -> TypeFit | None:
    pts = usable_points(points)
    if len(pts) < MIN_POINTS:
        return None
    lam = np.array([p.wavelength_um for p in pts], dtype=float)
    bw = np.array([p.bandwidth_um or 0.0 for p in pts], dtype=float)
    f = np.array([p.flux_ujy for p in pts], dtype=float)
    s = np.array([p.flux_err_ujy for p in pts], dtype=float)
    results: list[tuple[float, str, float]] = []
    for spt, (tw, tf) in load_standards().items():
        t = np.array([_band_average(tw, tf, c, b) for c, b in zip(lam, bw, strict=True)])
        a = float(np.sum(f * t / s**2) / np.sum(t**2 / s**2))
        chi2 = float(np.sum(((f - a * t) / s) ** 2)) / max(len(pts) - 1, 1)
        results.append((chi2, spt, a))
    results.sort()
    best_chi2, best_spt, best_scale = results[0]
    # Types whose fit is statistically as good as the best one (chi^2 within the expected spread).
    tol = best_chi2 * (1.0 + 2.0 * math.sqrt(2.0 / max(len(pts) - 1, 1)))
    acceptable = sorted((spt for c, spt, _ in results if c <= tol), key=spt_number)
    return TypeFit(best_spt, spt_number(best_spt), best_chi2, best_scale, len(pts), acceptable)


def apparent_j_mag(fit: TypeFit) -> float | None:
    w, f = load_standards()[fit.spt]
    band = (w >= J_BAND_UM[0]) & (w <= J_BAND_UM[1])
    fnu_ujy = fit.scale * float(f[band].mean())
    if fnu_ujy <= 0:
        return None
    return -2.5 * math.log10(fnu_ujy * 1e-6 / J_ZERO_POINT_JY)


def absolute_j_mag(spt_num: float) -> float | None:
    if not DUPUY2012_RANGE[0] <= spt_num <= DUPUY2012_RANGE[1]:
        return None
    return float(np.polyval(DUPUY2012_2MASS_J, spt_num - 10.0))


def distance_range_pc(fit: TypeFit) -> tuple[float, float] | None:
    m = apparent_j_mag(fit)
    if m is None:
        return None
    absolute = [absolute_j_mag(spt_number(s)) for s in fit.acceptable]
    absolute = [a for a in absolute if a is not None]
    if not absolute:
        return None
    lo_m = min(absolute) - DUPUY2012_SCATTER_MAG  # intrinsically brighter -> farther
    hi_m = max(absolute) + DUPUY2012_SCATTER_MAG
    far = 10 ** ((m - lo_m + 5) / 5)
    near = 10 ** ((m - hi_m + 5) / 5)
    return near, far


def spectrum_opinion(points: list[SpectrumPoint]) -> tuple[SpectrumOpinion, TypeFit | None]:
    """The spectrum opinion for the verdict. 'none' with quality poor when the spectrum can't be typed."""
    fit = fit_type(points)
    method = "SpeX standard chi2 fit (D1-D3) + Dupuy & Liu 2012 M_J"
    none = SpectrumOpinion(
        kind="none",
        **{"class": None},
        temperature_k=None,
        distance=Distance(lo=None, hi=None, unit=None),
        quality="poor",
        method=method,
    )
    if fit is None:
        return none, None
    d = distance_range_pc(fit)
    label = fit.spt if len(fit.acceptable) == 1 else f"{fit.acceptable[0]}-{fit.acceptable[-1]}"
    quality = "good" if fit.chi2_red < 3 and len(fit.acceptable) <= 3 else "fair" if fit.chi2_red < 10 else "poor"
    return (
        SpectrumOpinion(
            kind="template",
            **{"class": label},
            temperature_k=None,
            distance=Distance(lo=d[0], hi=d[1], unit="pc") if d else Distance(lo=None, hi=None, unit=None),
            quality=quality,
            method=method,
        ),
        fit,
    )
