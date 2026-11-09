import glob
from pathlib import Path

from planetes.frames import make_reference_grid, process_frame


def test_process_frame_real_fits():
    """Verify D2.2 acceptance on real cached SPHEREx cutout files."""
    fits_files = glob.glob(".planetes-cache/**/*.fits", recursive=True)
    if not fits_files:
        return

    fits_path = Path(fits_files[0])
    with open(fits_path, "rb") as f:
        fits_bytes = f.read()

    ra_center, dec_center = 269.4461, 4.7703
    ref_wcs, grid = make_reference_grid(ra_center, dec_center, size_pixels=64)

    frame_row = {
        "frame_id": "f_1234567890ab",
        "obs_id": fits_path.stem,
        "release": "QR3",
        "detector": 1,
        "mjd": 60500.0,
        "epoch_group": 0,
    }

    frame, webp_bytes, flags_png = process_frame(
        fits_bytes=fits_bytes,
        frame_row=frame_row,
        ref_wcs=ref_wcs,
        grid_shape=(64, 64),
        target_coord=(ra_center, dec_center),
        subtract_zodi=True,
    )

    # Acceptance checks:
    assert frame.wavelength_um is not None
    assert frame.wavelength_um > 0.5
    assert frame.flags_url == f"/api/frames/{frame.id}_flags.png"
    assert frame.target_xy is not None
    assert abs(frame.target_xy.root[0] - 31.5) < 1e-4

    # Web artifacts validity:
    assert webp_bytes[:4] == b"RIFF"
    assert flags_png[:8] == b"\x89PNG\r\n\x1a\n"
