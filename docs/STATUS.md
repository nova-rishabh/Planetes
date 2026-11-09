# Status

Updated Nov 8, 2026 · Owner: Rishabh · Update this whenever a deliverable lands or a [VERIFY] closes. Rishabh's account setup checklist: docs/RISHABH_GUIDE.md.

## Live URLs

| What | URL | State (Nov 8) |
|---|---|---|
| Website | https://planetes.divergit.com | Not live yet (no DNS record). Steps in docs/RUNBOOK.md |
| Website fallback | https://web-gamma-flame-16.vercel.app | Live (HTTP 200) |
| API | https://planetes-api.onrender.com/api/health | Live: `status ok`, `irsa_tap ok`, `code_version 08b009b` (deploys from `main`) |
| Repo | https://github.com/nova-rishabh/Planetes | Public |

## Deliverables

| Code | Owner | State |
|---|---|---|
| D1.1 scaffold (repo, contracts, CI, `/api/health`, status badge) | Rishabh | **Done** Nov 8; both services deploy from `main` |
| Light theme (docs/09 palette C tokens) | Rishabh | **Done** Nov 8; palette C locked by team vote Nov 9 |
| D2.1 access (Tirth) | Tirth | PR #1 open Nov 9: script plots **simulated** cutouts, no IRSA query yet; changes requested |
| D2.1 access · D3.1 resolve · D4.1/D4.3 prototypes | Tirth · Shivaansh · Shimaya | Phase 0, due at the G0 meeting (Mon 9, 10:00) |
| D1.2 API (part 1) | Rishabh | **In progress** Nov 9: cache (local + GCS), job queue, `POST /timelapse`, `/jobs/{id}`, `/frames`. Live time-lapse needs D2.1 + D2.2 merged, then wiring in `api/timelapse.py` |
| All other D-codes (docs/06) | — | Not started |
| Validation V1–V10 | — | Not run (docs/VALIDATION.md) |

## Open items (PM_PLAYBOOK §7; tick when done)

- [ ] Send the group message (palette vote + docs update) with `docs/assets/planetes-palettes-light.png` attached
- [ ] Tirth: turn on "looking for team members", approve join requests, transfer Team Owner to Rishabh (private message not sent yet)
- [ ] Everyone: create Space Apps accounts, register for 2026, join Team Planetes via the direct link
- [ ] Team page About text says "starry discoveries": change it (no discovery claims) once Rishabh is owner
- [x] Palette vote: **C "Plate Archive" chosen** (Nov 9); locked in docs/09, already in `tokens.css`
- [ ] Domain planetes.divergit.com: add to Vercel, CNAME at the divergit.com DNS, then add to Render `ALLOWED_ORIGINS`
- [ ] Google Cloud Storage cache: bucket, service account, lifecycle, budget alert (docs/RUNBOOK.md)
- [x] Camber dropped (Nov 9): bakes run in GitHub Actions, validation on laptops
- [ ] GitHub: add teammates as collaborators (Write) and protect `main` (docs/RISHABH_GUIDE.md)
- [ ] Science [VERIFY] at Monday standup (Shimaya, Shivaansh): is `pm_ra_masyr` multiplied by cos δ (Gaia convention)? Does `bands_covered` mean detector numbers 1–6?
- [ ] G0 meeting Mon 9, 10:00: each person shows a working notebook/plot (Phase 0 tasks in docs/05)
- [ ] Nov 13: read the Resources tab and Submission/Judging guides; update docs/01 and docs/08

## Next

1. G0 meeting (Mon 9, 10:00): real frames for at least one benchmark.
2. Phase 1 (to G1 Tue 10, 23:00): D1.2 API jobs + D1.3 player; D2.1/D2.2; D3.1/D3.2; D4.1.

## Open [VERIFY] items

| Doc | Item |
|---|---|
| 02 §2 | Google Cloud trial credit expiry date |
| 02 §4.10 | MJy/sr → µJy: IRSA solid-angle pixel map vs a constant |
| 02 §5 | TAP table and column names for QR3 |
| 02 §7 | Exact unWISE HiPS ID in Aladin |
| 02 §7, 06 | SPHEREx spacecraft-position header keys (for JPL SBIdent) |
| 02 §11 | Licences: spxquery, obsutils `spherex`, IRSA tutorials, Aladin Lite v3 (GPL-3 expected), Gagné et al. templates (terms) |
| 04 §1 | ε Indi Ba/Bb position (check against SIMBAD) |
| 04 §1 | R Draconis epoch coverage near the north ecliptic pole |
| 01 §10 | Global deadline under Universal Event (confirm Nov 13) |
