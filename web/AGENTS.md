# Web rules (Next.js)
- Next.js App Router, static export. TypeScript strict. Types come from contracts/ (generated).
- Same code path for baked files and live API (only base URL differs).
- All view state lives in the URL (see docs Data Contract §2). /embed reuses the same components.
- Accessibility: keyboard controls, focus states, alt text, contrast >= 4.5:1. No Inter font.

<!-- BEGIN:nextjs-agent-rules -->

## This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->
