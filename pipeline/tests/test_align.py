import io

import numpy as np
from astropy.io import fits

from planetes.align import (
    align_single_frame,
    compute_target_xy,
    make_reference_grid,
    normalize_to_webp,
)


def test_reference_grid_and_target_xy():
    """Verify Grid satisfies 0-based indexing and North-up convention."""
    ra = 269.4461
    dec = 4.7703
    size = 64

    ref_wcs, grid = make_reference_grid(ra, dec, size_pixels=size)

    assert grid.north_up is True
    assert grid.projection == "TAN"
    assert grid.crpix == [32.5, 32.5]
    assert len(grid.naxis) == 2
    assert grid.naxis[0].root == 64

    # Target pixel must match the center in 0-based coordinates
    target_xy = compute_target_xy(ra, dec, ref_wcs)
    coords = target_xy.root

    # Center of 64 pixels in 0-based indexing is 31.5
    assert abs(coords[0] - 31.5) < 1e-4
    assert abs(coords[1] - 31.5) < 1e-4

    # Moving North (+Dec) must increase y
    north_target = compute_target_xy(ra, dec + 0.01, ref_wcs)
    assert north_target.root[1] > coords[1]


def test_normalize_to_webp():
    """Ensure image data converts to valid WEBP bytes without crashing."""
    sample_data = np.random.normal(loc=10.0, scale=2.0, size=(64, 64)).astype(np.float32)
    webp_bytes, stretch = normalize_to_webp(sample_data)

    assert len(webp_bytes) > 0
    assert webp_bytes[:4] == b"RIFF"  # WEBP container magic header
    assert stretch.method == "linear"
    assert stretch.hi > stretch.lo


def test_align_single_frame_synthetic():
    """Verify synthetic FITS cutouts align and export valid Frame objects."""
    ra_target, dec_target = 269.4461, 4.7703
    ref_wcs, _ = make_reference_grid(ra_target, dec_target, size_pixels=64)

    # Build a minimal synthetic FITS cutout in memory
    hdr = ref_wcs.to_header()
    hdr["NAXIS"] = 2
    hdr["NAXIS1"] = 64
    hdr["NAXIS2"] = 64
    synthetic_pixels = np.ones((64, 64), dtype=np.float32) * 5.0
    hdu = fits.PrimaryHDU(data=synthetic_pixels, header=hdr)
    fits_buf = io.BytesIO()
    hdu.writeto(fits_buf)
    raw_fits_bytes = fits_buf.getvalue()

    frame_row = {
        "frame_id": "f_1234567890ab",
        "obs_id": "SPHEREx_Test_001",
        "release": "QR3",
        "detector": 1,
        "mjd": 60000.5,
        "epoch_group": 0,
    }

    frame, webp_bytes = align_single_frame(
        fits_bytes=raw_fits_bytes,
        frame_row=frame_row,
        ref_wcs=ref_wcs,
        grid_shape=(64, 64),
        target_coord=(ra_target, dec_target),
    )

    assert frame.id == "f_1234567890ab"
    assert frame.kind == "exposure"
    assert frame.detector.root == 1
    assert frame.target_xy is not None
    assert abs(frame.target_xy.root[0] - 31.5) < 1e-4
    assert len(webp_bytes) > 0
    assert webp_bytes[:4] == b"RIFF"
