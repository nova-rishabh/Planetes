"""Automated unit & fixture tests for SPHEREx image stacking and RGB composites (Deliverable D2.3)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from astropy.io import fits
from astropy.wcs import WCS

from planetes import frames, stack

FIXTURE_FITS = Path(__file__).parent / "data" / "barnard_d3_qr2_2025W33_2C_0321_1.fits"


def _make_coadd(
    val: float, var: float, shape: tuple[int, int] = (16, 16), det: int = 1, mjd: float = 61000.0
) -> stack.CoaddResult:
    return stack.CoaddResult(
        image=np.full(shape, val, dtype=np.float64),
        variance=np.full(shape, var, dtype=np.float64),
        coverage=np.ones(shape, dtype=np.int32),
        detector=det,
        epoch_index=0,
        mjd_start=mjd,
        mjd_end=mjd,
        n_frames=1,
        wavelength_um=1.0 + 0.5 * det,
    )


def test_inverse_variance_stack_weights_and_masks() -> None:
    """Inverse-variance weighting should give 4x weight to a frame with 1/4 the variance and exclude masked pixels."""
    img_a = np.full((8, 8), 10.0)
    var_a = np.full((8, 8), 1.0)  # weight = 1.0
    good_a = np.ones((8, 8), dtype=bool)

    img_b = np.full((8, 8), 20.0)
    var_b = np.full((8, 8), 0.25)  # weight = 4.0
    good_b = np.ones((8, 8), dtype=bool)
    good_b[0, 0] = False  # masked cosmic ray on frame B

    coadd = stack.inverse_variance_stack(
        [img_a, img_b], [var_a, var_b], [good_a, good_b], detector=3, mjds=[61000.0, 61005.0]
    )

    # Unmasked pixel: (1*10 + 4*20) / (1 + 4) = 90 / 5 = 18.0; var = 1 / 5 = 0.20
    assert np.isclose(coadd.image[4, 4], 18.0)
    assert np.isclose(coadd.variance[4, 4], 0.20)
    assert coadd.coverage[4, 4] == 2

    # Pixel (0, 0) masked in B -> falls back cleanly to frame A only
    assert np.isclose(coadd.image[0, 0], 10.0)
    assert np.isclose(coadd.variance[0, 0], 1.0)
    assert coadd.coverage[0, 0] == 1
    assert coadd.mjd_start == 61000.0
    assert coadd.mjd_end == 61005.0


def test_difference_coadds_propagates_variance_and_dipole() -> None:
    """Epoch B - Epoch A difference image must propagate var_A + var_B and render valid WebP."""
    ep_a = _make_coadd(val=2.0, var=0.1, det=3, mjd=60900.0)
    ep_b = _make_coadd(val=2.0, var=0.15, det=3, mjd=61100.0)
    # Simulate proper-motion dipole: star leaves (4, 4) and arrives at (4, 10)
    ep_a.image[4, 4] = 12.0
    ep_b.image[4, 10] = 12.0

    diff = stack.difference_coadds(ep_a, ep_b)
    assert np.isclose(diff.image[4, 4], -10.0)
    assert np.isclose(diff.image[4, 10], +10.0)
    assert np.isclose(diff.variance[4, 4], 0.25)

    webp_bytes = stack.difference_to_webp(diff)
    assert webp_bytes[:4] == b"RIFF"
    assert webp_bytes[8:12] == b"WEBP"


def test_sum_coadds_reduces_variance_by_n() -> None:
    """Summing N identical-variance epochs must reduce variance by factor N."""
    epochs = [_make_coadd(val=5.0, var=0.4, det=2, mjd=61000.0 + i) for i in range(4)]
    deep = stack.sum_coadds(epochs)
    assert deep.n_frames == 4
    assert np.isclose(np.nanmedian(deep.image), 5.0)
    assert np.isclose(np.nanmedian(deep.variance), 0.1)


def test_colour_composite_rgb_bands_and_webp() -> None:
    """3-band RGB composite maps D1+D2 -> Blue, D3+D4 -> Green, D5+D6 -> Red."""
    by_det = {d: _make_coadd(val=1.0, var=0.05, shape=(12, 12), det=d) for d in range(1, 7)}
    # Put bright hot source in D1 (Blue) at row 2 (south -> bottom after north-up flip)
    by_det[1].image[2, 3] = 50.0
    # Put bright red source in D6 (Red) at row 9 (north -> top after north-up flip)
    by_det[6].image[9, 8] = 50.0

    rgb = stack.colour_composite(by_det)
    assert rgb.shape == (12, 12, 3)
    assert rgb.dtype == np.uint8

    # North-up flip puts FITS row 9 at image row (12 - 1 - 9) = 2
    assert rgb[2, 8, 0] > rgb[2, 8, 2]  # Red channel dominates
    # FITS row 2 is at image row (12 - 1 - 2) = 9
    assert rgb[9, 3, 2] > rgb[9, 3, 0]  # Blue channel dominates

    webp_bytes = stack.colour_to_webp(rgb)
    assert webp_bytes[:4] == b"RIFF"
    assert webp_bytes[8:12] == b"WEBP"


@pytest.mark.skipif(not FIXTURE_FITS.exists(), reason="Offline Barnard FITS fixture missing")
def test_reproject_and_stack_real_spherex_fixture() -> None:
    """Reprojecting and stacking real SPHEREx cutout FITS produces finite image and positive coverage."""
    with fits.open(FIXTURE_FITS) as hdul:
        w0 = WCS(hdul["IMAGE"].header)
        ra_c, dec_c = w0.pixel_to_world_values(11, 11)

    ref_wcs, _ = frames.make_reference_grid(float(ra_c), float(dec_c), size_pixels=24)
    img, var, good = stack.prepare_reprojected_variance(FIXTURE_FITS.read_bytes(), ref_wcs, grid_shape=(24, 24))
    coadd = stack.inverse_variance_stack([img], [var], [good], detector=3)

    assert np.any(coadd.coverage > 0)
    assert np.any(np.isfinite(coadd.image))
