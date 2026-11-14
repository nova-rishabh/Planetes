"""
Planetes frame processing (D2.2, Tirth; review fixes by Rishabh).

One SPHEREx cutout -> zodi-subtracted image and integer flags on a shared north-up TAN grid, plus a
`Frame` contract object. Rendering (shared stretch, WebP, flag overlay) lives in render.py.
"""

from __future__ import annotations

import io
import warnings
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import numpy as np
from astropy.io import fits
from astropy.wcs import WCS, FITSFixedWarning
from scipy.ndimage import map_coordinates

from planetes.contracts import Detector, FlagLegendItem, Frame, Grid, Naxi, TargetXy

SPHEREX_PIXEL_SCALE_DEG = 6.2 / 3600.0

# Flag categories by name (bit numbers are always read from the header, never assumed).
# SOURCE marks pixels on a detected source and FULLSAMPLE a readout mode: information, not defects.
SATURATED_FLAGS = frozenset({"OVERFLOW", "NONLINEAR"})
COSMIC_FLAGS = frozenset({"TRANSIENT", "SNOWBALL"})
INFORMATIONAL_FLAGS = frozenset({"SOURCE", "FULLSAMPLE"})
# Pixels around target_xy checked for saturation.
SATURATION_RADIUS_PX = 2.0
# Pixel value in reprojected flags for "outside this exposure" (real flags are >= 0).
OUTSIDE = -1

REQUIRED_ROW_KEYS = ("frame_id", "obs_id", "release", "detector", "mjd", "epoch_group")


def make_reference_grid(
    ra_center: float,
    dec_center: float,
    size_pixels: int = 64,
    pixel_scale_deg: float = SPHEREX_PIXEL_SCALE_DEG,
) -> tuple[WCS, Grid]:
    """Common north-up TAN reference WCS and the matching Grid contract model."""
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
    """Target position on the reference grid (0-based pixel, +y north)."""
    x, y = ref_wcs.world_to_pixel_values(target_ra, target_dec)
    return TargetXy([float(x), float(y)])


def _source_coords(input_wcs: WCS, ref_wcs: WCS, shape_out: tuple[int, int]) -> tuple[np.ndarray, np.ndarray]:
    """For every output pixel, the (x, y) position in the input image (0-based)."""
    ny, nx = shape_out
    y_idx, x_idx = np.indices((ny, nx))
    ra_grid, dec_grid = ref_wcs.pixel_to_world_values(x_idx, y_idx)
    return input_wcs.world_to_pixel_values(ra_grid, dec_grid)


def reproject_to_grid(
    data: np.ndarray, input_wcs: WCS, ref_wcs: WCS, shape_out: tuple[int, int] = (64, 64)
) -> np.ndarray:
    """Bilinear resample of a float image onto the reference grid; NaN outside the input."""
    orig_x, orig_y = _source_coords(input_wcs, ref_wcs, shape_out)
    coords = np.array([orig_y.ravel(), orig_x.ravel()])
    out = map_coordinates(data.astype(np.float64), coords, order=1, mode="constant", cval=np.nan)
    return out.reshape(shape_out)


def reproject_flags(
    flags: np.ndarray, input_wcs: WCS, ref_wcs: WCS, shape_out: tuple[int, int] = (64, 64)
) -> np.ndarray:
    """Nearest-pixel lookup on the integer FLAGS array (never interpolated, never cast to float).
    Pixels outside the input get OUTSIDE."""
    orig_x, orig_y = _source_coords(input_wcs, ref_wcs, shape_out)
    ix = np.rint(orig_x).astype(np.int64)
    iy = np.rint(orig_y).astype(np.int64)
    ny_in, nx_in = flags.shape
    inside = (ix >= 0) & (ix < nx_in) & (iy >= 0) & (iy < ny_in)
    out = np.full(shape_out, OUTSIDE, dtype=np.int64)
    out[inside] = flags.astype(np.int64)[iy[inside], ix[inside]]
    return out


def flag_bits(header: fits.Header) -> dict[str, int]:
    """FLAGS bit numbers by name, read from the FLAGS header. Two layouts exist (checked):
    QR2 (VERSION 6.x): MP_OVERFLOW = 1 (the value is the bit number).
    QR3 (VERSION 7.x): MSKN0001 = 'OVERFLOW', MSKM0001 = 2 (the value is the bit mask), MSKD0001 = description."""
    bits = {k[3:]: int(v) for k, v in header.items() if k.startswith("MP_")}
    for key, name in header.items():
        if key.startswith("MSKN"):
            mask = header.get("MSKM" + key[4:])
            if isinstance(mask, int) and mask > 0 and mask & (mask - 1) == 0:
                bits[str(name).strip()] = mask.bit_length() - 1
    return bits


def flag_descriptions(header: fits.Header) -> dict[str, str]:
    """QR3 only: NASA's one-line description of each flag (MSKDnnnn), by name."""
    out: dict[str, str] = {}
    for key, name in header.items():
        if key.startswith("MSKN"):
            desc = header.get("MSKD" + key[4:])
            if isinstance(desc, str) and desc.strip():
                out[str(name).strip()] = desc.strip()
    return out


def flag_legend(bits: dict[str, int], descriptions: dict[str, str] | None = None) -> list[FlagLegendItem]:
    """Legend for TimelapseResult.flag_legend. `plain` is NASA's description where the file has one (QR3);
    simpler wording for the public comes from D4.1 (Shimaya)."""
    desc = descriptions or {}
    return [FlagLegendItem(bit=b, name=n, plain=desc.get(n)) for n, b in sorted(bits.items(), key=lambda kv: kv[1])]


@dataclass
class FlagMasks:
    saturated: np.ndarray
    cosmic: np.ndarray
    other: np.ndarray
    outside: np.ndarray

    @property
    def bad(self) -> np.ndarray:
        return self.saturated | self.cosmic | self.other


def classify_flags(flags: np.ndarray, bits: dict[str, int]) -> FlagMasks:
    """Split reprojected flags into saturated / cosmic-ray / other-bad masks. Informational bits are ignored."""
    if not bits:
        raise ValueError("No flag definitions (MP_* or MSKN*) in the FLAGS header; cannot interpret FLAGS")

    def mask_of(names: frozenset[str] | set[str]) -> int:
        return sum(1 << b for n, b in bits.items() if n in names)

    outside = flags == OUTSIDE
    f = np.where(outside, 0, flags)
    other_names = set(bits) - SATURATED_FLAGS - COSMIC_FLAGS - INFORMATIONAL_FLAGS
    return FlagMasks(
        saturated=(f & mask_of(SATURATED_FLAGS)) != 0,
        cosmic=(f & mask_of(COSMIC_FLAGS)) != 0,
        other=(f & mask_of(other_names)) != 0,
        outside=outside,
    )


def extract_wavelength(hdul: fits.HDUList) -> tuple[float | None, float | None]:
    """Central wavelength and bandwidth (µm) at the cutout centre via the 'W' spectral WCS.
    None if the file has no usable spectral WCS."""
    image_hdu = hdul["IMAGE"]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=FITSFixedWarning)
        try:
            w_wcs = WCS(image_hdu.header, hdul, key="W")
            w_wcs.sip = None  # AGENTS gotcha: SIP belongs to the sky WCS, not the spectral one
            cy, cx = image_hdu.data.shape[0] // 2, image_hdu.data.shape[1] // 2
            wave_val, band_val = w_wcs.pixel_to_world_values(cx, cy)
            return float(np.squeeze(wave_val)), float(np.squeeze(band_val))
        except (KeyError, ValueError, IndexError):
            return None, None


@dataclass
class PreparedFrame:
    """A frame on the shared grid, before the shared stretch is applied (render.py)."""

    frame: Frame
    image: np.ndarray
    masks: FlagMasks
    bits: dict[str, int]
    descriptions: dict[str, str]


def _require_row(row: dict[str, Any]) -> None:
    missing = [k for k in REQUIRED_ROW_KEYS if row.get(k) is None]
    if missing:
        raise ValueError(f"frame row is missing {missing}")


def mjd_to_utc(mjd: float) -> datetime:
    """MJD (TIMESYS UTC in SPHEREx headers) to a UTC datetime."""
    return datetime.fromtimestamp((mjd - 40587.0) * 86400.0, tz=UTC)


def prepare_frame(
    fits_bytes: bytes,
    frame_row: dict[str, Any],
    ref_wcs: WCS,
    grid_shape: tuple[int, int] = (64, 64),
    target_coord: tuple[float, float] | None = None,
) -> PreparedFrame:
    """Process one SPHEREx cutout: IMAGE - ZODI, wavelength, reprojection of image and flags, Frame object.

    frame_row needs frame_id, obs_id, release, detector, mjd, epoch_group (from access.find_frames).
    target_coord is the target's (ra, dec) at this frame's date (already propagated for proper motion).
    """
    _require_row(frame_row)
    with fits.open(io.BytesIO(fits_bytes)) as hdul:
        header = hdul["IMAGE"].header
        image = hdul["IMAGE"].data.astype(np.float64) - hdul["ZODI"].data.astype(np.float64)
        flags = np.asarray(hdul["FLAGS"].data)
        bits = flag_bits(hdul["FLAGS"].header)
        descriptions = flag_descriptions(hdul["FLAGS"].header)
        wavelength_um, bandwidth_um = extract_wavelength(hdul)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=FITSFixedWarning)
            input_wcs = WCS(header)

    reproj_image = reproject_to_grid(image, input_wcs, ref_wcs, grid_shape)
    masks = classify_flags(reproject_flags(flags, input_wcs, ref_wcs, grid_shape), bits)
    # Bilinear resampling spreads each saturated no-value pixel to its neighbours; resample the raw saturation
    # mask the same way so every output pixel it touched is marked saturated too.
    sat_raw = classify_flags(flags.astype(np.int64), bits).saturated.astype(np.float64)
    masks.saturated |= reproject_to_grid(sat_raw, input_wcs, ref_wcs, grid_shape) > 0

    covered = ~masks.outside
    n_covered = int(covered.sum())
    bad = (masks.bad | ~np.isfinite(reproj_image)) & covered
    flagged_frac = float(bad.sum() / n_covered) if n_covered else None

    notes: list[str] = []
    target_xy = None
    saturated: bool | None = None
    if target_coord is not None:
        target_xy = compute_target_xy(target_coord[0], target_coord[1], ref_wcs)
        tx, ty = target_xy.root
        yy, xx = np.indices(grid_shape)
        near = (xx - tx) ** 2 + (yy - ty) ** 2 <= SATURATION_RADIUS_PX**2
        if near.any() and covered[near].any():
            saturated = bool(masks.saturated[near].any())
        else:
            notes.append("Target is outside this exposure")
    if wavelength_um is None:
        notes.append("Wavelength could not be read from the spectral WCS")

    fid = frame_row["frame_id"]
    obs_id = str(frame_row["obs_id"])
    mjd = float(frame_row["mjd"])
    frame = Frame(
        id=fid,
        kind="exposure",
        obs_id=obs_id,
        members=[obs_id],
        release=str(frame_row["release"]),
        epoch_index=int(frame_row["epoch_group"]),
        mjd=mjd,
        utc=mjd_to_utc(mjd),
        detector=Detector(int(frame_row["detector"])),
        wavelength_um=wavelength_um,
        bandwidth_um=bandwidth_um,
        image_url=f"/api/frames/{fid}.webp",
        flags_url=f"/api/frames/{fid}/flags.png",
        flagged_frac=flagged_frac,
        saturated_near_center=saturated,
        target_xy=target_xy,
        notes=notes,
    )
    return PreparedFrame(frame=frame, image=reproj_image, masks=masks, bits=bits, descriptions=descriptions)
