# Status

Updated Nov 8, 2026 · Owner: Rishabh · Update this whenever a deliverable lands or a [VERIFY] closes.

## Live URLs

| What | URL | State (Nov 8) |
|---|---|---|
| Website | https://planetes.xyz | Not live yet: the domain answers with a certificate for a different name. Add it in Vercel (docs/RUNBOOK.md) |
| Website fallback | Vercel default URL | Not recorded in the repo yet; add it here |
| API | Render service URL + `/api/health` | Not recorded in the repo yet; add it here |
| Repo | https://github.com/nova-rishabh/Planetes | Public |

## Deliverables

| Code | Owner | State |
|---|---|---|
| D1.1 scaffold (repo, contracts, CI, `/api/health`, status badge) | Rishabh | **Done** Nov 8 |
| Light theme (docs/09 palette C tokens) | Rishabh | **Done** Nov 8: `web/src/styles/tokens.css`, page uses tokens only |
| D2.1 access · D3.1 resolve · D4.1/D4.3 prototypes | Tirth · Shivaansh · Shimaya | Phase 0, due G0 (Mon 9, 10:30) |
| All other D-codes (docs/06) | — | Not started |
| Validation V1–V10 | — | Not run (docs/VALIDATION.md) |

## Next

1. G0 (Mon 9, 10:30): real frames for at least one benchmark; site live on Vercel and API on Render.
2. Point planetes.xyz at Vercel; record the Vercel and Render URLs above.
3. Phase 1: D1.2 API jobs + D1.3 player; D2.1/D2.2; D3.1/D3.2; D4.1.
4. Team vote on the palette (docs/09 §3; C is the default).

## Open [VERIFY] items

| Doc | Item |
|---|---|
| 02 §2 | Cloudflare R2 free-tier storage and request limits |
| 02 §2 | Camber: how jobs launch and who can run them |
| 02 §4.10 | MJy/sr → µJy: IRSA solid-angle pixel map vs a constant |
| 02 §5 | TAP table and column names for QR3 |
| 02 §7 | Exact unWISE HiPS ID in Aladin |
| 02 §7, 06 | SPHEREx spacecraft-position header keys (for JPL SBIdent) |
| 02 §11 | Licences: spxquery, obsutils `spherex`, IRSA tutorials, Aladin Lite v3 (GPL-3 expected), Gagné et al. templates (terms) |
| 04 §1 | ε Indi Ba/Bb position (check against SIMBAD) |
| 04 §1 | R Draconis epoch coverage near the north ecliptic pole |
| 01 §10 | Global deadline under Universal Event (confirm Nov 13) |
