"""tests: proper motion fitting, asteroid rate inversion, and V1/V2 validation."""

from __future__ import annotations

import os

import numpy as np
import pytest
from astropy.io import fits
from astropy.time import Time
from astropy.wcs import WCS

import planetes.motion as pm
from planetes.contracts import MotionOpinion

BARNARD_FRAMES_CSV = r"C:\Users\Lenovo\.gemini\antigravity\scratch\barnard\frames.csv"
BARNARD_DIR = r"C:\Users\Lenovo\.gemini\antigravity\scratch\barnard"
EPSINDIB_TIMELAPSE = (
    r"C:\Users\Lenovo\.gemini\antigravity\scratch\Planetes-main\web\public\data\targets"
    r"\epsindib\timelapse_exposures.json"
)


def test_v1_barnards_star_proper_motion_validation() -> None:
    """V1 Validation test (docs/04 §7):

    Barnard's Star proper motion from SPHEREx epochs + Gaia DR3:
    μ within 10%; direction within 5°.
    """
    if not os.path.exists(BARNARD_FRAMES_CSV):
        pytest.skip("Barnard frames not available")

    # Gaia DR3 reference at epoch 2016.0
    t_gaia = Time(2016.0, format="jyear").mjd
    ra_gaia = 269.44850252544
    dec_gaia = 4.73942005111
    truth_mu = float(np.hypot(-801.551, 10362.394) / 1000.0)  # 10.393 arcsec/yr
    truth_pa = float(np.degrees(np.arctan2(-801.551, 10362.394)) % 360.0)  # 355.58 deg

    import pandas as pd

    df = pd.read_csv(BARNARD_FRAMES_CSV)

    epochs = [t_gaia]
    ras = [ra_gaia]
    decs = [dec_gaia]

    for _, row in df.iterrows():
        fpath = os.path.join(BARNARD_DIR, row["file"])
        with fits.open(fpath) as hdul:
            w = WCS(hdul["IMAGE"].header)
            data = hdul["IMAGE"].data
            sub = data[26:33, 26:33]
            dy, dx = np.unravel_index(np.nanargmax(sub), sub.shape)
            px = 26 + dx
            py = 26 + dy
            world = w.all_pix2world([[px, py]], 0)[0]
            epochs.append(float(row["mjd"]))
            ras.append(float(world[0]))
            decs.append(float(world[1]))

    fit = pm.fit_proper_motion(epochs, ras, decs)

    # Acceptance threshold checks
    mu_err_pct = abs(fit.mu_arcsec_yr - truth_mu) / truth_mu * 100.0
    pa_err_deg = abs(fit.pa_deg - truth_pa)

    assert mu_err_pct < 10.0, f"mu error {mu_err_pct:.2f}% exceeds 10% threshold"
    assert pa_err_deg < 5.0, f"PA error {pa_err_deg:.2f}° exceeds 5° threshold"

    # Verify MotionOpinion contract output
    opinion = pm.star_motion_opinion(
        fit=fit,
        truth_pm=truth_mu,
        truth_source="Gaia DR3",
        parallax_mas=546.98,
    )
    assert isinstance(opinion, MotionOpinion)
    assert opinion.kind == "proper_motion"
    assert opinion.unit == "arcsec/yr"
    assert opinion.quality == "good"
    assert opinion.distance.unit is None  # a catalogue parallax is never our measurement


def test_static_star_classification() -> None:
    # A stationary star observed over 2 years with negligible jitter (< 0.05"/yr)
    epochs = [60800.0, 61165.0, 61530.0]
    ras = [100.0, 100.000001, 100.000002]
    decs = [20.0, 20.000001, 20.000001]

    fit = pm.fit_proper_motion(epochs, ras, decs)
    opinion = pm.star_motion_opinion(fit)

    assert opinion.kind == "static"
    assert opinion.value is not None
    assert opinion.value < 0.15


def test_sso_rate_fitting_and_distance_inversion() -> None:
    # Main belt asteroid observed 4 times over 3 hours
    # Apparent motion: ~32 arcsec/hr retrograde
    epochs = [60800.00, 60800.0417, 60800.0833, 60800.1250]  # 1 hr steps
    ra0, dec0 = 223.0, -16.0  # near opposition
    ras = [ra0 - (i * 32.0 / 3600.0) for i in range(4)]
    decs = [dec0 for _ in range(4)]

    fit = pm.fit_sso_rate(epochs, ras, decs)
    assert 30.0 < fit.rate_arcsec_hr < 34.0
    assert fit.rate_err_arcsec_hr < 1.0

    r_lo, r_hi = pm.rate_to_distance_range(
        rate_arcsec_hr=fit.rate_arcsec_hr,
        rate_err_arcsec_hr=fit.rate_err_arcsec_hr,
        obs_time_mjd=60800.0,
        ra_deg=ra0,
        dec_deg=dec0,
    )
    # At ~32 arcsec/hr, distance should bracket main belt (~2.2 - 3.4 AU)
    assert 1.8 <= r_lo <= 2.8
    assert 2.6 <= r_hi <= 4.0

    opinion = pm.asteroid_motion_opinion(fit, (r_lo, r_hi), truth_dist_au=2.77, truth_source="JPL Horizons")
    assert isinstance(opinion, MotionOpinion)
    assert opinion.kind == "sso_rate"
    assert opinion.unit == "arcsec/hr"
    assert opinion.distance.unit == "au"
    assert opinion.distance.lo == r_lo
    assert opinion.distance.hi == r_hi


# --- measure_position: centroid in a real SPHEREx cutout (Shivaansh's centroid idea) ---
_BARNARD_FITS = os.path.join(os.path.dirname(__file__), "data", "barnard_d3_qr2_2025W33_2C_0321_1.fits")


def _cutout_bytes() -> bytes:
    with open(_BARNARD_FITS, "rb") as f:
        return f.read()


def test_measure_position_refuses_saturated_barnard() -> None:
    """Barnard's Star is saturated in D3; the centroid must be refused, not guessed."""
    with fits.open(_BARNARD_FITS) as h:
        w = WCS(h["IMAGE"].header).celestial
        ny, nx = h["IMAGE"].data.shape
    ra, dec = (float(v) for v in w.pixel_to_world_values(nx / 2, ny / 2))
    assert pm.measure_position(_cutout_bytes(), 60900.0, ra, dec) is None  # saturated core: refused
    assert pm.measure_position(_cutout_bytes(), 60900.0, ra + 5.0, dec) is None  # off the cutout


def test_measure_position_recovers_injected_star() -> None:
    """Checks the centroid maths only: a test star is added to a clean patch of the real cutout at a known sky
    position, and the measured RA/Dec must land on it within 0.1 px. Never used as data."""
    import io

    with fits.open(_BARNARD_FITS) as h:
        hdul = fits.HDUList([hdu.copy() for hdu in h])
    img = hdul["IMAGE"].data.astype(np.float64)
    from planetes.frames import classify_flags, flag_bits

    badmask = classify_flags(np.asarray(hdul["FLAGS"].data, dtype=np.int64), flag_bits(hdul["FLAGS"].header)).bad
    w = WCS(hdul["IMAGE"].header).celestial
    ny, nx = img.shape
    # pick the cleanest 7x7 patch away from the saturated centre (no bad pixels, lowest scatter)
    best = None
    for y in range(4, ny - 4):
        for x in range(4, nx - 4):
            if abs(x - nx / 2) < 6 and abs(y - ny / 2) < 6:
                continue
            if badmask[y - 3 : y + 4, x - 3 : x + 4].any():
                continue
            s = float(np.nanstd(img[y - 3 : y + 4, x - 3 : x + 4]))
            if best is None or s < best[0]:
                best = (s, x, y)
    assert best is not None
    _, x0, y0 = best
    xt, yt = x0 + 0.3, y0 - 0.2
    yy, xx = np.mgrid[0:ny, 0:nx]
    img = img + 200 * best[0] * np.exp(-((xx - xt) ** 2 + (yy - yt) ** 2) / (2 * 0.9**2))
    hdul["IMAGE"].data = img.astype(np.float32)
    buf = io.BytesIO()
    hdul.writeto(buf)
    ra_t, dec_t = (float(v) for v in w.pixel_to_world_values(xt, yt))
    ra_guess, dec_guess = (float(v) for v in w.pixel_to_world_values(x0, y0))
    m = pm.measure_position(buf.getvalue(), 60900.0, ra_guess, dec_guess)
    assert m is not None
    xm, ym = (float(v) for v in w.world_to_pixel_values(m.ra_deg, m.dec_deg))
    assert abs(xm - xt) < 0.1 and abs(ym - yt) < 0.1
    assert m.mjd == 60900.0
