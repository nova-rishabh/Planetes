"""
Planetes Frame Processing Module (D2.2)
Handles IMAGE - ZODI subtraction, spectral WCS wavelength extraction,
astrometric North-up TAN reprojection, and generation of Frame contract objects.
"""

from __future__ import annotations

import io
import warnings
from datetime import UTC, datetime
from typing import Any

import numpy as np
from astropy.io import fits
from astropy.wcs import WCS, FITSFixedWarning
from scipy.ndimage import map_coordinates

from planetes.contracts import Detector, Frame, Grid, Naxi, TargetXy
from planetes.render import normalize_to_webp, render_flag_mask_png

SPHEREX_PIXEL_SCALE_DEG = 6.2 / 3600.0


def make_reference_grid(
    ra_center: float,
    dec_center: float,
    size_pixels: int = 64,
    pixel_scale_deg: float = SPHEREX_PIXEL_SCALE_DEG,
) -> tuple[WCS, Grid]:
    """Construct a common North-up TAN reference WCS and the matching Grid contract model."""
    center_pix_1based = (size_pixels + 1.0) / 2.0

    wcs = WCS(naxis=2)
    wcs.wcs.crval = [ra_center, dec_center]
    wcs.wcs.crpix = [center_pix_1based, center_pix_1based]
    wcs.wcs.cdelt = [-pixel_scale_deg, pixel_scale_deg]
    wcs.wcs.ctype = ["RA---TAN", "DEC--TAN"]

    grid = Grid(
        projection="TAN",
        crval_deg=[float(ra_center), float(dec_center)],
        crpix=[float(center_pix_1based), float(center_pix_1based)],
        cdelt_deg=float(pixel_scale_deg),
        naxis=[Naxi(size_pixels), Naxi(size_pixels)],
        north_up=True,
    )
    return wcs, grid


def compute_target_xy(target_ra: float, target_dec: float, ref_wcs: WCS) -> TargetXy:
    """Calculate target position on reference grid (0-based pixel index, +y North)."""
    x, y = ref_wcs.world_to_pixel_values(target_ra, target_dec)
    return TargetXy([float(x), float(y)])


def reproject_to_grid(
    data: np.ndarray,
    input_wcs: WCS,
    ref_wcs: WCS,
    shape_out: tuple[int, int] = (64, 64),
    order: int = 1,
    cval: float = np.nan,
) -> np.ndarray:
    """Resample 2D array onto ref_wcs grid using SciPy interpolation."""
    ny, nx = shape_out
    y_idx, x_idx = np.indices((ny, nx))
    ra_grid, dec_grid = ref_wcs.pixel_to_world_values(x_idx, y_idx)
    orig_x, orig_y = input_wcs.world_to_pixel_values(ra_grid, dec_grid)

    coords = np.array([orig_y.ravel(), orig_x.ravel()])
    resampled = map_coordinates(
        data,
        coords,
        order=order,
        mode="constant",
        cval=cval,
    )
    return resampled.reshape(shape_out)


def extract_wavelength(hdul: fits.HDUList) -> tuple[float | None, float | None]:
    """Extract central wavelength and bandwidth (microns) via spectral WCS key 'W'."""
    image_hdu = hdul["IMAGE"] if "IMAGE" in hdul else hdul[0]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=FITSFixedWarning)
        try:
            w_wcs = WCS(image_hdu.header, hdul, key="W")
            cy = image_hdu.data.shape[0] // 2
            cx = image_hdu.data.shape[1] // 2
            wave_val, band_val = w_wcs.pixel_to_world_values(cx, cy)
            wave = float(np.squeeze(wave_val))
            band = float(np.squeeze(band_val))
            return wave, band
        except Exception:
            return None, None


def process_frame(
    fits_bytes: bytes,
    frame_row: dict[str, Any],
    ref_wcs: WCS,
    grid_shape: tuple[int, int] = (64, 64),
    target_coord: tuple[float, float] | None = None,
    subtract_zodi: bool = True,
) -> tuple[Frame, bytes, bytes]:
    """
    Process a raw SPHEREx FITS cutout:
    1. IMAGE - ZODI background subtraction
    2. Extract central wavelength and bandwidth
    3. Reproject science and flag planes onto North-up reference grid
    4. Generate .webp image and _flags.png mask
    """
    with fits.open(io.BytesIO(fits_bytes)) as hdul:
        if "IMAGE" in hdul:
            image_data = hdul["IMAGE"].data.astype(np.float32)
            header = hdul["IMAGE"].header
        else:
            image_data = hdul[0].data.astype(np.float32)
            header = hdul[0].header

        # IMAGE - ZODI subtraction
        if subtract_zodi and "ZODI" in hdul and hdul["ZODI"].data is not None:
            image_data = image_data - hdul["ZODI"].data.astype(np.float32)

        # Quality flags plane
        flags_data = (
            hdul["FLAGS"].data.astype(np.float32)
            if "FLAGS" in hdul and hdul["FLAGS"].data is not None
            else np.zeros_like(image_data)
        )

        wavelength_um, bandwidth_um = extract_wavelength(hdul)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=FITSFixedWarning)
            input_wcs = WCS(header)

    # Reproject science flux (bilinear) and flags (nearest neighbor)
    reproj_image = reproject_to_grid(image_data, input_wcs, ref_wcs, shape_out=grid_shape, order=1, cval=np.nan)
    reproj_flags = reproject_to_grid(flags_data, input_wcs, ref_wcs, shape_out=grid_shape, order=0, cval=1.0)

    # Compute flag stats and saturation near center
    total_pixels = reproj_image.size
    nan_count = np.sum(~np.isfinite(reproj_image) | (reproj_flags != 0))
    flagged_frac = float(nan_count / total_pixels) if total_pixels > 0 else 0.0

    cy, cx = grid_shape[0] // 2, grid_shape[1] // 2
    center_patch = reproj_image[max(0, cy - 2) : cy + 3, max(0, cx - 2) : cx + 3]
    saturated_center = bool(np.any(~np.isfinite(center_patch)))

    # Compute 0-based target coordinates (+y North)
    target_xy = None
    if target_coord is not None:
        target_xy = compute_target_xy(target_coord[0], target_coord[1], ref_wcs)

    # Render web artifacts
    webp_bytes, _ = normalize_to_webp(reproj_image)
    flags_png_bytes = render_flag_mask_png(reproj_flags)

    frame_id = frame_row["frame_id"]
    obs_id = frame_row.get("obs_id")
    mjd_val = float(frame_row["mjd"]) if frame_row.get("mjd") is not None else None

    utc_val = None
    if mjd_val is not None:
        unix_ts = (mjd_val - 40587.0) * 86400.0
        utc_val = datetime.fromtimestamp(unix_ts, tz=UTC)

    frame = Frame(
        id=frame_id,
        kind="exposure",
        obs_id=obs_id,
        members=[obs_id] if obs_id else [],
        release=frame_row.get("release", "QR3"),
        epoch_index=int(frame_row.get("epoch_group", 0)),
        mjd=mjd_val,
        utc=utc_val,
        detector=Detector(int(frame_row["detector"])),
        wavelength_um=wavelength_um,
        bandwidth_um=bandwidth_um,
        image_url=f"/api/frames/{frame_id}.webp",
        flags_url=f"/api/frames/{frame_id}_flags.png",
        flagged_frac=min(1.0, max(0.0, flagged_frac)),
        saturated_near_center=saturated_center,
        target_xy=target_xy,
        notes=[],
    )

    return frame, webp_bytes, flags_png_bytes
