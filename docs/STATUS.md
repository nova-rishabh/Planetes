# Status

Updated Nov 13, 2026, 01:30 IST · Owner: Rishabh · Update this whenever a deliverable lands or a [VERIFY] closes. Rishabh's account setup checklist: docs/RISHABH_GUIDE.md.

## Live URLs

| What | URL | State |
|---|---|---|
| Website | https://planetes.divergit.com | **Live** Nov 9 (HTTP 200 via Vercel); API CORS allows it |
| Website fallback | https://web-gamma-flame-16.vercel.app | Live (HTTP 200) |
| API | https://planetes-api.onrender.com/api/health | Live: `status ok`, `irsa_tap ok`, deploys from `main` |
| Repo | https://github.com/nova-rishabh/Planetes | Public |

## Deliverables

Full list with owners and hours: docs/REMAINING_WORK.md. Step plan: docs/IMPLEMENTATION_PLAN.md.

| Code | Owner | State |
|---|---|---|
| D1.1 scaffold, D1.2 API, D1.3 player | Rishabh | **Done** (live) |
| D1.4 modes + D2.3 stacks/difference/colour | Tirth (code), Rishabh (integration, bake) | **In PR #20 + #25**: baked for all 5 benchmarks from real DR1/QR3 frames |
| D1.5 Two Opinions panel, Validation, About | Rishabh | Done; verdicts baked in **PR #23** (spectrum opinion; motion pending D3.3) |
| D1.6 guided tour + Planet X UI | Rishabh | Planet X **live** (#15); tour in **PR #22** |
| D1.7 sonified blink + a11y | Rishabh | Sound mode in **PR #22**; a11y pass to do |
| D1.8 submission package | Rishabh | Draft updated (**PR #24**); final pass after the official guides (not out at 01:30 Nov 13) |
| Homepage redesign | Rishabh | **PR #21**: real-frame scroll story; viewer at /viewer |
| SPHEREx DR1 | Rishabh | **PR #25**: IRSA now lists DR1 + QR3, QR2 gone; main crashes on DR1 files until merged |
| D2.4 photometry, D2.5 quality | Tirth / Rishabh | Aperture photometry live; Tirth's PSF photometry kept as `psf_photometry.py`; quality report in #20 |
| D3.1 resolve, D3.2 overlays | Shivaansh | **Done** |
| D3.3 motion | Shivaansh | Fitter done; measured positions **reported done (ε Indi B 4.71″/yr vs 4.68), not pushed yet** |
| D3.4 known asteroids | Rishabh (code), Shivaansh (review, V6) | `known.py` on branch `rishabh/known-asteroids`; V6 running |
| D3.5 mover search | Shivaansh | Not started (lowest priority) |
| D4.1 spectrum, D4.3 typer | Rishabh | **Done**; typer now needs two of D1–D3 (RW Aur fix, #23) |
| D4.2 thermometer | Rishabh (from Amish's draft) | **Done** (#17); V7 needs real asteroid pairs |
| D4.4 verdict | Rishabh | Done; wired to the spectrum (#23) |
| D4.5 Planet X physics | Rishabh (from Amish's draft) | **Done** (#15), formula corrected |
| Validation | — | V1, V5 pass; V3 note (WISE 0855 blended); V4 interim; V6 interim (1 asteroid, 0.07 px); V7, V8, V9, V10 to run |

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
- [x] GitHub access: Shivaansh added Nov 11 (branch + PR into `main`). Others send PRs from their forks (Rishabh approves CI) or zips
- [ ] Science [VERIFY] (Role 4 lead, Shivaansh): is `pm_ra_masyr` multiplied by cos δ (Gaia convention)? Does `bands_covered` mean detector numbers 1–6?
- [ ] Nov 13: read the Resources tab and Submission/Judging guides; update docs/01 and docs/08

## Next

G2 Thu Nov 12, 22:00: stacks + difference (D2.3), overlays (D3.2), first spectrum (D2.4 + D4.1). G3 Fri Nov 13, 23:00: Two Opinions for the 5 benchmarks (needs D3.3 + D4.3) + Validation page; read the official Resources/Submission/Judging guides. Freeze Sat 14, 18:00. Submit Sun 15, 18:00.

Rishabh/agent: bake `opinions.json` once real opinions exist, bake stacks when D2.3 lands, review teammates' work, README + submission draft (doc 08).

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
