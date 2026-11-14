# Status

Owner: Rishabh · Update this whenever a deliverable lands or a [VERIFY] closes. Rishabh's account setup checklist: docs/RISHABH_GUIDE.md.

## Live URLs

| What | URL | State |
|---|---|---|
| Website | https://planetes.divergit.com | **Live** (HTTP 200 via Vercel); API CORS allows it |
| Website fallback | https://web-gamma-flame-16.vercel.app | Live (HTTP 200) |
| API | https://planetes-api.onrender.com/api/health | Live: `status ok`, `irsa_tap ok`, deploys from `main` |
| Repo | https://github.com/nova-rishabh/Planetes | Public |

## Deliverables

Full list with owners and hours: docs/REMAINING_WORK.md. Step plan: docs/IMPLEMENTATION_PLAN.md.

| Code | Owner | State |
|---|---|---|
| D1.1 scaffold, D1.2 API, D1.3 player | Rishabh | **Done** (live) |
| D1.4 modes + D2.3 stacks/difference/colour | Tirth (code), Rishabh (integration, bake) | **Done** (live): baked for all 5 benchmarks from real DR1/QR3 frames |
| D1.5 Two Opinions panel, Validation, About | Rishabh | **Done** (live); spectrum opinion baked, motion pending D3.3; saturated targets say "Can't tell: saturated" |
| D1.6 guided tour + Planet X UI | Rishabh | **Done** (live): tour starts from the homepage, plays and blinks real frames |
| D1.7 sonified blink + a11y | Rishabh | Sound mode **live**; a11y pass to do |
| D1.8 submission package | Rishabh | `docs/SUBMISSION.md` follows the official form; needs the demo link (Tirth) |
| Homepage redesign | Rishabh | **Done** (live): real-frame story; viewer at /viewer |
| SPHEREx DR1 | Rishabh | **Done**: reads DR1 + QR3 |
| D2.4 photometry, D2.5 quality | Tirth / Rishabh | Aperture photometry live; Tirth's PSF photometry kept as `psf_photometry.py`; quality report live |
| D3.1 resolve, D3.2 overlays | Shivaansh | **Done** |
| D3.3 motion | Shivaansh | Fitter done; measured positions **reported done (ε Indi B 4.71″/yr vs 4.68), not pushed yet** |
| D3.4 known asteroids | Rishabh (code), Shivaansh (review) | **Done**; V6 passed |
| D3.5 mover search | Shivaansh | Not started (lowest priority) |
| D4.1 spectrum, D4.3 typer | Rishabh | **Done**; typer needs two of D1–D3 |
| D4.2 thermometer | Rishabh (from Amish's draft) | **Done**; V7 needs D3/D6 pairs of 20 real asteroids |
| D4.4 verdict | Rishabh | **Done**; wired to the spectrum |
| D4.5 Planet X physics | Rishabh (from Amish's draft) | **Done**, formula corrected |
| Validation | — | V1, V5, V6, V8, V10 pass; V3, V4, V7 in progress; V2 needs D3.3; V9 running |

## Open items (PM_PLAYBOOK §7; tick when done)

- [ ] Send the group message (palette vote + docs update) with `docs/assets/planetes-palettes-light.png` attached
- [x] Team Owner transferred to Rishabh
- [ ] Everyone: create Space Apps accounts, register for 2026, join Team Planetes via the direct link
- [ ] Rishabh: change the team page About text ("starry discoveries" → no discovery claims)
- [x] Palette vote: **C "Plate Archive" chosen**; locked in docs/09, already in `tokens.css`
- [x] Domain planetes.divergit.com live, Render `ALLOWED_ORIGINS` set
- [x] Google Cloud Storage cache: project `planetes-514208`, key in Render
- [x] Camber dropped: bakes run in GitHub Actions, validation on laptops
- [x] GitHub: `main` protected (PR + green CI; admin bypass)
- [x] GitHub access: Shivaansh added (branch + PR into `main`). Others send PRs from their forks (Rishabh approves CI) or zips
- [ ] Science [VERIFY] (Role 4 lead, Shivaansh): is `pm_ra_masyr` multiplied by cos δ (Gaia convention)? Does `bands_covered` mean detector numbers 1–6?
- [ ] Read the Resources tab and Submission/Judging guides; update docs/01 and docs/08

## Next

Next gate G2: stacks + difference (D2.3), overlays (D3.2), first spectrum (D2.4 + D4.1). Then G3: Two Opinions for the 5 benchmarks (needs D3.3 + D4.3) + Validation page; read the official Resources/Submission/Judging guides. Then freeze (18:00 on the second-to-last day), then submit (18:00 on the final day).

Rishabh/agent: bake `opinions.json` once real opinions exist, bake stacks when D2.3 lands, review teammates' work, README + submission draft (doc 08).

## Open [VERIFY] items

| Doc | Item |
|---|---|
| 02 §2 | Google Cloud trial credit expiry date |
| 02 §4.10 | MJy/sr → µJy: IRSA solid-angle pixel map vs a constant |
| 02 §7 | SPHEREx and unWISE HiPS (none on ESASky; CDS was down at the time). Sky map images now come from ESASky and were seen working |
| 02 §7, 06 | SPHEREx spacecraft-position header keys (for JPL SBIdent) |
| 02 §11 | Licences: spxquery, obsutils `spherex`, IRSA tutorials, Gagné et al. templates (terms). Aladin Lite done (LGPL-3/GPL-3, loaded unbundled) |
| 04 §1 | WISE 0855 and RW Aur positions come from SIMBAD (epoch J2000, no Gaia id): check against AllWISE |
| 04 §1 | R Draconis epoch coverage near the north ecliptic pole |
| 01 §10 | Global deadline under Universal Event (to confirm) |
