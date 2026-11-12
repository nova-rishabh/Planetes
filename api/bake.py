"""Bake benchmark targets into web/public/data (docs/03 §6) with the same pipeline as the live API.

    python -m api.bake barnard [rdra ...]            (time-lapse; from the repo root; needs IRSA and SIMBAD)
    python -m api.bake --spectrum epsindib [...]     (spectrum.json: forced photometry on every exposure)
    python -m api.bake --overlays barnard [...]      (overlays.json: Gaia DR3 + AllWISE moved to each epoch)
    python -m api.bake --opinions epsindib [...]     (opinions.json: Two Opinions from the baked spectrum + motion)

Writes, per target: target.json (Resolved), timelapse_exposures.json (TimelapseResult) and frames/*.webp|png.
Frame URLs are relative (./frames/...), so the web app loads baked and live results the same way.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from planetes.cache import Cache
from planetes.contracts import OpinionsRequest, ProperMotion, SpectrumRequest, SpectrumResult, TimelapseRequest
from planetes.overlays import build_overlays, query_allwise_sources, query_gaia_sources
from planetes.resolve import BENCHMARK_QUERIES, resolve
from planetes.spectrum import build_spectrum

from .main import code_version
from .opinions import opinions_for
from .timelapse import run_timelapse

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "web" / "public" / "data" / "targets"
CUTOUT_CACHE = ROOT / ".planetes-cache"
FOV_DEG = 0.1
MAX_FRAMES = 60


class _SplitCache(Cache):
    """Downloaded cutouts go to the local cache; rendered frames go into the baked target folder."""

    def __init__(self, target_dir: Path) -> None:
        super().__init__(target_dir)
        self._cutouts = Cache(CUTOUT_CACHE)

    def get(self, key: str) -> bytes | None:
        return self._cutouts.get(key) if key.startswith("cutouts/") else super().get(key)

    def put(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> None:
        if key.startswith("cutouts/"):
            self._cutouts.put(key, data, content_type)
        else:
            super().put(key, data, content_type)


class _Progress:
    def progress(self, done: int, total: int | None, stage: str | None) -> None:
        print(f"  {stage} {done}/{total if total is not None else '?'}", flush=True)

    def partial(self, result: object) -> None:  # not needed offline
        pass


def bake(target_id: str) -> Path:
    out = DATA / target_id
    out.mkdir(parents=True, exist_ok=True)
    star = resolve(BENCHMARK_QUERIES[target_id])
    (out / "target.json").write_text(star.to_contract().model_dump_json(indent=2), encoding="utf-8")

    pm = None
    if star.pm_ra_masyr is not None and star.pm_dec_masyr is not None and star.ref_epoch_jyear is not None:
        pm = ProperMotion(
            pm_ra_masyr=star.pm_ra_masyr, pm_dec_masyr=star.pm_dec_masyr, ref_epoch_jyear=star.ref_epoch_jyear
        )
    req = TimelapseRequest(
        ra=star.ra_deg, dec=star.dec_deg, fov_deg=FOV_DEG, mode="exposures", max_frames=MAX_FRAMES, pm=pm
    )
    result = run_timelapse(req, _Progress(), _SplitCache(out), code_version())  # type: ignore[arg-type]
    for f in result.frames:
        f.image_url = f"./frames/{f.id}.webp"
        f.flags_url = f"./frames/{f.id}_flags.png"
    (out / "timelapse_exposures.json").write_text(
        json.dumps(result.model_dump(mode="json"), separators=(",", ":")), encoding="utf-8"
    )
    return out


def bake_spectrum(target_id: str) -> Path:
    """spectrum.json for a baked target, from its resolved position and proper motion (target.json)."""
    out = DATA / target_id
    t = json.loads((out / "target.json").read_text(encoding="utf-8"))
    pm = None
    if t.get("pm_ra_masyr") is not None and t.get("pm_dec_masyr") is not None and t.get("ref_epoch_jyear"):
        pm = ProperMotion(
            pm_ra_masyr=t["pm_ra_masyr"], pm_dec_masyr=t["pm_dec_masyr"], ref_epoch_jyear=t["ref_epoch_jyear"]
        )
    result = build_spectrum(
        SpectrumRequest(ra=t["ra"], dec=t["dec"], pm=pm),
        code_version(),
        Cache(CUTOUT_CACHE),
        progress=lambda done, total, stage: print(
            f"  {stage} {done}/{total if total is not None else '?'}", flush=True
        ),
    )
    (out / "spectrum.json").write_text(result.model_dump_json(by_alias=True), encoding="utf-8")
    return out / "spectrum.json"


def _pm(t: dict) -> ProperMotion | None:
    if t.get("pm_ra_masyr") is None or t.get("pm_dec_masyr") is None or not t.get("ref_epoch_jyear"):
        return None
    return ProperMotion(
        pm_ra_masyr=t["pm_ra_masyr"], pm_dec_masyr=t["pm_dec_masyr"], ref_epoch_jyear=t["ref_epoch_jyear"]
    )


def bake_opinions(target_id: str) -> Path:
    """opinions.json from the baked spectrum (and the measured motion once D3.3 provides one)."""
    out = DATA / target_id
    t = json.loads((out / "target.json").read_text(encoding="utf-8"))
    spec = SpectrumResult.model_validate_json((out / "spectrum.json").read_text(encoding="utf-8"))
    result = opinions_for(OpinionsRequest(ra=t["ra"], dec=t["dec"], pm=_pm(t)), points=list(spec.points))
    (out / "opinions.json").write_text(result.model_dump_json(by_alias=True), encoding="utf-8")
    return out / "opinions.json"


OVERLAY_MAX_SOURCES = 300


def bake_overlays(target_id: str) -> Path:
    """overlays.json for a baked time-lapse: catalogue stars covering its grid, at each observing epoch."""
    out = DATA / target_id
    tl = json.loads((out / "timelapse_exposures.json").read_text(encoding="utf-8"))
    grid = tl["grid"]
    ra, dec = grid["crval_deg"]
    radius_deg = grid["cdelt_deg"] * max(grid["naxis"]) / 2 * 1.42  # covers the corners
    # One position per day of observation is enough: nothing in these fields moves a pixel within a day.
    mjds = sorted({round(float(f["mjd"]), 1) for f in tl["frames"]})
    gaia = query_gaia_sources(ra, dec, radius_deg, max_sources=OVERLAY_MAX_SOURCES)
    wise = query_allwise_sources(ra, dec, radius_deg, max_sources=OVERLAY_MAX_SOURCES)
    result = build_overlays(gaia, wise, mjds)
    (out / "overlays.json").write_text(result.model_dump_json(), encoding="utf-8")
    return out / "overlays.json"


if __name__ == "__main__":
    args = sys.argv[1:]
    step = {"--spectrum": bake_spectrum, "--overlays": bake_overlays, "--opinions": bake_opinions}
    fn = next((step[a] for a in args if a in step), bake)
    for tid in [a for a in args if not a.startswith("--")] or ["barnard"]:
        print(f"Baking {fn.__name__} for {tid}…", flush=True)
        print("  wrote", fn(tid))
