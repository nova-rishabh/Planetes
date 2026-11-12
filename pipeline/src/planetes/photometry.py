"""Forced ePSF and aperture photometry engine for SPHEREx frames (Deliverable D2.4).

Algorithmic approach inspired by SPHEREx xcavation (MIT, https://github.com/spx-xcavation):
- Zone-matched oversampled ePSF selection via detector coordinates ('A' WCS / CRPIX1A, CRPIX2A)
- Sub-pixel shifted & integrated PSF model normalized to unit sum
- Weighted linear least-squares fit (amplitude + local sky background) using VARIANCE HDU
- Automatic circular aperture + sigma-clipped annulus fallback
- Conversion from surface brightness (MJy/sr) to integrated flux density (uJy)
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC_DIR = str(Path(__file__).resolve().parents[1])
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

import io
import math
import warnings
from typing import Any, Literal

import astropy.units as u
import numpy as np
from astropy import log as astropy_log
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.time import Time
from astropy.wcs import WCS, FITSFixedWarning
from astropy.wcs.utils import proj_plane_pixel_area
from scipy.ndimage import shift as ndimage_shift

from planetes.contracts import (
    Detector,
    ProperMotion,
    SpectrumPoint,
    SpectrumProvenance,
    SpectrumResult,
    SpectrumSummary,
    SpectrumTarget,
)
from planetes.frames import (
    SPHEREX_PIXEL_SCALE_DEG,
    classify_flags,
    extract_wavelength,
    flag_bits,
)

# Silence noisy SIP header warnings on SPHEREx cutouts
astropy_log.setLevel("ERROR")


def propagate_position(
    ra_deg: float,
    dec_deg: float,
    mjd: float,
    pm: ProperMotion | dict[str, float] | None = None,
) -> tuple[float, float]:
    """Propagate ICRS coordinates from ref_epoch_jyear to observation MJD using Astropy SkyCoord."""
    if pm is None or mjd <= 0.0:
        return float(ra_deg), float(dec_deg)

    if isinstance(pm, dict):
        pm_ra = float(pm.get("pm_ra_masyr", 0.0))
        pm_dec = float(pm.get("pm_dec_masyr", 0.0))
        ref_epoch = float(pm.get("ref_epoch_jyear", 2000.0))
    else:
        pm_ra = float(pm.pm_ra_masyr)
        pm_dec = float(pm.pm_dec_masyr)
        ref_epoch = float(pm.ref_epoch_jyear)

    star = SkyCoord(
        ra=ra_deg * u.deg,
        dec=dec_deg * u.deg,
        pm_ra_cosdec=pm_ra * u.mas / u.yr,
        pm_dec=pm_dec * u.mas / u.yr,
        obstime=Time(ref_epoch, format="jyear"),
    )
    moved = star.apply_space_motion(new_obstime=Time(mjd, format="mjd"))
    return float(moved.ra.deg), float(moved.dec.deg)


def get_pixel_solid_angle_sr(wcs: WCS) -> float:
    """Calculate pixel solid angle in steradians from sky WCS (nominal ~9.035e-10 sr)."""
    try:
        pix_area_deg2 = float(proj_plane_pixel_area(wcs))
        if not math.isfinite(pix_area_deg2) or pix_area_deg2 <= 0:
            pix_area_deg2 = SPHEREX_PIXEL_SCALE_DEG**2
    except Exception:
        pix_area_deg2 = SPHEREX_PIXEL_SCALE_DEG**2

    deg2_to_sr = (math.pi / 180.0) ** 2
    return float(pix_area_deg2 * deg2_to_sr)


def get_pair_id(detector: int) -> str | None:
    """Return simultaneous detector pair ID (D1&D4, D2&D5, D3&D6)."""
    pair_map = {1: "D1&D4", 4: "D1&D4", 2: "D2&D5", 5: "D2&D5", 3: "D3&D6", 6: "D3&D6"}
    return pair_map.get(detector)


def _detector_coords(image_hdu: fits.ImageHDU, x_pix: float, y_pix: float) -> tuple[float, float]:
    """Map 0-based cutout (x_pix, y_pix) to full-detector pixel coordinates via 'A' WCS."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=FITSFixedWarning)
        try:
            wcs_a = WCS(image_hdu.header, key="A")
            xd, yd = wcs_a.pixel_to_world_values(x_pix, y_pix)
            return float(np.squeeze(xd)), float(np.squeeze(yd))
        except Exception:
            crpix1a = float(image_hdu.header.get("CRPIX1A", 0.0))
            crpix2a = float(image_hdu.header.get("CRPIX2A", 0.0))
            crval1a = float(image_hdu.header.get("CRVAL1A", 0.0))
            crval2a = float(image_hdu.header.get("CRVAL2A", 0.0))
            return (x_pix + 1.0 - crpix1a + crval1a), (y_pix + 1.0 - crpix2a + crval2a)


def _build_shifted_psf_stamp(
    hdul: fits.HDUList,
    image_hdu: fits.ImageHDU,
    x_pix: float,
    y_pix: float,
    stamp_shape: tuple[int, int],
) -> np.ndarray | None:
    """Extract zone-matched PSF (EPSF table for QR3 or PSF cube for QR2), shift to (x_pix, y_pix),
    integrate oversampled subpixels onto the native pixel grid, and normalize sum(PSF) = 1.
    """
    x_det, y_det = _detector_coords(image_hdu, x_pix, y_pix)
    oversamp_psf: np.ndarray | None = None
    ov_x, ov_y = 5, 5

    if "EPSF" in hdul and hdul["EPSF"].data is not None:
        epsf_hdu = hdul["EPSF"]
        tbl = epsf_hdu.data
        ov_x = int(epsf_hdu.header.get("OVSMPX") or epsf_hdu.header.get("OVERSAMP") or 5)
        ov_y = int(epsf_hdu.header.get("OVSMPY") or epsf_hdu.header.get("OVERSAMP") or 5)

        if len(tbl) > 0 and "EPSF" in tbl.columns.names:
            xc = np.asarray(tbl["XCENTER"], dtype=float)
            yc = np.asarray(tbl["YCENTER"], dtype=float)
            stamps = np.asarray(tbl["EPSF"], dtype=float)
            nstar = np.asarray(tbl["NSTAR"], dtype=int) if "NSTAR" in tbl.columns.names else np.ones(len(tbl))

            valid = (nstar > 0) & np.all(np.isfinite(stamps.reshape(len(tbl), -1)), axis=1)
            if not np.any(valid):
                valid = np.any(np.isfinite(stamps.reshape(len(tbl), -1)), axis=1)

            if np.any(valid):
                valid_idx = np.where(valid)[0]
                dist2 = (xc[valid_idx] - x_det) ** 2 + (yc[valid_idx] - y_det) ** 2
                best_row = valid_idx[int(np.argmin(dist2))]
                oversamp_psf = np.nan_to_num(stamps[best_row], nan=0.0)

    elif "PSF" in hdul and hdul["PSF"].data is not None:
        psf_hdu = hdul["PSF"]
        psf_data = np.asarray(psf_hdu.data, dtype=float)
        ov_x = int(psf_hdu.header.get("OVSMPX") or psf_hdu.header.get("OVERSAMP") or 5)
        ov_y = int(psf_hdu.header.get("OVSMPY") or psf_hdu.header.get("OVERSAMP") or 5)
        if psf_data.ndim == 3:
            nz = psf_data.shape[0]
            slice_idx = min(nz - 1, max(0, int(round((y_det / 2048.0) * (nz - 1)))))
            oversamp_psf = np.nan_to_num(psf_data[slice_idx], nan=0.0)
        elif psf_data.ndim == 2:
            oversamp_psf = np.nan_to_num(psf_data, nan=0.0)

    if oversamp_psf is None or oversamp_psf.ndim != 2:
        return None

    sh_y, sh_x = oversamp_psf.shape
    if sh_y < ov_y or sh_x < ov_x or np.sum(oversamp_psf) <= 0:
        return None

    psf_cy = (sh_y - 1) / 2.0
    psf_cx = (sh_x - 1) / 2.0

    ix0, iy0 = int(round(x_pix)), int(round(y_pix))
    dx_sub = (x_pix - ix0) * ov_x
    dy_sub = (y_pix - iy0) * ov_y

    shifted_ov = ndimage_shift(oversamp_psf, shift=(dy_sub, dx_sub), order=1, mode="constant", cval=0.0)

    ny, nx = stamp_shape
    model = np.zeros((ny, nx), dtype=np.float64)
    half_y = sh_y // (2 * ov_y)
    half_x = sh_x // (2 * ov_x)

    for dy_pix in range(-half_y, half_y + 1):
        py = iy0 + dy_pix
        if py < 0 or py >= ny:
            continue
        oy_start = int(round(psf_cy + (dy_pix - 0.5) * ov_y))
        oy_end = int(round(psf_cy + (dy_pix + 0.5) * ov_y))
        oy_start = max(0, oy_start)
        oy_end = min(sh_y, oy_end)
        if oy_end <= oy_start:
            continue

        for dx_pix in range(-half_x, half_x + 1):
            px = ix0 + dx_pix
            if px < 0 or px >= nx:
                continue
            ox_start = int(round(psf_cx + (dx_pix - 0.5) * ov_x))
            ox_end = int(round(psf_cx + (dx_pix + 0.5) * ov_x))
            ox_start = max(0, ox_start)
            ox_end = min(sh_x, ox_end)
            if ox_end <= ox_start:
                continue

            model[py, px] = float(np.sum(shifted_ov[oy_start:oy_end, ox_start:ox_end]))

    total_psf = float(np.sum(model))
    if not math.isfinite(total_psf) or total_psf <= 0.05:
        return None

    return model / total_psf


def psf_photometry_2d(
    image: np.ndarray,
    psf_model: np.ndarray,
    x: float,
    y: float,
    variance: np.ndarray | None = None,
    good_mask: np.ndarray | None = None,
    fit_radius: float = 5.5,
) -> tuple[float, float] | None:
    """Weighted linear least-squares fit of I(x, y) = F * P(x, y) + B within fit_radius."""
    ny, nx = image.shape
    yy, xx = np.indices((ny, nx))
    dist = np.sqrt((xx - x) ** 2 + (yy - y) ** 2)

    valid = (dist <= fit_radius) & np.isfinite(image) & np.isfinite(psf_model)
    if good_mask is not None:
        valid &= good_mask

    if int(np.sum(valid)) < 6:
        return None

    psf_coverage = float(np.sum(psf_model[valid]))
    if psf_coverage < 0.35:
        return None

    y_vec = image[valid]
    p_vec = psf_model[valid]

    if variance is not None and np.all(np.isfinite(variance[valid])) and np.all(variance[valid] > 0):
        w_vec = 1.0 / np.maximum(variance[valid], 1e-12)
    else:
        med = float(np.median(y_vec))
        mad = float(np.median(np.abs(y_vec - med)))
        sig = (1.4826 * mad) or float(np.std(y_vec)) or 1.0
        w_vec = np.full_like(y_vec, 1.0 / (sig**2))

    A = np.column_stack([p_vec, np.ones_like(p_vec)])
    Aw = A * w_vec[:, None]
    ata = A.T @ Aw
    try:
        cov = np.linalg.inv(ata)
    except np.linalg.LinAlgError:
        return None

    params = cov @ (Aw.T @ y_vec)
    flux_mjy_sr = float(params[0])
    var_flux = float(cov[0, 0])
    if not math.isfinite(flux_mjy_sr) or not math.isfinite(var_flux) or var_flux <= 0:
        return None

    return flux_mjy_sr, math.sqrt(var_flux)


def aperture_photometry_2d(
    image: np.ndarray,
    x: float,
    y: float,
    variance: np.ndarray | None = None,
    good_mask: np.ndarray | None = None,
    r_ap: float = 2.5,
    r_in: float = 4.5,
    r_out: float = 7.5,
) -> tuple[float, float]:
    """Perform circular aperture photometry with sigma-clipped local background annulus."""
    ny, nx = image.shape
    yy, xx = np.indices((ny, nx))
    dist = np.sqrt((xx - x) ** 2 + (yy - y) ** 2)

    valid_img = np.isfinite(image)
    if good_mask is not None:
        valid_img &= good_mask

    bkg_mask = (dist >= r_in) & (dist <= r_out) & valid_img
    if np.sum(bkg_mask) < 5:
        bkg_vals = image[valid_img] if np.any(valid_img) else np.array([0.0])
    else:
        bkg_vals = image[bkg_mask]

    med0 = float(np.median(bkg_vals))
    mad0 = float(np.median(np.abs(bkg_vals - med0)))
    sigma0 = 1.4826 * mad0 if mad0 > 0 else float(np.std(bkg_vals))
    if sigma0 > 0:
        clipped = bkg_vals[np.abs(bkg_vals - med0) <= 3.0 * sigma0]
        if len(clipped) >= 5:
            bkg_vals = clipped

    bkg_med = float(np.median(bkg_vals))
    mad = float(np.median(np.abs(bkg_vals - bkg_med)))
    bkg_std = float(1.4826 * mad) or float(np.std(bkg_vals)) or 1e-6

    ap_mask = (dist <= r_ap) & np.isfinite(image)
    n_pix = int(np.sum(ap_mask))
    if n_pix == 0:
        return 0.0, 1e-6

    raw_flux = float(np.sum(image[ap_mask]))
    net_flux = float(raw_flux - (n_pix * bkg_med))

    if variance is not None and np.all(np.isfinite(variance[ap_mask])):
        var_sum = float(np.sum(np.maximum(variance[ap_mask], 0.0)))
        bkg_err_term = (n_pix**2) * (bkg_std**2) / max(1, int(np.sum(bkg_mask)))
        flux_err = float(math.sqrt(var_sum + bkg_err_term))
    else:
        flux_err = float(math.sqrt(n_pix * (bkg_std**2)))

    return net_flux, flux_err


def measure_hdul_flux(
    hdul: fits.HDUList,
    ra: float,
    dec: float,
    pm: ProperMotion | dict[str, float] | None = None,
    method: Literal["auto", "psf", "aperture"] = "auto",
    fallback_obs_id: str = "unknown",
) -> SpectrumPoint:
    """Run forced photometry on an opened SPHEREx HDUList."""
    combined: dict[str, Any] = {}
    for hdu in hdul:
        for k, v in hdu.header.items():
            if k not in combined or combined[k] in ("N/A", None, ""):
                combined[k] = v

    image_hdu = hdul["IMAGE"] if "IMAGE" in hdul else hdul[1]
    header = image_hdu.header
    data = image_hdu.data.astype(np.float64)

    # Subtract SPHEREx zodiacal light model if present
    if "ZODI" in hdul and hdul["ZODI"].data is not None:
        data = data - hdul["ZODI"].data.astype(np.float64)

    variance = None
    if "VARIANCE" in hdul and hdul["VARIANCE"].data is not None:
        variance = hdul["VARIANCE"].data.astype(np.float64)

    obs_id = str(combined.get("OBS_ID") or fallback_obs_id)
    mjd = float(
        combined.get("MJD-OBS")
        or combined.get("MJD_OBS")
        or combined.get("OBS_MJD")
        or combined.get("MJD")
        or 0.0
    )

    obs_ra, obs_dec = propagate_position(ra, dec, mjd, pm=pm)

    det_val = combined.get("DETECTOR") or combined.get("DET_ID") or combined.get("BAND")
    detector = 1
    if det_val is not None:
        try:
            detector = int(det_val)
        except ValueError:
            for ch in str(det_val):
                if ch.isdigit() and 1 <= int(ch) <= 6:
                    detector = int(ch)
                    break

    wavelength_um, bandwidth_um = extract_wavelength(hdul)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=FITSFixedWarning)
        wcs = WCS(header)

    x_pix, y_pix = wcs.world_to_pixel_values(obs_ra, obs_dec)
    x_pix, y_pix = float(np.squeeze(x_pix)), float(np.squeeze(y_pix))

    ny, nx = data.shape
    in_bounds = (
        math.isfinite(x_pix)
        and math.isfinite(y_pix)
        and (0.0 <= x_pix < nx)
        and (0.0 <= y_pix < ny)
    )

    flags_val = 0
    saturated = False
    bad_core = False
    good_mask: np.ndarray | None = None

    if in_bounds and "FLAGS" in hdul and hdul["FLAGS"].data is not None:
        flag_data = np.asarray(hdul["FLAGS"].data, dtype=np.int64)
        xi, yi = int(round(x_pix)), int(round(y_pix))
        if 0 <= xi < nx and 0 <= yi < ny:
            flags_val = int(flag_data[yi, xi])
        try:
            bits = flag_bits(hdul["FLAGS"].header)
            fmasks = classify_flags(flag_data, bits)
            good_mask = ~fmasks.bad
            yy, xx = np.indices((ny, nx))
            core = (xx - x_pix) ** 2 + (yy - y_pix) ** 2 <= 1.5**2
            if np.any(core):
                saturated = bool(np.any(fmasks.saturated[core]))
                bad_core = bool(np.any((fmasks.cosmic | fmasks.other)[core]))
        except ValueError:
            saturated = bool(flags_val & 2)

    if not in_bounds:
        return SpectrumPoint(
            obs_id=obs_id,
            mjd=mjd,
            detector=detector,
            wavelength_um=wavelength_um,
            bandwidth_um=bandwidth_um,
            flux_ujy=None,
            flux_err_ujy=None,
            snr=None,
            flags=flags_val,
            saturated=saturated,
            used=False,
            reject_reason="target_out_of_bounds",
            pair_id=get_pair_id(detector),
            method=None,
            ra=obs_ra,
            dec=obs_dec,
        )

    used_method: Literal["psf", "aperture"] = "aperture"
    net_flux_mjy_sr: float | None = None
    flux_err_mjy_sr: float | None = None

    if method in ("auto", "psf"):
        psf_stamp = _build_shifted_psf_stamp(hdul, image_hdu, x_pix, y_pix, data.shape)
        if psf_stamp is not None:
            psf_res = psf_photometry_2d(
                data, psf_stamp, x_pix, y_pix, variance=variance, good_mask=good_mask
            )
            if psf_res is not None:
                net_flux_mjy_sr, flux_err_mjy_sr = psf_res
                used_method = "psf"

    if net_flux_mjy_sr is None or flux_err_mjy_sr is None:
        net_flux_mjy_sr, flux_err_mjy_sr = aperture_photometry_2d(
            data, x_pix, y_pix, variance=variance, good_mask=good_mask
        )
        used_method = "aperture"

    omega_pix = get_pixel_solid_angle_sr(wcs)
    flux_ujy = float(net_flux_mjy_sr * omega_pix * 1e12)
    flux_err_ujy = float(flux_err_mjy_sr * omega_pix * 1e12)
    snr = float(flux_ujy / flux_err_ujy) if flux_err_ujy > 0 else None

    used = True
    reject_reason = None
    if saturated:
        used = False
        reject_reason = "saturated"
    elif bad_core:
        used = False
        reject_reason = "bad_pixel_flag"
    elif flux_ujy < 0 and (snr is not None and snr < -3.0):
        used = False
        reject_reason = "negative_detection"

    return SpectrumPoint(
        obs_id=obs_id,
        mjd=mjd,
        detector=detector,
        wavelength_um=wavelength_um,
        bandwidth_um=bandwidth_um,
        flux_ujy=round(flux_ujy, 3),
        flux_err_ujy=round(flux_err_ujy, 3),
        snr=round(snr, 2) if snr is not None else None,
        flags=flags_val,
        saturated=saturated,
        used=used,
        reject_reason=reject_reason,
        pair_id=get_pair_id(detector),
        method=used_method,
        ra=obs_ra,
        dec=obs_dec,
    )


def measure_frame_flux(
    fits_source: str | Path | bytes,
    ra: float,
    dec: float,
    pm: ProperMotion | dict[str, float] | None = None,
    method: Literal["auto", "psf", "aperture"] = "auto",
) -> SpectrumPoint:
    """Measure forced photometry from either a FITS file path or raw FITS bytes."""
    if isinstance(fits_source, bytes):
        with fits.open(io.BytesIO(fits_source)) as hdul:
            return measure_hdul_flux(hdul, ra=ra, dec=dec, pm=pm, method=method)
    path = Path(fits_source)
    with fits.open(path) as hdul:
        return measure_hdul_flux(
            hdul, ra=ra, dec=dec, pm=pm, method=method, fallback_obs_id=path.stem
        )


def extract_spectrum(
    fits_sources: list[str | Path | bytes],
    ra: float,
    dec: float,
    pm: ProperMotion | dict[str, float] | None = None,
    method: Literal["auto", "psf", "aperture"] = "auto",
    release: Literal["QR2", "QR3"] = "QR3",
    code_version: str = "d2.4-epsf",
) -> SpectrumResult:
    """Build a complete SpectrumResult across a list of FITS paths or byte buffers."""
    if isinstance(pm, dict):
        pm_data = {"ref_epoch_jyear": 2000.0, **pm}
        pm_obj = ProperMotion(**pm_data)
    else:
        pm_obj = pm

    points: list[SpectrumPoint] = []
    bands_covered: set[int] = set()

    for src in fits_sources:
        try:
            pt = measure_frame_flux(src, ra=ra, dec=dec, pm=pm_obj, method=method)
            points.append(pt)
            if pt.used:
                bands_covered.add(int(pt.detector))
        except Exception:
            continue

    points.sort(key=lambda pt: (pt.wavelength_um or 0.0, pt.mjd))

    n_points = len(points)
    n_used = sum(1 for pt in points if pt.used)
    n_rejected = n_points - n_used

    return SpectrumResult(
        schema_version="1.0",
        target=SpectrumTarget(ra=ra, dec=dec, pm=pm_obj),
        points=points,
        summary=SpectrumSummary(
            n_points=n_points,
            n_used=n_used,
            n_rejected=n_rejected,
            bands_covered=[Detector(b) for b in sorted(bands_covered)],
        ),
        provenance=SpectrumProvenance(
            release=release,
            code_version=code_version,
        ),
    )


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[3]
    fits_files = sorted((root / ".planetes-cache").rglob("*.fits"))
    if not fits_files:
        fits_files = sorted((root / "pipeline" / "tests" / "data").glob("*.fits"))

    print(f"Found {len(fits_files)} FITS files.")
    if fits_files:
        res = extract_spectrum(fits_files, ra=269.46293, dec=4.72563)
        print(f"Extracted {res.summary.n_used}/{res.summary.n_points} points:")
        for pt in res.points:
            wave_str = f"{pt.wavelength_um:.3f} um" if pt.wavelength_um is not None else "N/A"
            print(
                f"D{pt.detector} | {wave_str} | "
                f"Flux: {pt.flux_ujy} uJy | SNR: {pt.snr} | Method: {pt.method} | Used: {pt.used} ({pt.reject_reason})"
            )
# --- Compatibility helpers imported by test_spectrum_typing.py ---
from dataclasses import dataclass, field as _dc_field


@dataclass
class PointFlux:
    """One forced-photometry measurement compatibility dataclass."""

    flux_ujy: float | None
    flux_err_ujy: float | None
    flags: int
    flag_names: list[str] = _dc_field(default_factory=list)
    saturated: bool = False
    wavelength_um: float | None = None
    bandwidth_um: float | None = None
    aperture_correction: float | None = None
    problem: str | None = None

    @property
    def snr(self) -> float | None:
        if self.flux_ujy is None or not self.flux_err_ujy:
            return None
        return self.flux_ujy / self.flux_err_ujy


def pixel_solid_angle_sr(wcs: WCS, x: float, y: float) -> float:
    """Solid angle of one pixel at (x, y), from the local WCS Jacobian."""
    cx = wcs.pixel_to_world(x + 0.5, y)
    cx0 = wcs.pixel_to_world(x - 0.5, y)
    cy = wcs.pixel_to_world(x, y + 0.5)
    cy0 = wcs.pixel_to_world(x, y - 0.5)
    ax = np.array([v.to_value(u.rad) for v in cx0.spherical_offsets_to(cx)])
    ay = np.array([v.to_value(u.rad) for v in cy0.spherical_offsets_to(cy)])
    return float(abs(ax[0] * ay[1] - ax[1] * ay[0]))


def _enclosed_fraction(psf: np.ndarray, oversample: int, radius_px: float) -> float:
    n = psf.shape[0]
    yy, xx = np.indices(psf.shape)
    centre = (n - 1) / 2.0
    inside = (xx - centre) ** 2 + (yy - centre) ** 2 <= (radius_px * oversample) ** 2
    total = float(psf.sum())
    return float(psf[inside].sum() / total) if total > 0 else float("nan")
