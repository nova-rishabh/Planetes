import pytest

from planetes.access import compute_frame_id, extract_detector, extract_release, find_frames


def test_contract_offline():
    """Offline unit test verifying field transformations and ID hash format."""
    obs_id = "SPHEREx_test_001"
    frame_id = compute_frame_id(obs_id, 269.4461, 4.7703, 0.05)

    assert frame_id.startswith("f_")
    assert len(frame_id) == 14  # 'f_' + 12 hex chars
    assert extract_detector("SPHEREx-D1") == 1
    assert extract_detector("SPHEREx-D6") == 6
    assert extract_release("/ibe/data/spherex/qr3/level2/file.fits") == "QR3"
    assert extract_release("/ibe/data/spherex/qr2/level2/file.fits") == "QR2"
    assert extract_release("ibe/data/spherex/dr1/level2/2026W11_1A/l2b-v27-2026-232/1/x.fits") == "DR1"
    assert extract_release("ivo://irsa.ipac/spherex_dr1_deep?2026W19_2A_0001_1/D1") == "DR1"


@pytest.mark.network
def test_barnard_live_coverage():
    """Live IRSA test ensuring Barnard's Star returns all 6 detectors across QR2/QR3."""
    ra_b = 269.4461
    dec_b = 4.7703
    df = find_frames(ra_b, dec_b)

    assert not df.empty, "Live IRSA query returned no frames"
    required_cols = {"obs_id", "release", "mjd", "detector", "frame_id", "cutout_url"}
    assert required_cols.issubset(df.columns), f"Missing required columns: {required_cols - set(df.columns)}"

    # Ensure all 6 detectors are present
    detectors = set(df["detector"].unique())
    assert set(range(1, 7)).issubset(detectors), f"Missing detectors: {set(range(1, 7)) - detectors}"
