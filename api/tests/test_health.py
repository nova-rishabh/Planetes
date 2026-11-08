"""API tests. The network-marked test makes a real call to IRSA; the rest make no outside requests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from api import main
from api.irsa_status import SLOW_AFTER_S, classify, parse_available

CONTRACTS = Path(__file__).resolve().parents[2] / "contracts"


def _validator(name: str) -> Draft202012Validator:
    schemas = [json.loads(p.read_text(encoding="utf-8")) for p in CONTRACTS.glob("*.schema.json")]
    reg = Registry().with_resources((s["$id"], Resource.from_contents(s)) for s in schemas)
    schema = next(s for s in schemas if s["$id"].endswith("/" + name))
    return Draft202012Validator(schema, registry=reg)


def test_classify() -> None:
    assert classify(200, True, 0.5) == "ok"
    assert classify(200, True, SLOW_AFTER_S + 0.1) == "slow"
    assert classify(200, False, 0.5) == "down"
    assert classify(503, True, 0.5) == "down"
    assert classify(None, False, 5.0) == "down"


def test_parse_available() -> None:
    ns = "http://www.ivoa.net/xml/VOSIAvailability/v1.0"
    assert parse_available(
        f'<vosi:availability xmlns:vosi="{ns}" xmlns="{ns}"><available>true</available></vosi:availability>'
    )
    assert not parse_available(f'<availability xmlns="{ns}"><available>false</available></availability>')
    assert not parse_available("not xml")


def test_code_version_order(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GIT_COMMIT", raising=False)
    monkeypatch.delenv("RENDER_GIT_COMMIT", raising=False)
    assert main.code_version() == "dev"
    monkeypatch.setenv("RENDER_GIT_COMMIT", "0123456789abcdef")
    assert main.code_version() == "0123456"
    monkeypatch.setenv("GIT_COMMIT", "abc1234")
    assert main.code_version() == "abc1234"


def test_unknown_route_uses_error_contract() -> None:
    with TestClient(main.app) as client:
        resp = client.get("/api/does-not-exist")
    assert resp.status_code == 404
    body = resp.json()
    assert body["error"]["code"] == "NOT_FOUND"
    _validator("error.schema.json").validate(body)


@pytest.mark.network
def test_health_live_validates() -> None:
    with TestClient(main.app) as client:
        resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    print("live /api/health:", body)
    _validator("health.schema.json").validate(body)
