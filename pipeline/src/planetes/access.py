"""
Planetes Data Access Module (D2.1)
Direct NASA/IPAC IRSA TAP query and cutout retrieval for SPHEREx images.
"""

import io
import time
import requests
import pandas as pd

IRSA_TAP_URL = "https://irsa.ipac.caltech.edu/TAP/sync"


def query_irsa_tap(adql_query: str) -> pd.DataFrame:
    """Execute an ADQL query against IRSA TAP service and return a Pandas DataFrame."""
    params = {
        "REQUEST": "doQuery",
        "LANG": "ADQL",
        "FORMAT": "csv",
        "QUERY": adql_query.strip(),
    }
    resp = requests.post(IRSA_TAP_URL, data=params, timeout=120)
    if resp.status_code != 200:
        raise RuntimeError(f"IRSA TAP Error ({resp.status_code}): {resp.text[:500]}")
    return pd.read_csv(io.StringIO(resp.text))


def print_irsa_schema():
    """Inspect and print real column names from SPHEREx tables for PR verification."""
    print("=" * 60)
    print("Fetching real IRSA TAP column names for SPHEREx...")
    print("=" * 60)
    query = """
    SELECT table_name, column_name, datatype, description 
    FROM tap_schema.columns 
    WHERE table_name IN ('spherex.plane', 'spherex.artifact')
    ORDER BY table_name, column_name
    """
    df = query_irsa_tap(query)
    for _, row in df.iterrows():
        print(f"[{row['table_name']}] {row['column_name']:<25} ({row['datatype']}) - {row['description']}")
    return df


def find_frames(ra: float, dec: float, size_deg: float = 0.05) -> pd.DataFrame:
    """
    Find SPHEREx image frames covering (ra, dec) and construct cutout URLs.
    Searches spherex.plane and spherex.artifact according to official IRSA docs.
    """
    print(f"\nSearching SPHEREx frames for RA={ra:.6f}, Dec={dec:.6f}...")
    adql = f"""
    SELECT 
        p.planeid,
        p.energy_bandpassname,
        p.time_bounds_lower,
        p.time_bounds_upper,
        'https://irsa.ipac.caltech.edu/' || a.uri || '?center={ra:.6f},{dec:.6f}d&size={size_deg}' AS cutout_url
    FROM spherex.artifact a
    JOIN spherex.plane p ON a.planeid = p.planeid
    WHERE 1 = CONTAINS(POINT('ICRS', {ra:.6f}, {dec:.6f}), p.poly)
    ORDER BY p.energy_bandpassname, p.time_bounds_lower
    """
    df = query_irsa_tap(adql)
    print(f"Found {len(df)} matching SPHEREx exposures.")
    return df


if __name__ == "__main__":
    # 1. Print real schema columns for the PR verification requirement
    print_irsa_schema()

    # 2. Test search on Barnard's Star at 2026 coordinates
    ra_barnard_2026 = 269.444747
    dec_barnard_2026 = 4.743126
    frames = find_frames(ra_barnard_2026, dec_barnard_2026)
    if not frames.empty:
        print("\nSample frame cutouts:")
        print(frames[["energy_bandpassname", "cutout_url"]].head(6).to_string())