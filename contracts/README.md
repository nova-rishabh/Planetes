# contracts/

JSON Schemas for every API response and baked file. Source: docs/03-Data-Contract-API.md (§4–§6).
Built in deliverable D1.1 (Rishabh). pydantic models and TypeScript types are generated from these; never hand-edit generated files.

## Files
- `<shape>.schema.json`: one per top-level shape in docs/03 §3-§5 (Health, Resolved, Job, JobCreated,
  TimelapseRequest/Result, SpectrumRequest/Result, OpinionsRequest, Opinions, Overlays, Error).
  Nested shapes live in each file's `$defs`; `common.schema.json` holds shared definitions only.
- `schema_version` (`"1.0"`) is required on every response/baked shape and optional on request bodies.
- `generate.py` (`make contracts`): bundles the schemas, then writes `pipeline/src/planetes/contracts.py`
  (datamodel-code-generator) and `web/src/types/contracts.ts` (json-schema-to-typescript).
  `$def` names must be unique across files.
- `validate.py` (`make validate`): validates `web/public/data/**/*.json`; a file with no mapped schema fails.
