---
description: Verify a deliverable before PR
---
1. Run `pytest -q` in pipeline/ and `npm run lint && npm run typecheck` in web/.
2. Run the module on one benchmark target with real data; save a screenshot/plot to docs/evidence/.
3. Validate outputs against contracts/ (`make validate`).
4. Summarise what changed and any [VERIFY] items still open.
