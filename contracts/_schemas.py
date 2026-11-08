"""Shared helpers for contracts/generate.py and contracts/validate.py (stdlib + jsonschema only)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

CONTRACTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = CONTRACTS_DIR.parent
BASE_ID = "https://github.com/nova-rishabh/Planetes/contracts/"


def schema_files() -> list[Path]:
    return sorted(CONTRACTS_DIR.glob("*.schema.json"))


def load_schemas() -> dict[str, dict[str, Any]]:
    """Return {file name: schema} for every contracts/*.schema.json."""
    return {p.name: json.loads(p.read_text(encoding="utf-8")) for p in schema_files()}


def registry():
    """A `referencing` registry holding every schema under its $id, for jsonschema validation."""
    from referencing import Registry, Resource

    resources = []
    for name, schema in load_schemas().items():
        if schema.get("$id") != BASE_ID + name:
            raise SystemExit(f"{name}: $id must be {BASE_ID + name!r}")
        resources.append((schema["$id"], Resource.from_contents(schema)))
    return Registry().with_resources(resources)
