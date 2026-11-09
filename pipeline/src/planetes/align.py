"""
Planetes Alignment & Frame Generation Module (D2.2)
Projects raw FITS cutouts onto a common North-up tangent grid,
computes 0-based target_xy coordinates, and exports web-ready .webp images.
"""

from __future__ import annotations

import io
from datetime import datetime, timezone
from typing import Any

import numpy as np
from astropy.io import fits
from astropy.wcs import WCS
from PIL import Image
from scipy.ndimage import map_coordinates

from planetes.contracts import (
    Detector,
    Frame,
    Grid,
    Naxi,
    Stretch,
    TargetXy,
)

# Standard SPHEREx pixel scale is ~6.2 arcsec (~0.001722 deg)
SPHEREX_PIXEL_SCALE_DEG = 6.2 / 3600.0


def make_reference_grid(
    ra_center: float,
    dec_center: float,
    size_pixels: int = 64,
    pixel_scale_deg: float = SPHEREX_PIXEL_SCALE_DEG,
) -> tuple[WCS, Grid]:
    """
    Construct a common North-up TAN reference WCS and the matching Grid contract model.

    In FITS convention:
    - crpix is 1-based center.
    - cdelt is [-pixel_scale, pixel_scale] for standard North-up (East-left).
    """
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
    """
    Calculate target position on the reference grid.

    Returns a 0-based pixel index [x, y] with +y pointing North.
    """
    x, y = ref_wcs.world_to_pixel_values(target_ra, target_dec)
    return TargetXy([float(x), float(y)])


def reproject_to_grid(
    data: np.ndarray,
    input_wcs: WCS,
    ref_wcs: WCS,
    shape_out: tuple[int, int] = (64, 64),
) -> np.ndarray:
    """
    Resample input image data onto ref_wcs grid using Astropy WCS and SciPy interpolation.
    """
    ny, nx = shape_out
    y_idx, x_idx = np.indices((ny, nx))

    # Convert output pixel grid coordinates to celestial (RA, Dec)
    ra_grid, dec_grid = ref_wcs.pixel_to_world_values(x_idx, y_idx)

    # Convert celestial coordinates back to input image pixel space
    orig_x, orig_y = input_wcs.world_to_pixel_values(ra_grid, dec_grid)

    # Interpolate input data onto the new coordinate grid
    coords = np.array([orig_y.ravel(), orig_x.ravel()])
    resampled = map_coordinates(
        data,
        coords,
        order=1,
        mode="constant",
        cval=np.nan,
    )
    return resampled.reshape(shape_out)


def normalize_to_webp(
    image_data: np.ndarray,
    stretch_lo: float | None = None,
    stretch_hi: float | None = None,
) -> tuple[bytes, Stretch]:
    """
    Scale a 2D float image array to 8-bit using a percentile stretch
    and encode it into .webp format.
    """
    finite_vals = image_data[np.isfinite(image_data)]
    if len(finite_vals) == 0:
        norm_img = np.zeros(image_data.shape, dtype=np.uint8)
        lo, hi = 0.0, 1.0
    else:
        lo = stretch_lo if stretch_lo is not None else float(np.percentile(finite_vals, 2))
        hi = stretch_hi if stretch_hi is not None else float(np.percentile(finite_vals, 98))
        if hi <= lo:
            hi = lo + 1e-5

        scaled = (image_data - lo) / (hi - lo)
        clipped = np.clip(scaled, 0.0, 1.0)
        clipped = np.nan_to_num(clipped, nan=0.0)
        norm_img = (clipped * 255.0).astype(np.uint8)

    # In FITS arrays, row 0 is the bottom (South). Invert the y-axis for standard image display
    pil_image = Image.fromarray(np.flipud(norm_img))
    buffer = io.BytesIO()
    pil_image.save(buffer, format="WEBP", quality=90)

    stretch_meta = Stretch(method="linear", lo=lo, hi=hi, unit="MJy/sr")
    return buffer.getvalue(), stretch_meta


def align_single_frame(
    fits_bytes: bytes,
    frame_row: dict[str, Any],
    ref_wcs: WCS,
    grid_shape: tuple[int, int] = (64, 64),
    target_coord: tuple[float, float] | None = None,
) -> tuple[Frame, bytes]:
    """
    Reproject one raw FITS cutout onto the reference WCS grid
    and produce the web-ready image and Frame metadata.
    """
    with fits.open(io.BytesIO(fits_bytes)) as hdul:
        data = hdul[0].data if hdul[0].data is not None else hdul[1].data
        header = hdul[0].header if hdul[0].data is not None else hdul[1].header
        input_wcs = WCS(header)

    reprojected_data = reproject_to_grid(data, input_wcs, ref_wcs, shape_out=grid_shape)

    # Calculate flagged fraction and center saturation
    total_pixels = reprojected_data.size
    nan_count = np.sum(~np.isfinite(reprojected_data))
    flagged_fraction = float(nan_count / total_pixels) if total_pixels > 0 else 0.0

    cy, cx = grid_shape[0] // 2, grid_shape[1] // 2
    center_patch = reprojected_data[max(0, cy - 2) : cy + 3, max(0, cx - 2) : cx + 3]
    saturated_center = bool(np.any(~np.isfinite(center_patch)))

    # Compute target_xy (0-based pixel, +y North)
    target_xy = None
    if target_coord is not None:
        target_xy = compute_target_xy(target_coord[0], target_coord[1], ref_wcs)

    # Encode to webp
    webp_bytes, _ = normalize_to_webp(reprojected_data)

    frame_id = frame_row["frame_id"]
    obs_id = frame_row.get("obs_id")
    mjd_val = float(frame_row["mjd"]) if frame_row.get("mjd") is not None else None

    # UTC timestamp from MJD (MJD 0 = Nov 17, 1858)
    utc_val = None
    if mjd_val is not None:
        unix_ts = (mjd_val - 40587.0) * 86400.0
        utc_val = datetime.fromtimestamp(unix_ts, tz=timezone.utc)

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
        wavelength_um=None,
        bandwidth_um=None,
        image_url=f"/api/frames/{frame_id}.webp",
        flags_url=None,
        flagged_frac=min(1.0, max(0.0, flagged_fraction)),
        saturated_near_center=saturated_center,
        target_xy=target_xy,
        notes=[],
    )

    return frame, webp_bytes