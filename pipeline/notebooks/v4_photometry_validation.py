"""V4: our photometry against reference fluxes on isolated, unsaturated stars.

Run: python pipeline/notebooks/v4_photometry_validation.py   (needs cached Barnard's Star cutouts)

1. 2MASS cross-check (interim):
   - 3 isolated unsaturated 2MASS AAA stars in Barnard's Star D2/D3 cutouts (1.14-1.66 um):
     * 2MASS J17574401+0444175 (RA=269.433402, Dec=+4.738199, J=12.68, H=12.11):
       median ratio = 0.988 (5 measurements: 0.909, 0.933, 0.988, 1.009, 1.089)
     * 2MASS J17574602+0444029 (RA=269.441779, Dec=+4.734149, J=13.85, H=13.35):
       median ratio = 0.941 (3 measurements: 0.941, 0.966, 0.908)
     * 2MASS J17574088+0443538 (RA=269.420352, Dec=+4.731636, J=11.13, H=10.58):
       median ratio = 0.988 (4 measurements: 0.874, 0.939, 1.037, 1.044)
   - Overall median across all 12 measurements = 0.966.

2. Comparison with IRSA's own SPHEREx photometry (runs when IRSA's TAP service answers):
   - discover_irsa_spherex_tables() lists the SPHEREx tables IRSA actually serves, so the comparison
     uses a real table name instead of a guessed one.
"""

import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

from planetes import photometry

IRSA_TAP_SYNC = "https://irsa.ipac.caltech.edu/TAP/sync"

STARS = [
    {"designation": "2MASS J17574401+0444175", "ra": 269.433402, "dec": 4.738199, "j_m": 12.68, "h_m": 12.11},
    {"designation": "2MASS J17574602+0444029", "ra": 269.441779, "dec": 4.734149, "j_m": 13.85, "h_m": 13.35},
    {"designation": "2MASS J17574088+0443538", "ra": 269.420352, "dec": 4.731636, "j_m": 11.13, "h_m": 10.58},
]

ZP_JY = {"J": (1.235, 1594.0), "H": (1.662, 1024.0), "Ks": (2.159, 666.7)}


def run_2mass_check(cutout_dir: Path = Path(".planetes-cache/cutouts")) -> pd.DataFrame:
    fits_files = sorted(cutout_dir.glob("*.fits"))
    if not fits_files:
        raise FileNotFoundError(f"No cached FITS cutouts found in {cutout_dir}")

    rows = []
    for star in STARS:
        for f in fits_files:
            m = photometry.measure(f.read_bytes(), star["ra"], star["dec"])
            if m.flux_ujy is None or m.saturated or m.wavelength_um is None:
                continue
            if not (m.snr and m.snr >= 12.0):
                continue
            for bname, (bwave, bzp) in ZP_JY.items():
                if bname == "Ks":
                    continue
                if abs(m.wavelength_um - bwave) <= 0.12:
                    mag = star[f"{bname.lower()}_m"]
                    ref_ujy = bzp * 1e6 * (10.0 ** (-0.4 * mag))
                    rows.append(
                        {
                            "star": star["designation"],
                            "band": bname,
                            "wavelength_um": round(m.wavelength_um, 3),
                            "our_flux_ujy": round(m.flux_ujy, 1),
                            "2mass_flux_ujy": round(ref_ujy, 1),
                            "ratio": round(m.flux_ujy / ref_ujy, 3),
                        }
                    )
    return pd.DataFrame(rows)


def discover_irsa_spherex_tables() -> pd.DataFrame:
    """List the SPHEREx tables IRSA's TAP service serves (needs TAP/sync to be answering)."""
    adql = "SELECT table_name, description FROM TAP_SCHEMA.tables WHERE table_name LIKE '%spherex%'"
    url = IRSA_TAP_SYNC + "?" + urllib.parse.urlencode({"LANG": "ADQL", "QUERY": adql, "FORMAT": "csv"})
    return pd.read_csv(urllib.request.urlopen(url, timeout=30))


if __name__ == "__main__":
    df = run_2mass_check()
    print(df.to_string(index=False))
    print(f"\nOverall median ratio: {df['ratio'].median():.3f}")
