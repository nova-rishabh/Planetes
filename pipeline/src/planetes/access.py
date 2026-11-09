"""
Planetes Data Access Module (D2.1)
NASA/IPAC IRSA TAP query and concurrent cutout retrieval for SPHEREx images.
"""

from __future__ import annotations

import concurrent.futures
import hashlib
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

import pandas as pd
import requests
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


def compute_frame_id(obs_id: str, ra: float, dec: float, size_deg: float) -> str:
    """Return f_ + first 12 hex characters of sha1(obs_id + cutout params)."""
    hash_str = f"{obs_id}_{ra:.6f}_{dec:.6f}_{size_deg:.4f}"
    digest = hashlib.sha1(hash_str.encode("utf-8")).hexdigest()[:12]
    return f"f_{digest}"


def extract_detector(bandpass_name: str) -> int:
    """Extract detector integer (1-6) from bandpass name like SPHEREx-D1."""
    match = re.search(r"D(\d)", str(bandpass_name))
    if match:
        return int(match.group(1))
    return 1


def extract_release(uri: str) -> str:
    """Extract data release string (QR2, QR3) from artifact URI."""
    uri_str = str(uri).lower()
    if "qr3" in uri_str:
        return "QR3"
    elif "qr2" in uri_str:
        return "QR2"
    return "QR2"


def find_frames(
    ra: float,
    dec: float,
    size_deg: float = 0.05,
    limit: int | None = None,
    release: str = "auto",
) -> pd.DataFrame:
    """
    Find SPHEREx image frames covering (ra, dec).
    
    Parameters
    ----------
    ra : float
        Right Ascension in degrees (ICRS).
    dec : float
        Declination in degrees (ICRS).
    size_deg : float
        Cutout bounding size in degrees.
    limit : int | None
        Optional maximum number of frames to retrieve from TAP.
    release : str
        Data release to query ('auto' for QR2+QR3 combined, or 'QR2', 'QR3').
        
    Returns
    -------
    pd.DataFrame
        Matching contract columns: obs_id, release, mjd, detector, frame_id, cutout_url.
    """
    log.info(f"Querying IRSA TAP for frames at RA={ra:.6f}, Dec={dec:.6f} (release={release})...")

    top_clause = f"TOP {limit} " if limit else ""
    adql = f"""
    SELECT {top_clause}
        p.planeid,
        p.energy_bandpassname,
        p.time_bounds_lower,
        p.time_bounds_upper,
        p.obs_publisher_did,
        a.uri
    FROM spherex.artifact a
    JOIN spherex.plane p ON a.planeid = p.planeid
    WHERE 1 = CONTAINS(POINT('ICRS', {ra:.6f}, {dec:.6f}), p.poly)
    ORDER BY p.time_bounds_lower ASC, p.energy_bandpassname ASC
    """
    df = query_irsa_tap(adql)

    if df.empty:
        log.warning(f"No frames found at RA={ra}, Dec={dec}")
        return pd.DataFrame(
            columns=["obs_id", "release", "mjd", "detector", "frame_id", "cutout_url", "epoch_group"]
        )

    # Format required contract columns
    df["obs_id"] = df["obs_publisher_did"].astype(str)
    df["release"] = df["uri"].apply(extract_release)
    df["mjd"] = df["time_bounds_lower"].astype(float)
    df["detector"] = df["energy_bandpassname"].apply(extract_detector)
    df["frame_id"] = df.apply(
        lambda r: compute_frame_id(r["obs_id"], ra, dec, size_deg), axis=1
    )
    df["cutout_url"] = (
        "https://irsa.ipac.caltech.edu/"
        + df["uri"].astype(str)
        + f"?center={ra:.6f},{dec:.6f}d&size={size_deg}"
    )

    # Filter release if explicitly requested and not 'auto'
    if release and release.lower() != "auto":
        target_rel = release.strip().upper()
        df = df[df["release"].str.upper() == target_rel].reset_index(drop=True)

    # Epoch grouping (gaps > 1 day)
    df = df.sort_values(by="mjd").reset_index(drop=True)
    time_diffs = df["mjd"].diff().fillna(0)
    df["epoch_group"] = (time_diffs > 1.0).cumsum()

    log.info(
        f"Retrieved {len(df)} total frames ({df['release'].value_counts().to_dict()}) across {df['epoch_group'].nunique()} survey epochs."
    )
    return df[
        ["obs_id", "release", "mjd", "detector", "frame_id", "cutout_url", "epoch_group"]
    ]


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
        return key, cached_data

    for attempt in range(1, max_retries + 1):
        try:
            resp = _SESSION.get(url, timeout=timeout)
            if resp.status_code == 200 and len(resp.content) > 1000:
                cache.put(key, resp.content, content_type="application/fits")
                return key, resp.content
            log.warning(f"Attempt {attempt}: HTTP {resp.status_code} for {url}")
        except Exception as e:
            log.warning(f"Attempt {attempt} download failed for {url}: {e}")
        time.sleep(1.5 * attempt)

    return key, None


def fetch_cutouts(
    frames_df: pd.DataFrame,
    max_concurrent: int = 8,
    cache: Cache | None = None,
) -> dict[str, bytes]:
    """Download cutouts concurrently (max 8) with caching."""
    if cache is None:
        cache = from_env()

    results: dict[str, bytes] = {}
    tasks = [
        (row["cutout_url"], f"cutouts/{row['frame_id']}.fits")
        for _, row in frames_df.iterrows()
    ]

    log.info(f"Downloading {len(tasks)} cutouts (concurrency: {max_concurrent})...")

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


if __name__ == "__main__":
    # Test on Gaia DR3 2026 position for Barnard's Star with release="auto"
    ra_b = 269.4461
    dec_b = 4.7703
    df = find_frames(ra_b, dec_b, release="auto")
    print("\nDataFrame structure:")
    print(df.head())
    print("\nCounts by detector and release:")
    print(df.groupby(["release", "detector"]).size())