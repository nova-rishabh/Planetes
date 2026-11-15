"""Regenerate pydantic models and TypeScript types from contracts/*.schema.json.

Both generators handle cross-file $refs poorly, so the schemas are first bundled into one
temporary schema whose $defs hold every top-level shape (by title) and every nested $def
(by name; names must be unique across files). Then:

  datamodel-codegen -> pipeline/src/planetes/contracts.py
  json2ts           -> web/src/types/contracts.ts   (needs `npm ci` in web/)

Run via `make contracts`.
"""

from __future__ import annotations

import copy
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _schemas import REPO_ROOT, load_schemas

PY_OUT = REPO_ROOT / "pipeline" / "src" / "planetes" / "contracts.py"
TS_OUT = REPO_ROOT / "web" / "src" / "types" / "contracts.ts"
HEADER = "GENERATED, DO NOT EDIT. Source: contracts/*.schema.json. Regenerate with `make contracts`."


def bundle() -> dict[str, Any]:
    schemas = load_schemas()
    titles = {name: s["title"] for name, s in schemas.items()}
    defs: dict[str, Any] = {}

    def add(key: str, value: Any, origin: str) -> None:
        if key in defs:
            raise SystemExit(f"Duplicate definition name {key!r} (from {origin}); names must be unique.")
        defs[key] = value

    def rewrite(node: Any) -> Any:
        if isinstance(node, dict):
            out = {}
            for k, v in node.items():
                if k == "$ref" and isinstance(v, str):
                    file_part, _, frag = v.partition("#")
                    if frag:
                        if not frag.startswith("/$defs/"):
                            raise SystemExit(f"Unsupported $ref {v!r}")
                        out[k] = "#" + frag
                    else:
                        out[k] = f"#/$defs/{titles[file_part]}"
                else:
                    out[k] = rewrite(v)
            return out
        if isinstance(node, list):
            return [rewrite(x) for x in node]
        return node

    for name, schema in schemas.items():
        s = copy.deepcopy(schema)
        for key in ("$schema", "$id"):
            s.pop(key, None)
        for def_name, def_schema in s.pop("$defs", {}).items():
            add(def_name, rewrite(def_schema), name)
        if "type" in s:  # common.schema.json only holds $defs
            add(s["title"], rewrite(s), name)

    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "PlanetesContracts",
        "$defs": dict(sorted(defs.items())),
    }


def normalise_newlines(path: Path) -> None:
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    path.write_text(text, encoding="utf-8", newline="\n")


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)


def main() -> None:
    bundled = bundle()
    with tempfile.TemporaryDirectory() as tmp:
        bundle_path = Path(tmp) / "planetes_contracts.json"
        bundle_path.write_text(json.dumps(bundled, indent=2), encoding="utf-8")

        codegen = shutil.which("datamodel-codegen") or str(
            Path(sys.executable).parent / ("datamodel-codegen.exe" if os.name == "nt" else "datamodel-codegen")
        )
        run(
            [
                codegen,
                "--input",
                str(bundle_path),
                "--input-file-type",
                "jsonschema",
                "--output",
                str(PY_OUT),
                "--output-model-type",
                "pydantic_v2.BaseModel",
                "--target-python-version",
                "3.11",
                "--disable-timestamp",
                "--use-standard-collections",
                "--use-union-operator",
                "--field-constraints",
                "--use-double-quotes",
                "--enum-field-as-literal",
                "all",
                "--use-schema-description",
                "--use-field-description",
                "--strict-nullable",
                "--use-default",
                "--collapse-root-models",
                "--formatters",
                "builtin",
                "--custom-file-header",
                f"# {HEADER}",
            ]
        )
        normalise_newlines(PY_OUT)

        TS_OUT.parent.mkdir(parents=True, exist_ok=True)
        json2ts = REPO_ROOT / "web" / "node_modules" / ".bin" / ("json2ts.cmd" if os.name == "nt" else "json2ts")
        if not json2ts.exists():
            raise SystemExit("json2ts not found: run `npm ci` in web/ first.")
        run(
            [
                str(json2ts),
                "--input",
                str(bundle_path),
                "--output",
                str(TS_OUT),
                "--unreachableDefinitions",
                "--additionalProperties",
                "false",
                "--bannerComment",
                f"/* {HEADER} */",
            ]
        )
        normalise_newlines(TS_OUT)

    print(f"wrote {PY_OUT.relative_to(REPO_ROOT)} and {TS_OUT.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
