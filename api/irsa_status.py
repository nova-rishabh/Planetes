"""Live check of the IRSA TAP service, used by GET /api/health."""

from __future__ import annotations

import time
from typing import Literal

import httpx

# A real, tiny search of the SPHEREx table the time-lapse uses. IRSA's VOSI /TAP/availability page kept saying "true"
# while every search returned 502, and generic TAP_SCHEMA queries can succeed while SPHEREx searches fail (both
# checked), so the badge asks the SPHEREx table itself.
IRSA_TAP_SYNC_URL = "https://irsa.ipac.caltech.edu/TAP/sync"
PROBE_QUERY = {"LANG": "ADQL", "FORMAT": "csv", "QUERY": "SELECT TOP 1 planeid FROM spherex.plane"}
# Fallback check: IRSA's SIA image search, asked for SPHEREx frames at Barnard's Star (always covered).
SIA_URL = "https://irsa.ipac.caltech.edu/SIA"
SIA_PROBE = {
    "COLLECTION": "spherex_dr1",
    "POS": "CIRCLE 269.4485 4.7394 0.0001",
    "RESPONSEFORMAT": "CSV",
    "MAXREC": "2",
}

TIMEOUT_S = 5.0
# Answers slower than this count as "slow". Picked by hand; the first real check took ~2.0 s.
SLOW_AFTER_S = 3.0
# Reuse a result for this long so frequent health checks (e.g. Render's) don't hammer IRSA.
CACHE_TTL_S = 30.0

IrsaState = Literal["ok", "slow", "down"]


def parse_available(csv_text: str) -> bool:
    """True if the probe search returned its CSV header (planeid) and at least one row."""
    lines = [ln for ln in csv_text.strip().splitlines() if ln.strip()]
    return len(lines) >= 2 and lines[0].strip().strip('"') == "planeid"


def classify(http_status: int | None, available: bool, elapsed_s: float) -> IrsaState:
    """Map a probe outcome to ok/slow/down. http_status None means no response (timeout/network error)."""
    if http_status != 200 or not available:
        return "down"
    return "ok" if elapsed_s < SLOW_AFTER_S else "slow"


async def probe(client: httpx.AsyncClient) -> IrsaState:
    """One real, tiny TAP search (5 s timeout)."""
    start = time.monotonic()
    try:
        resp = await client.get(IRSA_TAP_SYNC_URL, params=PROBE_QUERY, timeout=TIMEOUT_S)
        state = classify(resp.status_code, parse_available(resp.text), time.monotonic() - start)
    except httpx.HTTPError:
        state = "down"
    if state != "down":
        return state
    # TAP failed: searches still work through IRSA's SIA image search (planetes.access falls back to it), so report
    # "slow" rather than "down" when SIA answers. "down" means neither route works.
    try:
        sia = await client.get(SIA_URL, params=SIA_PROBE, timeout=TIMEOUT_S)
    except httpx.HTTPError:
        return "down"
    rows = [ln for ln in sia.text.splitlines() if ln.strip()]
    return "slow" if sia.status_code == 200 and rows and rows[0].startswith("s_ra") and len(rows) >= 2 else "down"


class CachedProbe:
    """Keeps the last probe result for CACHE_TTL_S seconds."""

    def __init__(self) -> None:
        self._state: IrsaState | None = None
        self._at = 0.0

    async def get(self, client: httpx.AsyncClient) -> IrsaState:
        now = time.monotonic()
        if self._state is None or now - self._at > CACHE_TTL_S:
            self._state = await probe(client)
            self._at = time.monotonic()
        return self._state
