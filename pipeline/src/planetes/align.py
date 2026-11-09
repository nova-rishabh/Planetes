"""
Planetes Alignment compatibility module.
Re-exports functionality from frames.py and render.py.
"""

from __future__ import annotations

from planetes.frames import (
    SPHEREX_PIXEL_SCALE_DEG,
    compute_target_xy,
    extract_wavelength,
    make_reference_grid,
    process_frame,
    reproject_to_grid,
)
from planetes.render import normalize_to_webp, render_flag_mask_png


def align_single_frame(fits_bytes, frame_row, ref_wcs, grid_shape=(64, 64), target_coord=None):
    frame, webp_bytes, _ = process_frame(
        fits_bytes=fits_bytes,
        frame_row=frame_row,
        ref_wcs=ref_wcs,
        grid_shape=grid_shape,
        target_coord=target_coord,
    )
    return frame, webp_bytes