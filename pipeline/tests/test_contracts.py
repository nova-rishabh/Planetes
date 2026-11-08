"""Contract checks: every schema is valid draft 2020-12, refs resolve, and the generated models import."""

from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

CONTRACTS_DIR = Path(__file__).resolve().parents[2] / "contracts"
SCHEMA_FILES = sorted(CONTRACTS_DIR.glob("*.schema.json"))

# Every top-level shape required by docs/03 §3-§5, plus the shared definitions file.
EXPECTED = {
    "common",
    "error",
    "health",
    "job",
    "job_created",
    "opinions",
    "opinions_request",
    "overlays",
    "resolved",
    "spectrum_request",
    "spectrum_result",
    "timelapse_request",
    "timelapse_result",
}


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _registry() -> Registry:
    return Registry().with_resources((_load(p)["$id"], Resource.from_contents(_load(p))) for p in SCHEMA_FILES)


def test_all_expected_schemas_exist() -> None:
    assert {p.name.removesuffix(".schema.json") for p in SCHEMA_FILES} == EXPECTED


@pytest.mark.parametrize("path", SCHEMA_FILES, ids=lambda p: p.name)
def test_schema_is_valid_draft_2020_12(path: Path) -> None:
    schema = _load(path)
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["$id"].endswith("/" + path.name)
    Draft202012Validator.check_schema(schema)


def _refs(node: object) -> list[str]:
    if isinstance(node, dict):
        out = [node["$ref"]] if isinstance(node.get("$ref"), str) else []
        return out + [r for v in node.values() for r in _refs(v)]
    if isinstance(node, list):
        return [r for v in node for r in _refs(v)]
    return []


@pytest.mark.parametrize("path", SCHEMA_FILES, ids=lambda p: p.name)
def test_every_ref_resolves(path: Path) -> None:
    schema = _load(path)
    resolver = _registry().resolver(base_uri=schema["$id"])
    for ref in _refs(schema):
        resolver.lookup(ref)  # raises if the target does not exist


@pytest.mark.parametrize("path", [p for p in SCHEMA_FILES if p.name != "common.schema.json"], ids=lambda p: p.name)
def test_responses_require_schema_version(path: Path) -> None:
    schema = _load(path)
    assert schema["properties"]["schema_version"] == {"$ref": "common.schema.json#/$defs/SchemaVersion"}
    is_request = path.name.endswith("_request.schema.json")
    # docs/03 §1: schema_version is required on every response and baked file; requests may omit it.
    assert ("schema_version" in schema["required"]) is not is_request


def test_generated_models_import() -> None:
    contracts = importlib.import_module("planetes.contracts")
    for name in [
        "Health",
        "Resolved",
        "Job",
        "JobCreated",
        "TimelapseRequest",
        "TimelapseResult",
        "SpectrumRequest",
        "SpectrumResult",
        "OpinionsRequest",
        "Opinions",
        "Overlays",
        "Error",
        "Grid",
        "Epoch",
        "Frame",
        "Stretch",
        "FlagLegendItem",
        "Provenance",
        "SpectrumPoint",
    ]:
        assert hasattr(contracts, name), name


def test_generated_files_have_header() -> None:
    root = CONTRACTS_DIR.parent
    for rel in ["pipeline/src/planetes/contracts.py", "web/src/types/contracts.ts"]:
        first = (root / rel).read_text(encoding="utf-8").splitlines()[0]
        assert "GENERATED, DO NOT EDIT" in first, rel
