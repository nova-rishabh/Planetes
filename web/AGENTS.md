# Web rules (Next.js)
- Next.js App Router, static export. TypeScript strict. Types come from contracts/ (generated).
- Same code path for baked files and live API (only base URL differs).
- All view state lives in the URL (see docs Data Contract §2). /embed reuses the same components.
- Accessibility: keyboard controls, focus states, alt text, contrast >= 4.5:1. No Inter font.
