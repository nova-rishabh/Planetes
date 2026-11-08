"""Validate every JSON file under web/public/data against its contract (docs/03 §6).

A JSON file with no matching schema is an error, so new baked file types must get a schema first.
Passes (exit 0) when the folder holds no JSON files. Run via `make validate`.
"""

from __future__ import annotations

import fnmatch
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _schemas import BASE_ID, REPO_ROOT, registry

DATA_DIR = REPO_ROOT / "web" / "public" / "data"

# Path patterns relative to web/public/data (docs/03 §6) -> schema file.
RULES: list[tuple[str, str]] = [
    ("targets/*/timelapse_*.json", "timelapse_result.schema.json"),
    ("targets/*/spectrum.json", "spectrum_result.schema.json"),
    ("targets/*/overlays.json", "overlays.schema.json"),
    ("targets/*/opinions.json", "opinions.schema.json"),
]


def schema_for(rel: str) -> str | None:
    for pattern, schema in RULES:
        if fnmatch.fnmatchcase(rel, pattern):
            return schema
    return None


def main() -> int:
    from jsonschema import Draft202012Validator

    reg = registry()
    files = sorted(DATA_DIR.rglob("*.json")) if DATA_DIR.exists() else []
    failures = 0
    for path in files:
        rel = path.relative_to(DATA_DIR).as_posix()
        schema_name = schema_for(rel)
        if schema_name is None:
            print(f"FAIL {rel}: no contract maps to this file (add a schema and a rule in contracts/validate.py)")
            failures += 1
            continue
        schema = reg.contents(BASE_ID + schema_name)
        validator = Draft202012Validator(schema, registry=reg, format_checker=Draft202012Validator.FORMAT_CHECKER)
        errors = sorted(validator.iter_errors(json.loads(path.read_text(encoding="utf-8"))), key=str)
        if errors:
            failures += 1
            for err in errors[:20]:
                loc = "/".join(str(p) for p in err.absolute_path) or "(root)"
                print(f"FAIL {rel} at {loc}: {err.message}")
        else:
            print(f"ok   {rel} ({schema_name})")
    print(f"{len(files)} file(s) checked, {failures} failed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
