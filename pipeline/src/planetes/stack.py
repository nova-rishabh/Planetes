"""SPHEREx image stacking, difference, sum, and RGB colour composite modes (Deliverable D2.3).

Implements:
- Per-epoch, per-detector inverse-variance-weighted coadds (excluding flagged pixels)
- Epoch B - Epoch A difference images with propagated variance
- Multi-epoch deep sum stacks
- 3-band RGB colour composites (D1+D2 -> Blue, D3+D4 -> Green, D5+D6 -> Red)
- North-up WebP rendering helpers for difference and RGB composite products
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC_DIR = str(Path(__file__).resolve().parents[1])
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

import io
import warnings
from dataclasses import dataclass
from typing import Sequence

import numpy as np
from astropy import log as astropy_log
from astropy.io import fits
from astropy.wcs import WCS, FITSFixedWarning
from PIL import Image

from planetes import frames, render

astropy_log.setLevel("ERROR")


@dataclass
class CoaddResult:
    """Result of stacking or differencing reprojected SPHEREx frames."""

    image: np.ndarray
    variance: np.ndarray
    coverage: np.ndarray
    detector: int | None
    epoch_index: int | None
    mjd_start: float
    mjd_end: float
    n_frames: int
    wavelength_um: float | None = None


def prepare_reprojected_variance(
    fits_bytes: bytes,
    ref_wcs: WCS,
    grid_shape: tuple[int, int] = (64, 64),
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Extract zodi-subtracted image, variance, and good-pixel mask reprojected onto ref_wcs."""
    with fits.open(io.BytesIO(fits_bytes)) as hdul:
        header = hdul["IMAGE"].header
        image = hdul["IMAGE"].data.astype(np.float64) - hdul["ZODI"].data.astype(np.float64)
        if "VARIANCE" in hdul and hdul["VARIANCE"].data is not None:
            var_raw = hdul["VARIANCE"].data.astype(np.float64)
        else:
            mad = float(np.nanmedian(np.abs(image - np.nanmedian(image))))
            sig = (1.4826 * mad) or 1.0
            var_raw = np.full_like(image, sig**2)

        flags = np.asarray(hdul["FLAGS"].data, dtype=np.int64)
        bits = frames.flag_bits(hdul["FLAGS"].header)

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=FITSFixedWarning)
            input_wcs = WCS(header)

    reproj_img = frames.reproject_to_grid(image, input_wcs, ref_wcs, grid_shape)
    reproj_var = frames.reproject_to_grid(var_raw, input_wcs, ref_wcs, grid_shape)
    reproj_flags = frames.reproject_flags(flags, input_wcs, ref_wcs, grid_shape)
    masks = frames.classify_flags(reproj_flags, bits)

    # Spread raw saturation mask identically to frames.prepare_frame
    sat_raw = frames.classify_flags(flags, bits).saturated.astype(np.float64)
    masks.saturated |= frames.reproject_to_grid(sat_raw, input_wcs, ref_wcs, grid_shape) > 0

    good = (
        (~masks.outside)
        & (~masks.bad)
        & np.isfinite(reproj_img)
        & np.isfinite(reproj_var)
        & (reproj_var > 0.0)
    )
    return reproj_img, reproj_var, good


def inverse_variance_stack(
    images: Sequence[np.ndarray],
    variances: Sequence[np.ndarray],
    good_masks: Sequence[np.ndarray],
    detector: int | None = None,
    epoch_index: int | None = None,
    mjds: Sequence[float] | None = None,
    wavelengths: Sequence[float | None] | None = None,
) -> CoaddResult:
    """Compute inverse-variance-weighted coadd excluding flagged pixels."""
    if not images:
        raise ValueError("Cannot stack an empty list of images")

    shape = images[0].shape
    num = np.zeros(shape, dtype=np.float64)
    den = np.zeros(shape, dtype=np.float64)
    cov = np.zeros(shape, dtype=np.int32)

    for img, var, good in zip(images, variances, good_masks, strict=True):
        valid = good & np.isfinite(img) & np.isfinite(var) & (var > 0.0)
        w = np.where(valid, 1.0 / np.maximum(var, 1e-12), 0.0)
        num += np.where(valid, w * img, 0.0)
        den += w
        cov += valid.astype(np.int32)

    has_data = den > 0.0
    out_img = np.where(has_data, num / np.where(has_data, den, 1.0), np.nan)
    out_var = np.where(has_data, 1.0 / np.where(has_data, den, 1.0), np.nan)

    valid_mjds = [float(m) for m in (mjds or []) if m is not None]
    valid_waves = [float(w) for w in (wavelengths or []) if w is not None]

    return CoaddResult(
        image=out_img,
        variance=out_var,
        coverage=cov,
        detector=detector,
        epoch_index=epoch_index,
        mjd_start=min(valid_mjds) if valid_mjds else 0.0,
        mjd_end=max(valid_mjds) if valid_mjds else 0.0,
        n_frames=len(images),
        wavelength_um=float(np.median(valid_waves)) if valid_waves else None,
    )


def difference_coadds(epoch_a: CoaddResult, epoch_b: CoaddResult) -> CoaddResult:
    """Compute Epoch B - Epoch A difference image with propagated variance (var_A + var_B)."""
    if epoch_a.image.shape != epoch_b.image.shape:
        raise ValueError("Epoch A and Epoch B images must have identical shapes")

    diff_img = epoch_b.image - epoch_a.image
    diff_var = epoch_a.variance + epoch_b.variance
    cov = np.minimum(epoch_a.coverage, epoch_b.coverage)

    return CoaddResult(
        image=diff_img,
        variance=diff_var,
        coverage=cov,
        detector=epoch_b.detector or epoch_a.detector,
        epoch_index=epoch_b.epoch_index,
        mjd_start=epoch_a.mjd_start,
        mjd_end=epoch_b.mjd_end,
        n_frames=epoch_a.n_frames + epoch_b.n_frames,
        wavelength_um=epoch_b.wavelength_um or epoch_a.wavelength_um,
    )


def sum_coadds(coadds: Sequence[CoaddResult]) -> CoaddResult:
    """Combine multiple epoch coadds into a single deep inverse-variance-weighted sum."""
    if not coadds:
        raise ValueError("Cannot sum an empty sequence of coadds")

    images = [c.image for c in coadds]
    variances = [c.variance for c in coadds]
    masks = [np.isfinite(c.image) & np.isfinite(c.variance) & (c.variance > 0) for c in coadds]
    mjds = [c.mjd_start for c in coadds] + [c.mjd_end for c in coadds]
    waves = [c.wavelength_um for c in coadds]

    res = inverse_variance_stack(
        images,
        variances,
        masks,
        detector=coadds[0].detector,
        epoch_index=None,
        mjds=mjds,
        wavelengths=waves,
    )
    res.n_frames = sum(c.n_frames for c in coadds)
    return res


def _asinh_normalize(image: np.ndarray) -> np.ndarray:
    """Stretch a single 2D array into [0, 1] using render.shared_stretch and render.ASINH_K."""
    stretch = render.shared_stretch([image])
    if stretch is None:
        return np.zeros_like(image, dtype=np.float64)
    denom = max(stretch.hi - stretch.lo, 1e-9)
    x = (image - stretch.lo) / denom
    v = np.arcsinh(render.ASINH_K * np.clip(x, 0.0, None)) / np.arcsinh(render.ASINH_K)
    return np.nan_to_num(np.clip(v, 0.0, 1.0), nan=0.0)


def colour_composite(detector_coadds: dict[int, CoaddResult]) -> np.ndarray:
    """Build an (H, W, 3) uint8 RGB colour composite (north up):
    - Blue  = D1 + D2 (0.75 - 1.63 um)
    - Green = D3 + D4 (1.63 - 3.29 um)
    - Red   = D5 + D6 (3.29 - 5.00 um)
    """
    sample = next(iter(detector_coadds.values()))
    shape = sample.image.shape

    def _combine_band(dets: tuple[int, int]) -> np.ndarray:
        present = [detector_coadds[d] for d in dets if d in detector_coadds]
        if not present:
            return np.zeros(shape, dtype=np.float64)
        coadd = sum_coadds(present) if len(present) > 1 else present[0]
        return _asinh_normalize(coadd.image)

    blue = _combine_band((1, 2))
    green = _combine_band((3, 4))
    red = _combine_band((5, 6))

    rgb = np.stack([red, green, blue], axis=-1)
    return np.flipud(np.rint(rgb * 255.0).astype(np.uint8))


def colour_to_webp(rgb: np.ndarray) -> bytes:
    """Encode a north-up (H, W, 3) uint8 RGB composite as lossless WebP."""
    buf = io.BytesIO()
    Image.fromarray(rgb, mode="RGB").save(buf, format="WEBP", lossless=True)
    return buf.getvalue()


def difference_to_webp(diff: CoaddResult) -> bytes:
    """Render a symmetric signed difference image (Epoch B - Epoch A) as north-up lossless WebP.

    Negative residuals (Epoch A position) map to cool blue/cyan; zero maps to dark neutral;
    positive detections (Epoch B position) map to warm amber/white.
    """
    img = diff.image
    finite = img[np.isfinite(img)]
    scale = float(np.percentile(np.abs(finite), 99.5)) if finite.size else 1.0
    scale = max(scale, 1e-6)

    norm = np.arcsinh(render.ASINH_K * (img / scale)) / np.arcsinh(render.ASINH_K)
    norm = np.nan_to_num(np.clip(norm, -1.0, 1.0), nan=0.0)

    pos = np.clip(norm, 0.0, 1.0)
    neg = np.clip(-norm, 0.0, 1.0)

    r = np.rint(255.0 * (0.10 + 0.90 * pos)).astype(np.uint8)
    g = np.rint(255.0 * (0.10 + 0.65 * pos + 0.55 * neg)).astype(np.uint8)
    b = np.rint(255.0 * (0.12 + 0.88 * neg)).astype(np.uint8)

    rgb = np.flipud(np.stack([r, g, b], axis=-1))
    buf = io.BytesIO()
    Image.fromarray(rgb, mode="RGB").save(buf, format="WEBP", lossless=True)
    return buf.getvalue()


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[3]
    fits_files = sorted((root / ".planetes-cache").rglob("*.fits"))
    if not fits_files:
        fits_files = sorted((root / "pipeline" / "tests" / "data").glob("*.fits"))

    print(f"Found {len(fits_files)} FITS files for D2.3 stacking check.")
    if fits_files:
        with fits.open(fits_files[0]) as hdul:
            w0 = WCS(hdul["IMAGE"].header)
            ra_c, dec_c = w0.pixel_to_world_values(11, 11)

        ref_wcs, _ = frames.make_reference_grid(float(ra_c), float(dec_c), size_pixels=32)
        by_det: dict[int, CoaddResult] = {}

        for f in fits_files[:6]:
            with fits.open(f) as hdul:
                det = int(
                    hdul["IMAGE"].header.get("DETECTOR")
                    or hdul["PRIMARY"].header.get("DETECTOR")
                    or 3
                )
            img, var, good = prepare_reprojected_variance(f.read_bytes(), ref_wcs, grid_shape=(32, 32))
            coadd = inverse_variance_stack([img], [var], [good], detector=det)
            by_det[det] = sum_coadds([by_det[det], coadd]) if det in by_det else coadd

        print(f"Stacked detectors: {sorted(by_det.keys())}")
        for d, c in sorted(by_det.items()):
            print(f"  D{d}: n_frames={c.n_frames}, median_var={np.nanmedian(c.variance):.4f}")

        if len(by_det) >= 2:
            dets = sorted(by_det.keys())
            diff = difference_coadds(by_det[dets[0]], by_det[dets[-1]])
            diff_webp = difference_to_webp(diff)
            print(
                f"Difference (D{dets[-1]} - D{dets[0]}): "
                f"min={np.nanmin(diff.image):.2f}, max={np.nanmax(diff.image):.2f}, "
                f"webp_bytes={len(diff_webp)}"
            )

        rgb = colour_composite(by_det)
        rgb_webp = colour_to_webp(rgb)
        print(f"RGB composite shape={rgb.shape}, dtype={rgb.dtype}, max={rgb.max()}, webp_bytes={len(rgb_webp)}")