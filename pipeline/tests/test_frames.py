"""D2.2 tests on a real SPHEREx cutout (tests/data: Barnard's Star, D3, QR2 2025W33_2C_0321_1, from IRSA,
cropped to 0.04 deg with the PSF and VARIANCE extensions removed). No network."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from planetes.frames import (
    OUTSIDE,
    classify_flags,
    compute_target_xy,
    flag_bits,
    flag_descriptions,
    make_reference_grid,
    prepare_frame,
)
from planetes.render import render_flag_mask_png, shared_stretch, to_webp

FIXTURE = Path(__file__).parent / "data" / "barnard_d3_qr2_2025W33_2C_0321_1.fits"
OBS_ID = "ivo://irsa.ipac/spherex_qr2?2025W33_2C_0321_1/D3"
ROW = {
    "frame_id": "f_0123456789ab",
    "obs_id": OBS_ID,
    "release": "QR2",
    "detector": 3,
    "mjd": 60902.864715,
    "epoch_group": 0,
}
RA, DEC = 269.4461, 4.7703


@pytest.fixture(scope="module")
def prepared():
    ref_wcs, _ = make_reference_grid(RA, DEC, size_pixels=32)
    return prepare_frame(FIXTURE.read_bytes(), ROW, ref_wcs, (32, 32), target_coord=(RA, DEC))


def test_grid_is_north_up_and_zero_based():
    ref_wcs, grid = make_reference_grid(RA, DEC, size_pixels=64)
    assert grid.crpix == [32.5, 32.5]
    x, y = compute_target_xy(RA, DEC, ref_wcs).root
    assert abs(x - 31.5) < 1e-6 and abs(y - 31.5) < 1e-6
    assert compute_target_xy(RA, DEC + 0.01, ref_wcs).root[1] > y


def test_flag_names_come_from_the_header():
    from astropy.io import fits

    with fits.open(FIXTURE) as h:
        bits = flag_bits(h["FLAGS"].header)
    assert bits["SOURCE"] == 21 and bits["OVERFLOW"] == 1 and bits["TRANSIENT"] == 0


def test_qr3_mask_keys_are_read():
    from astropy.io import fits

    h = fits.Header()
    h["MSKN0021"], h["MSKM0021"], h["MSKD0021"] = "SOURCE", 2097152, "Pixel mapped to a known source"
    h["MSKN0001"], h["MSKM0001"] = "OVERFLOW", 2
    assert flag_bits(h) == {"SOURCE": 21, "OVERFLOW": 1}
    assert flag_descriptions(h) == {"SOURCE": "Pixel mapped to a known source"}


def test_source_bit_is_not_counted_as_bad():
    bits = {"OVERFLOW": 1, "TRANSIENT": 0, "HOT": 10, "SOURCE": 21}
    flags = np.array([[1 << 21, (1 << 21) | (1 << 1)], [1 << 0, OUTSIDE]])
    m = classify_flags(flags, bits)
    assert m.bad.tolist() == [[False, True], [True, False]]
    assert m.saturated[0, 1] and m.cosmic[1, 0] and m.outside[1, 1]
    with pytest.raises(ValueError):
        classify_flags(flags, {})


def test_real_frame_contract_fields(prepared):
    f = prepared.frame
    assert f.obs_id == OBS_ID and f.release == "QR2" and f.detector.root == 3
    assert f.flags_url == "/api/frames/f_0123456789ab/flags.png"
    assert 1.6 < f.wavelength_um < 2.5  # D3 covers 1.64-2.42 µm
    assert f.flagged_frac is not None and f.flagged_frac < 0.5  # SOURCE pixels are not "flagged"
    assert f.target_xy is not None
    assert f.utc.year == 2025


def test_missing_row_field_raises():
    ref_wcs, _ = make_reference_grid(RA, DEC, size_pixels=8)
    with pytest.raises(ValueError, match="release"):
        prepare_frame(FIXTURE.read_bytes(), {**ROW, "release": None}, ref_wcs, (8, 8))


def test_render_shared_stretch(prepared):
    stretch = shared_stretch([prepared.image])
    assert stretch is not None and stretch.method == "asinh" and stretch.hi > stretch.lo
    assert to_webp(prepared.image, stretch)[:4] == b"RIFF"
    assert render_flag_mask_png(prepared.masks)[:8] == b"\x89PNG\r\n\x1a\n"
    assert shared_stretch([np.full((2, 2), np.nan)]) is None
