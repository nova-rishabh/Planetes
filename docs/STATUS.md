# Status

Updated Nov 11, 2026 (after the 10 pm call) · Owner: Rishabh · Update this whenever a deliverable lands or a [VERIFY] closes. Rishabh's account setup checklist: docs/RISHABH_GUIDE.md.

## Live URLs

| What | URL | State |
|---|---|---|
| Website | https://planetes.divergit.com | **Live** Nov 9 (HTTP 200 via Vercel); API CORS allows it |
| Website fallback | https://web-gamma-flame-16.vercel.app | Live (HTTP 200) |
| API | https://planetes-api.onrender.com/api/health | Live: `status ok`, `irsa_tap ok`, deploys from `main` |
| Repo | https://github.com/nova-rishabh/Planetes | Public |

## Deliverables

| Code | Owner | State |
|---|---|---|
| D1.1 scaffold (repo, contracts, CI, `/api/health`, status badge) | Rishabh | **Done** Nov 8; both services deploy from `main` |
| Light theme (docs/09 palette C tokens) | Rishabh | **Done** Nov 8; palette C locked by team vote Nov 9 |
| D2.1 access + D2.2 frames/render | Tirth (fixes: Rishabh) | **Done** Nov 9: Tirth's PRs #2/#3 plus review fixes (flags, saturation, shared stretch, QR3 flag keys), merged via `rishabh/d2.2-review-fixes`. Live time-lapse works end to end (59 real D3 frames of Barnard in ~2.5 min) |
| D3.1 resolve | Shivaansh (fixes: Rishabh) | **Done** Nov 11: 5 benchmarks resolve (Gaia DR3 via IRSA for Barnard, ε Indi B, R Dra; SIMBAD for WISE 0855, RW Aur). Barnard 1.86" from its core in a real 2026 frame |
| D4.4 verdict engine | Rishabh (took over from Role 4) | **Built** Nov 11 (`verdict.py`, rules + tests). Needs real motion (D3.3) and spectrum (D4.1/D4.3/D4.2) opinions as input |
| D1.2 API (part 1) | Rishabh | **Live time-lapse wired** Nov 9: cache (local + GCS), job queue, `POST /timelapse` runs access → frames → render, `/jobs/{id}`, `/frames`. Single exposures only until D2.3 |
| D1.3 player (part 1) | Rishabh | **In progress** Nov 9: coordinate input, 5 benchmark buttons, canvas player (play/step/scrub/speed/loop, A/B blink, flags, target marker, metadata), URL state, `/embed`. All 5 benchmarks baked Nov 11 (`api/bake.py`), live Nov 12. Re-bake from GitHub Actions ("Bake benchmarks", docs/RUNBOOK.md) |
| D1.4/D1.5 spectrum chart + Two Opinions panel | Rishabh | **Built** Nov 9 against the contract; show "no baked … yet" until `spectrum.json` / `opinions.json` exist |
| D2.4 photometry → D2.3 stacks | Tirth | **In progress** Nov 11 (D2.4 first). Due for G2 Thu 12, 22:00 |
| D3.2 overlays → D3.3 motion fit | Shivaansh | **In progress** Nov 11 (zips) |
| D4.1 spectrum layer → D4.3 typer → D4.2 thermometer | New Role 4 lead (replaced Shimaya, who left Nov 11) | **Starting** Nov 11; also fact-checks `/about` |
| About page `/about` | Rishabh | **Live** Nov 11; needs Role 4 fact-check |
| All other D-codes (docs/06) | — | Not started |
| Validation V1–V10 | — | Not run (docs/VALIDATION.md) |

## Open items (PM_PLAYBOOK §7; tick when done)

- [ ] Send the group message (palette vote + docs update) with `docs/assets/planetes-palettes-light.png` attached
- [ ] Tirth: turn on "looking for team members", approve join requests, transfer Team Owner to Rishabh (private message not sent yet)
- [ ] Everyone: create Space Apps accounts, register for 2026, join Team Planetes via the direct link
- [ ] Team page About text says "starry discoveries": change it (no discovery claims) once Rishabh is owner
- [x] Palette vote: **C "Plate Archive" chosen** (Nov 9); locked in docs/09, already in `tokens.css`
- [x] Domain planetes.divergit.com live, Render `ALLOWED_ORIGINS` set (Nov 9)
- [x] Google Cloud Storage cache: project `planetes-514208`, key in Render (Nov 9)
- [x] Camber dropped (Nov 9): bakes run in GitHub Actions, validation on laptops
- [x] GitHub: `main` protected (PR + green CI; admin bypass), Nov 9
- [x] GitHub collaborators: dropped Nov 11 (no usernames shared). Teammates send PRs from their forks (Rishabh approves CI) or zips
- [ ] Science [VERIFY] (Role 4 lead, Shivaansh): is `pm_ra_masyr` multiplied by cos δ (Gaia convention)? Does `bands_covered` mean detector numbers 1–6?
- [ ] Nov 13: read the Resources tab and Submission/Judging guides; update docs/01 and docs/08

## Next

G2 Thu Nov 12, 22:00: stacks + difference (D2.3), overlays (D3.2), first spectrum (D2.4 + D4.1). G3 Fri Nov 13, 23:00: Two Opinions for the 5 benchmarks (needs D3.3 + D4.3) + Validation page; read the official Resources/Submission/Judging guides. Freeze Sat 14, 18:00. Submit Sun 15, 18:00.

Rishabh/agent: `/api/opinions` + `opinions.json` (empty with a reason until real opinions exist), bake stacks when D2.3 lands, review teammates' work, README + submission draft (doc 08).

## Open [VERIFY] items

| Doc | Item |
|---|---|
| 02 §2 | Google Cloud trial credit expiry date |
| 02 §4.10 | MJy/sr → µJy: IRSA solid-angle pixel map vs a constant |
| 02 §7 | SPHEREx and unWISE HiPS (none on ESASky; CDS was down Nov 9). Sky map images now come from ESASky and were seen working Nov 9 |
| 02 §7, 06 | SPHEREx spacecraft-position header keys (for JPL SBIdent) |
| 02 §11 | Licences: spxquery, obsutils `spherex`, IRSA tutorials, Gagné et al. templates (terms). Aladin Lite done (LGPL-3/GPL-3, loaded unbundled) |
| 04 §1 | WISE 0855 and RW Aur positions come from SIMBAD (epoch J2000, no Gaia id): check against AllWISE |
| 04 §1 | R Draconis epoch coverage near the north ecliptic pole |
| 01 §10 | Global deadline under Universal Event (confirm Nov 13) |
