"""POST /api/opinions: contract-valid, and an honest "can't tell" until motion and spectrum are measured."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from api import main, opinions
from planetes.contracts import Distance, MotionOpinion, MotionTruth, OpinionsRequest, SpectrumOpinion

CONTRACTS = Path(__file__).resolve().parents[2] / "contracts"


def _validator(name: str) -> Draft202012Validator:
    schemas = [json.loads(p.read_text(encoding="utf-8")) for p in CONTRACTS.glob("*.schema.json")]
    reg = Registry().with_resources((s["$id"], Resource.from_contents(s)) for s in schemas)
    schema = next(s for s in schemas if s["$id"].endswith("/" + name))
    return Draft202012Validator(schema, registry=reg)


BARNARD = {"ra": 269.4521, "dec": 4.6934}


def test_opinions_without_measurements_is_cant_tell_and_valid() -> None:
    with TestClient(main.app) as client:
        resp = client.post("/api/opinions", json=BARNARD)
    assert resp.status_code == 200
    body = resp.json()
    _validator("opinions.schema.json").validate(body)
    assert body["verdict"]["label"] == "cant_tell"
    assert body["verdict"]["reasons"] == [opinions.MOTION_PENDING, opinions.SPECTRUM_PENDING]
    assert body["motion"]["value"] is None and body["spectrum"]["class"] is None


def test_opinions_rejects_bad_coordinates() -> None:
    with TestClient(main.app) as client:
        resp = client.post("/api/opinions", json={"ra": 400, "dec": 0})
    assert resp.status_code == 400 or resp.status_code == 422
    _validator("error.schema.json").validate(resp.json())


def test_measured_opinions_go_through_the_verdict_engine(monkeypatch) -> None:
    # Shape test of the wiring only: these inputs exercise decide(), they are never shown or baked.
    pc = Distance(lo=3.0, hi=4.0, unit="pc")
    motion = MotionOpinion(
        kind="proper_motion",
        value=4.7,
        unit="arcsec/yr",
        err=0.1,
        pa_deg=120.0,
        distance=Distance(lo=None, hi=None, unit=None),
        truth=MotionTruth(value=None, source=None),
        quality="good",
        method="test",
    )
    spectrum = SpectrumOpinion(
        kind="template", **{"class": "T1"}, temperature_k=None, distance=pc, quality="good", method="test"
    )
    monkeypatch.setattr(opinions, "measure_motion", lambda req: motion)
    monkeypatch.setattr(opinions, "measure_spectrum", lambda req, points=None, moving_sso=False: (spectrum, False))
    out = opinions.opinions_for(OpinionsRequest(ra=330.0, dec=-56.8))
    assert out.verdict.label == "agree"


def test_baked_spectrum_feeds_the_typer() -> None:
    """Real baked ε Indi B spectrum -> template opinion with a pc distance (motion still unmeasured -> can't tell)."""
    import json
    from pathlib import Path

    from planetes.contracts import SpectrumResult

    path = Path(__file__).resolve().parents[2] / "web" / "public" / "data" / "targets" / "epsindib" / "spectrum.json"
    result = SpectrumResult.model_validate(json.loads(path.read_text(encoding="utf-8")))
    out = opinions.opinions_for(OpinionsRequest(ra=result.target.ra, dec=result.target.dec), points=result.points)
    assert out.spectrum.kind == "template" and out.spectrum.distance.unit == "pc"
    assert out.verdict.label == "cant_tell"
    assert any("Motion" in r for r in out.verdict.reasons)
