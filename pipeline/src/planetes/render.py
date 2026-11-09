"""
Planetes Rendering Module (D2.2)
Handles stretch scaling, 8-bit quantization, and exporting .webp and .png flag masks.
"""

from __future__ import annotations

import io

import numpy as np
from PIL import Image

from planetes.contracts import Stretch


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

    # Invert y-axis: FITS row 0 is bottom (South), web image row 0 is top (North)
    pil_image = Image.fromarray(np.flipud(norm_img))
    buffer = io.BytesIO()
    pil_image.save(buffer, format="WEBP", quality=90)

    stretch_meta = Stretch(method="linear", lo=lo, hi=hi, unit="MJy/sr")
    return buffer.getvalue(), stretch_meta


def render_flag_mask_png(flags_data: np.ndarray) -> bytes:
    """
    Convert a 2D integer flag array into an 8-bit RGBA PNG mask.
    Clean pixels (0) are completely transparent; flagged/corrupted pixels are highlighted red.
    """
    ny, nx = flags_data.shape
    rgba = np.zeros((ny, nx, 4), dtype=np.uint8)

    bad_mask = (flags_data != 0) | (~np.isfinite(flags_data))
    # Red with 60% opacity for flagged/corrupted pixels
    rgba[bad_mask] = [230, 50, 50, 150]

    pil_image = Image.fromarray(np.flipud(rgba), mode="RGBA")
    buffer = io.BytesIO()
    pil_image.save(buffer, format="PNG")
    return buffer.getvalue()
