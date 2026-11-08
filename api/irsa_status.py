"""Live check of the IRSA TAP service, used by GET /api/health."""

from __future__ import annotations

import re
import time
from typing import Literal

import httpx

# IVOA VOSI availability endpoint of IRSA's TAP service. Checked on 2026-11-08: HTTP 200,
# <available>true</available>, "services work properly.", ~2.0 s.
IRSA_TAP_AVAILABILITY_URL = "https://irsa.ipac.caltech.edu/TAP/availability"
# Matches <available>…</available>, with or without a namespace prefix. A regex avoids running a full
# XML parser on remote content just to read one boolean.
_AVAILABLE_RE = re.compile(r"<(?:\w+:)?available>\s*(true|false)\s*</(?:\w+:)?available>", re.IGNORECASE)

TIMEOUT_S = 5.0
# [VERIFY] Answers slower than this count as "slow". Picked by hand; the first real check took ~2.0 s.
SLOW_AFTER_S = 3.0
# Reuse a result for this long so frequent health checks (e.g. Render's) don't hammer IRSA.
CACHE_TTL_S = 30.0

IrsaState = Literal["ok", "slow", "down"]


def parse_available(xml_text: str) -> bool:
    """True if a VOSI availability document says <available>true</available>."""
    match = _AVAILABLE_RE.search(xml_text)
    return match is not None and match.group(1).lower() == "true"


def classify(http_status: int | None, available: bool, elapsed_s: float) -> IrsaState:
    """Map a probe outcome to ok/slow/down. http_status None means no response (timeout/network error)."""
    if http_status != 200 or not available:
        return "down"
    return "ok" if elapsed_s < SLOW_AFTER_S else "slow"


async def probe(client: httpx.AsyncClient) -> IrsaState:
    """One real request to the TAP availability endpoint (5 s timeout)."""
    start = time.monotonic()
    try:
        resp = await client.get(IRSA_TAP_AVAILABILITY_URL, timeout=TIMEOUT_S)
    except httpx.HTTPError:
        return "down"
    elapsed = time.monotonic() - start
    return classify(resp.status_code, parse_available(resp.text), elapsed)


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
