"""
Planetes Data Access Module (D2.1)
NASA/IPAC IRSA TAP query, concurrent cutout downloads with caching,
and multi-band real SPHEREx FITS visualization.
"""

from __future__ import annotations

import concurrent.futures
import io
import logging
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

# Ensure local planetes module is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
from astropy.io import fits
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from planetes.cache import Cache, from_env

log = logging.getLogger("planetes.access")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

IRSA_TAP_URL = "https://irsa.ipac.caltech.edu/TAP/sync"


def get_http_session() -> requests.Session:
    """Create a persistent requests session with retries and a valid User-Agent."""
    session = requests.Session()
    retries = Retry(
        total=5,
        backoff_factor=1.5,
        status_forcelist=[429, 500, 502, 503, 504],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update(
        {
            "User-Agent": "Planetes-D2.1/1.0 (NASA Hackathon; Astropy Data Access)",
            "Accept": "text/csv,application/fits,*/*",
        }
    )
    return session


_SESSION = get_http_session()


def query_irsa_tap(adql_query: str, timeout: int = 120) -> pd.DataFrame:
    """Execute an ADQL query against IRSA TAP service with fallback and retries."""
    params = {
        "REQUEST": "doQuery",
        "LANG": "ADQL",
        "FORMAT": "csv",
        "QUERY": adql_query.strip(),
    }

    # Attempt POST first, then fall back to GET if the server forcibly drops POST
    for attempt in range(1, 4):
        try:
            resp = _SESSION.post(IRSA_TAP_URL, data=params, timeout=timeout)
            if resp.status_code == 200 and "error" not in resp.text.lower()[:200]:
                return pd.read_csv(io.StringIO(resp.text))
            elif resp.status_code == 200:
                raise RuntimeError(f"TAP Query Error: {resp.text[:400]}")
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            log.warning(f"POST attempt {attempt} failed ({e}). Retrying with GET...")
            time.sleep(2 * attempt)
            try:
                resp = _SESSION.get(IRSA_TAP_URL, params=params, timeout=timeout)
                if resp.status_code == 200 and "error" not in resp.text.lower()[:200]:
                    return pd.read_csv(io.StringIO(resp.text))
            except Exception as e2:
                log.warning(f"GET attempt {attempt} failed: {e2}")

    raise RuntimeError("Failed to query IRSA TAP after multiple attempts.")


def print_irsa_schema() -> pd.DataFrame:
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
        print(
            f"[{row['table_name']}] {row['column_name']:<25} ({row['datatype']}) - {row['description']}"
        )
    return df


def find_frames(
    ra: float, dec: float, size_deg: float = 0.05, limit: int | None = None
) -> pd.DataFrame:
    """
    Find SPHEREx image frames covering (ra, dec) and format cutout URLs.
    Checks QR3 first, falls back to QR2 if no QR3 frames exist.
    """
    log.info(f"Querying IRSA TAP for frames at RA={ra:.6f}, Dec={dec:.6f}...")

    top_clause = f"TOP {limit} " if limit else ""
    adql = f"""
    SELECT {top_clause}
        p.planeid,
        p.energy_bandpassname,
        p.time_bounds_lower,
        p.time_bounds_upper,
        a.uri
    FROM spherex.artifact a
    JOIN spherex.plane p ON a.planeid = p.planeid
    WHERE 1 = CONTAINS(POINT('ICRS', {ra:.6f}, {dec:.6f}), p.poly)
    ORDER BY p.time_bounds_lower ASC, p.energy_bandpassname ASC
    """
    df = query_irsa_tap(adql)

    if df.empty:
        log.warning(f"No frames found at RA={ra}, Dec={dec}")
        return df

    # Fallback check: QR3 then QR2
    qr3_mask = df["uri"].str.contains("qr3", case=False, na=False)
    if qr3_mask.any():
        df = df[qr3_mask].copy()

    def make_frame_id(uri: str) -> str:
        base = os.path.basename(str(uri)).replace(".fits", "")
        clean = re.sub(r"[^A-Za-z0-9_-]", "_", base)
        return f"f_{clean}"

    df["frame_id"] = df["uri"].apply(make_frame_id)
    df["cutout_url"] = (
        "https://irsa.ipac.caltech.edu/"
        + df["uri"].astype(str)
        + f"?center={ra:.6f},{dec:.6f}d&size={size_deg}"
    )

    df = df.sort_values(by="time_bounds_lower").reset_index(drop=True)
    time_diffs = df["time_bounds_lower"].diff().fillna(0)
    df["epoch_group"] = (time_diffs > 1.0).cumsum()

    log.info(
        f"Retrieved {len(df)} frames grouped into {df['epoch_group'].nunique()} survey epochs."
    )
    return df


def download_single_cutout(
    url: str,
    key: str,
    cache: Cache,
    max_retries: int = 3,
    timeout: int = 120,
) -> tuple[str, bytes | None]:
    """Download one cutout with local caching, retries, and a 2-minute timeout."""
    cached_data = cache.get(key)
    if cached_data is not None:
        log.info(f"Loaded from cache: {key}")
        return key, cached_data

    for attempt in range(1, max_retries + 1):
        try:
            resp = _SESSION.get(url, timeout=timeout)
            if resp.status_code == 200 and len(resp.content) > 1000:
                cache.put(key, resp.content, content_type="application/fits")
                log.info(f"Downloaded and cached: {key} ({len(resp.content)} bytes)")
                return key, resp.content
            log.warning(f"Attempt {attempt}: HTTP {resp.status_code} for {url}")
        except Exception as e:
            log.warning(f"Attempt {attempt} download failed for {url}: {e}")
        time.sleep(1.5 * attempt)

    return key, None


def fetch_cutouts(
    frames_df: pd.DataFrame,
    max_concurrent: int = 6,
    cache: Cache | None = None,
) -> dict[str, bytes]:
    """Download cutouts concurrently with caching."""
    if cache is None:
        cache = from_env()

    results: dict[str, bytes] = {}
    tasks = [(row["cutout_url"], f"cutouts/{row['frame_id']}.fits") for _, row in frames_df.iterrows()]

    log.info(f"Downloading {len(tasks)} cutouts (max concurrency: {max_concurrent})...")

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_concurrent) as executor:
        future_map = {
            executor.submit(download_single_cutout, url, key, cache, 3, 120): key
            for url, key in tasks
        }
        for future in concurrent.futures.as_completed(future_map):
            key = future_map[future]
            try:
                res_key, data = future.result()
                if data:
                    results[res_key] = data
            except Exception as exc:
                log.error(f"Download task error for {key}: {exc}")

    return results


def plot_barnard_6band():
    """Download 6 real SPHEREx detector cutouts for Barnard's Star (2026) and plot them."""
    ra_barnard = 269.444747
    dec_barnard = 4.743126

    df = find_frames(ra_barnard, dec_barnard, size_deg=0.04)
    if df.empty:
        print("No frames available for Barnard's Star.")
        return

    # Select one unique frame per detector band: SPHEREx-D1 through D6
    selected = []
    for band in ["SPHEREx-D1", "SPHEREx-D2", "SPHEREx-D3", "SPHEREx-D4", "SPHEREx-D5", "SPHEREx-D6"]:
        matching = df[df["energy_bandpassname"] == band]
        if not matching.empty:
            selected.append(matching.iloc[0])

    if not selected:
        selected_df = df.head(6)
    else:
        selected_df = pd.DataFrame(selected)

    print("\nSelected one exposure for each detector band:")
    for _, r in selected_df.iterrows():
        print(f"  {r['energy_bandpassname']} -> {r['frame_id']}")

    cache = from_env()
    cutouts = fetch_cutouts(selected_df, max_concurrent=6, cache=cache)

    fig, axes = plt.subplots(2, 3, figsize=(13, 8))
    axes = axes.flatten()

    for i, (_, row) in enumerate(selected_df.iterrows()):
        band = row["energy_bandpassname"]
        frame_id = row["frame_id"]
        key = f"cutouts/{frame_id}.fits"
        data_bytes = cutouts.get(key)

        ax = axes[i]
        if data_bytes:
            try:
                with fits.open(io.BytesIO(data_bytes)) as hdul:
                    # HDU 0 or HDU 1 contains image array
                    img_data = hdul[0].data
                    if img_data is None and len(hdul) > 1:
                        img_data = hdul[1].data
                    
                    if img_data is not None:
                        clean_data = img_data[np.isfinite(img_data)]
                        vmin, vmax = np.percentile(clean_data, [5, 98]) if len(clean_data) > 0 else (0, 1)
                        im = ax.imshow(img_data, origin="lower", cmap="magma", vmin=vmin, vmax=vmax)
                        ax.set_title(f"{band}\n{frame_id[:16]}...", fontsize=9)
                        plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
                    else:
                        ax.text(0.5, 0.5, "Empty Array", ha="center", va="center")
                        ax.set_title(band)
            except Exception as e:
                ax.text(0.5, 0.5, f"FITS Error\n{e}", ha="center", va="center", fontsize=8)
                ax.set_title(band)
        else:
            ax.text(0.5, 0.5, "Cutout Missing", ha="center", va="center")
            ax.set_title(band)

        ax.set_xticks([])
        ax.set_yticks([])

    plt.suptitle("Barnard's Star (2026 Coordinates) — Real SPHEREx Flight Cutouts", fontsize=14)
    plt.tight_layout()
    output_png = "barnard_real_spherex_6band.png"
    plt.savefig(output_png, dpi=150)
    print(f"\n[SUCCESS] 6-Panel Real Data Plot saved as: {output_png}")


if __name__ == "__main__":
    print_irsa_schema()
    plot_barnard_6band()