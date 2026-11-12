"""Forced aperture photometry on one SPHEREx cutout (D2.4 aperture method; docs/02 §4.10, §5).

Interim version written while the PSF-fit engine (D2.4, Tirth) is in progress: an aperture of
APERTURE_PX pixels at the exact (sub-pixel) source position, a local sky annulus, and an aperture
correction taken from the file's own PSF, so the flux is the total flux of a point source.

Read from the real files (checked Nov 12 on cached QR2 and QR3 cutouts):
- IMAGE and ZODI in MJy/sr, VARIANCE in MJy²/sr². Zodiacal light is subtracted here.
- QR2 (VERSION 6.x): PSF image cube (121 zones, 101×101, OVERSAMP 10), zone centres XCTR_i / YCTR_i.
- QR3 (VERSION 7.x): EPSF table (441 zones, 33×33, OVSMPX 5), zone centres XCENTER / YCENTER.
- Both PSFs sum to 1. Zones are in parent-image pixels; the cutout's "A" WCS (CRPIX1A/CRPIX2A,
  "0-based active pixel coordinates") maps cutout pixels to parent pixels.
"""

from __future__ import annotations

import io
import warnings
from dataclasses import dataclass, field

import astropy.units as u
import numpy as np
from astropy.io import fits
from astropy.wcs import WCS, FITSFixedWarning
from photutils.aperture import CircularAnnulus, CircularAperture, aperture_photometry

from .frames import INFORMATIONAL_FLAGS, SATURATED_FLAGS, extract_wavelength, flag_bits

APERTURE_PX = 3.0
ANNULUS_PX = (6.0, 9.0)
MJY_PER_SR_TO_UJY_PER_SR = 1e12


@dataclass
class PointFlux:
    """One forced-photometry measurement. flux_ujy is None when it could not be measured (see `problem`)."""

    flux_ujy: float | None
    flux_err_ujy: float | None
    flags: int
    flag_names: list[str] = field(default_factory=list)
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


def _sky_wcs(header: fits.Header) -> WCS:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=FITSFixedWarning)
        return WCS(header)


def pixel_solid_angle_sr(wcs: WCS, x: float, y: float) -> float:
    """Solid angle of one pixel at (x, y), from the local WCS Jacobian (includes SIP distortion)."""
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


def aperture_correction(hdul: fits.HDUList, x: float, y: float, radius_px: float = APERTURE_PX) -> float | None:
    """Fraction of a point source's light inside the aperture, from the PSF zone nearest the source."""
    header = hdul["IMAGE"].header
    if "CRPIX1A" not in header or "CRPIX2A" not in header:
        return None
    # cutout 0-based pixel -> parent 0-based pixel (FITS pixels are 1-based, hence +1).
    px = x + 1.0 - float(header["CRPIX1A"])
    py = y + 1.0 - float(header["CRPIX2A"])
    names = [h.name for h in hdul]
    if "EPSF" in names:  # QR3
        t = hdul["EPSF"].data
        i = int(np.argmin((t["XCENTER"] - px) ** 2 + (t["YCENTER"] - py) ** 2))
        oversample = int(hdul["EPSF"].header["OVSMPX"])
        return _enclosed_fraction(np.asarray(t["EPSF"][i], dtype=float), oversample, radius_px)
    if "PSF" in names:  # QR2
        h = hdul["PSF"].header
        n_zones = hdul["PSF"].data.shape[0]
        xc = np.array([h[f"XCTR_{k}"] for k in range(1, n_zones + 1)], dtype=float)
        yc = np.array([h[f"YCTR_{k}"] for k in range(1, n_zones + 1)], dtype=float)
        i = int(np.argmin((xc - px) ** 2 + (yc - py) ** 2))
        return _enclosed_fraction(np.asarray(hdul["PSF"].data[i], dtype=float), int(h["OVERSAMP"]), radius_px)
    return None


def measure(fits_bytes: bytes, ra_deg: float, dec_deg: float) -> PointFlux:
    """Forced aperture photometry of the point source at (ra_deg, dec_deg) in one cutout."""
    with fits.open(io.BytesIO(fits_bytes)) as hdul:
        header = hdul["IMAGE"].header
        image = hdul["IMAGE"].data.astype(np.float64) - hdul["ZODI"].data.astype(np.float64)
        variance = hdul["VARIANCE"].data.astype(np.float64)
        flags = np.asarray(hdul["FLAGS"].data).astype(np.int64)
        bits = flag_bits(hdul["FLAGS"].header)
        wcs = _sky_wcs(header)
        x, y = (float(v) for v in wcs.world_to_pixel_values(ra_deg, dec_deg))
        wavelength_um, bandwidth_um = extract_wavelength(hdul)
        ny, nx = image.shape
        edge = APERTURE_PX + 1.0  # aperture fully inside; the sky check below needs enough annulus pixels
        if not (edge <= x <= nx - 1 - edge and edge <= y <= ny - 1 - edge):
            return PointFlux(None, None, 0, wavelength_um=wavelength_um, bandwidth_um=bandwidth_um, problem="outside")
        corr = aperture_correction(hdul, x, y)

    ap = CircularAperture((x, y), r=APERTURE_PX)
    ap_mask = ap.to_mask(method="center").to_image(image.shape).astype(bool)
    raw_flags = int(np.bitwise_or.reduce(flags[ap_mask])) if ap_mask.any() else 0
    names = sorted(n for n, b in bits.items() if raw_flags & (1 << b))
    saturated = any(n in SATURATED_FLAGS for n in names)
    result = PointFlux(None, None, raw_flags, names, saturated, wavelength_um, bandwidth_um, corr)

    # Sky: sigma-clipped median of unflagged annulus pixels (informational bits like SOURCE are fine).
    bad_bits = sum(1 << b for n, b in bits.items() if n not in INFORMATIONAL_FLAGS)
    ann_mask = CircularAnnulus((x, y), *ANNULUS_PX).to_mask(method="center").to_image(image.shape).astype(bool)
    sky = image[ann_mask & ((flags & bad_bits) == 0) & np.isfinite(image)]
    if sky.size < 10 or not np.isfinite(image[ap_mask]).all() or not np.isfinite(variance[ap_mask]).all():
        result.problem = "no_sky" if sky.size < 10 else "bad_pixels"
        return result
    med = float(np.median(sky))
    for _ in range(3):
        sd = float(np.std(sky))
        keep = np.abs(sky - med) < 3 * sd if sd > 0 else np.ones(sky.shape, bool)
        sky = sky[keep]
        med = float(np.median(sky))
    sky_err = float(np.std(sky) / np.sqrt(sky.size))

    tbl = aperture_photometry(image, ap, error=np.sqrt(np.clip(variance, 0, None)))
    area = float(ap.area)
    net = float(tbl["aperture_sum"][0]) - med * area  # MJy/sr summed over pixels
    err = float(np.hypot(float(tbl["aperture_sum_err"][0]), sky_err * area))

    omega = pixel_solid_angle_sr(wcs, x, y)
    scale = omega * MJY_PER_SR_TO_UJY_PER_SR / (corr if corr and corr > 0 else 1.0)
    result.flux_ujy = net * scale
    result.flux_err_ujy = err * scale
    if not corr:
        result.problem = "no_psf"
    return result
