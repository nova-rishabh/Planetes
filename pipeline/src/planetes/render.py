"""
Planetes rendering (D2.2, Tirth; review fixes by Rishabh).

One shared asinh stretch for all frames of a time-lapse (so the movie does not flicker), WebP frames with
north at the top, and a transparent flag overlay coloured per docs/09 §3.
"""

from __future__ import annotations

import io
from collections.abc import Sequence

import numpy as np
from PIL import Image

from planetes.contracts import Stretch
from planetes.frames import FlagMasks

STRETCH_PERCENTILES = (1.0, 99.5)
# asinh softening: larger = more contrast for faint sources.
ASINH_K = 10.0

# Flag overlay colours from docs/09 §3 (they sit on the dark frame, not on the page), RGBA.
FLAG_RGBA_SATURATED = (0xF4, 0xA6, 0x2A, 200)
FLAG_RGBA_COSMIC = (0xF0, 0x47, 0x70, 200)
FLAG_RGBA_OTHER = (0xFF, 0xD1, 0x67, 160)


def shared_stretch(images: Sequence[np.ndarray]) -> Stretch | None:
    """One asinh stretch from the pooled finite pixels of every frame (MJy/sr, zodi-subtracted).
    None if no frame has data."""
    finite = [im[np.isfinite(im)] for im in images]
    pooled = np.concatenate(finite) if finite else np.array([])
    if pooled.size == 0:
        return None
    lo, hi = (float(v) for v in np.percentile(pooled, STRETCH_PERCENTILES))
    if hi <= lo:
        hi = lo + 1e-6
    return Stretch(method="asinh", lo=lo, hi=hi, unit="MJy/sr")


def to_webp(image: np.ndarray, stretch: Stretch, saturated: np.ndarray | None = None) -> bytes:
    """8-bit lossless WebP, north up (FITS row 0 is south, image row 0 is the top). No-data pixels are black,
    except saturated ones (a bright star's core has no valid value): those are drawn white, as the sky is there
    brighter than the detector can measure. The flag overlay marks them."""
    x = (image - stretch.lo) / (stretch.hi - stretch.lo)
    v = np.arcsinh(ASINH_K * np.clip(x, 0.0, None)) / np.arcsinh(ASINH_K)
    v = np.nan_to_num(v, nan=0.0)
    if saturated is not None:
        v = np.where(saturated & ~np.isfinite(image), 1.0, v)
    px = (np.clip(v, 0.0, 1.0) * 255.0).astype(np.uint8)
    buf = io.BytesIO()
    Image.fromarray(np.flipud(px)).save(buf, format="WEBP", lossless=True)
    return buf.getvalue()


def render_flag_mask_png(masks: FlagMasks) -> bytes:
    """Transparent PNG, north up: saturated / cosmic ray / other flagged pixels in their docs/09 colours."""
    ny, nx = masks.saturated.shape
    rgba = np.zeros((ny, nx, 4), dtype=np.uint8)
    rgba[masks.other] = FLAG_RGBA_OTHER
    rgba[masks.cosmic] = FLAG_RGBA_COSMIC
    rgba[masks.saturated] = FLAG_RGBA_SATURATED  # drawn last: saturation matters most
    buf = io.BytesIO()
    Image.fromarray(np.flipud(rgba), mode="RGBA").save(buf, format="PNG")
    return buf.getvalue()
