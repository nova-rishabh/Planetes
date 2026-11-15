# Run from the repo root. Uses the repo-local .venv if present, else `python` on PATH.
ifeq ($(OS),Windows_NT)
  VENV_PY := .venv/Scripts/python.exe
else
  VENV_PY := .venv/bin/python
endif
PYTHON ?= $(if $(wildcard $(VENV_PY)),$(VENV_PY),python)

.PHONY: contracts validate

## Regenerate pipeline/src/planetes/contracts.py and web/src/types/contracts.ts from contracts/*.schema.json
contracts:
	$(PYTHON) contracts/generate.py

## Validate every JSON file in web/public/data against its schema
validate:
	$(PYTHON) contracts/validate.py
