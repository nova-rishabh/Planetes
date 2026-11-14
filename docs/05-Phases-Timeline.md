# Planetes 05 — Phases & Timeline

Hackathon: NASA Space Apps 2026 · All times IST

**How it works:**

- **Every phase ends with a deployed site we could submit as-is.** If time runs out, we submit the last finished phase.
- Daily tasks are **not** in this doc. Rishabh posts each person's tasks every night based on that day's progress.
- Deliverable codes (D1.x … D4.x) are defined in doc 06.

## At a glance

| Phase | Order | Goal | Gate to pass |
| --- | --- | --- | --- |
| **0 · Prove it** (light, Diwali) | Step 1: start, ends at G0 | Each person proves their data/tool works on real SPHEREx data | G0: real frames for ≥1 benchmark; repo + AGENTS.md + contracts v1; “hello” site live on Vercel and API live on Render |
| **1 · Live time-lapse MVP** | Step 2: after G0, ends at G1 | The challenge's core: coordinates in → SPHEREx “little video” out | G1: any coordinates + 5 benchmarks play as aligned time-lapses with flags and metadata → **first submittable version** |
| **2 · Power features** | Step 3: after G1, ends at G2 | Stacks, difference, colour, FOV, overlays, URL/embed, spectra on the fly, proper motions | G2: every official “consideration” (C1–C9 in doc 01) works on the benchmarks |
| **3 · Two Opinions** | Step 4: after G2, ends at G3 | Our differentiator + Validation page | G3: verdict panel live for benchmarks + validation set; V1–V8 results shown |
| **Buffer A** | After G3, before the wow layer | Catch up. **The official Resources tab + Submission/Judging guides come out around now** → adapt | Everything in G3 done; doc 01 re-checked against the Resources tab |
| **4 · Wow layer** (only if G3 passed) | Second-to-last day, until the freeze | Guided tour, Planet X Reality Check, known-asteroid overlay, mover search, sonified blink | An item ships only if finished and tested |
| **5 · Ship** | From the freeze to the deadline | Freeze, demo video, README, References, submission | **Internal deadline: 18:00 IST on the last day** (official deadline: confirm) |

**Buffer:** \~16 hours before the wow layer, plus everything between our internal and the official deadline (about 30% of the remaining time).

**Hosting (decided):** website on **Vercel** (free), API on **Render Starter** (team credits, no sleep) from day one.

## Phase 0 · Prove it (ends at G0)

Light work for the holiday: about 2–3 hours each.

- **Rishabh:** GitHub repo, `AGENTS.md` (doc 07), `contracts/` v1 (doc 03), Next.js shell and FastAPI “hello” deployed (web on Vercel, API on Render via `render.yaml`). (D1.1 start)
- **Tirth:** TAP query + cutouts for Barnard's Star at its **propagated** position; list of frames (obs ID, date, detector, wavelength at the star); 6 frames rendered side by side. (D2.1 start)
- **Shivaansh:** `resolve` prototype: name → position + proper motion (SIMBAD/Gaia), propagated to any date; table for the 5 benchmarks with sources. (D3.1 start)
- **Shimaya:** `sbpy` NEATM + reflected model at 1.5/2.5/3.5/5.2 AU, plot TR (D6/D3 ratio) vs r; locate the SPHEREx brown-dwarf templates and their terms. (D4.1/D4.3 start)
- **G0 (10:00 on the day after Phase 0):** each shows a working notebook/plot. **Decision:** confirm QR3 vs QR2 table names; confirm the thermometer is worth pursuing.

## Phase 1 · Live time-lapse MVP (G0 to G1)

- **Tirth:** D2.1 access (TAP, cutouts, retries, cache, QR3→QR2) + D2.2 frame processing (zodi, flags, wavelength, reprojection to a common north-up grid, stretch, WebP).
- **Shivaansh:** D3.1 resolve + proper-motion propagation wired into the API; D3.2 Gaia/AllWISE overlay data (positions per frame date).
- **Shimaya:** D4.1 spectrum extraction prototype (reuse xcavation), checked against IRSA's tool for one unsaturated star (V4 setup); flag legend in plain language.
- **Rishabh:** D1.2 API jobs (`/timelapse`, `/jobs`, `/frames`) + D1.3 player (play/step/scrub/blink, frame metadata, flag overlay) + coordinate input + benchmark buttons + bake workflow for the 5 benchmarks.
- **G1 (23:00 on the last day of Phase 1):** live link; typed coordinates produce an aligned time-lapse; the 5 benchmarks load from baked data; flags visible. **This version alone is a valid entry.**

## Phase 2 · Power features (G1 to G2)

- **Tirth:** D2.3 stacks / difference / sum / colour modes; D2.4 spectrum photometry in the API (with Shimaya).
- **Shivaansh:** D3.3 proper-motion fit (V1, V2, V3 motion part); D3.2 overlays in the player; Aladin context panel config (with Rishabh).
- **Shimaya:** D4.1 spectrum assembly + plot data (paired detectors, rejection reasons); V4 result.
- **Rishabh:** D1.4 FOV control, URL state + `/embed`, spectrum chart, mode switcher, Aladin Lite panel.
- **G2:** C1–C9 all demonstrable on the benchmarks; WISE 0855 visible in a D6 stack (or an honest note); Barnard's Star difference shows a +/− pair.

## Phase 3 · Two Opinions (G2 to G3)

- **Shimaya:** D4.3 brown-dwarf/star typer + photometric distance (V5); D4.4 verdict rules; D4.2 thermometer on a known-asteroid set if Phase 2 photometry allows (V7), otherwise documented fallback.
- **Shivaansh:** D3.4 known asteroids in frames (V6) and the asteroid rate → distance range; V9 false-alarm test.
- **Tirth:** photometry quality fixes from validation; D2.5 data-quality numbers; demo script draft (pitch owner).
- **Rishabh:** D1.5 Two Opinions panel + Validation page + About/How-it-works.
- **G3:** verdicts for ε Indi B, Barnard's Star (motion-only, saturation explained), WISE 0855, RW Aur, R Dra; Validation page live with V1–V8.

## Buffer A (after G3, before the wow layer)

- Read the official **Resources tab**, **Project Submission Guide** and **Judging & Awards Guide** (all due around now). Update docs 01 and 08 if anything changes (video length, required fields, AI-use disclosure).
- Fix whatever slipped. No new features.

## Phase 4 · Wow layer (second-to-last day, until the freeze), in priority order

1. Guided tour of the 5 benchmarks (Rishabh, D1.6)
2. Planet X Reality Check (Shimaya physics D4.5, Rishabh UI)
3. Known-asteroid overlay in any frame (Shivaansh D3.4 extension)
4. Mover search on 2–3 ecliptic fields + fake-object recovery test (Shivaansh D3.5, Tirth support)
5. Sonified blink + accessibility pass (Rishabh D1.7)

## Phase 5 · Ship (freeze to deadline)

- **18:00 on the second-to-last day:** feature freeze. Only bug fixes after this.
- **That night:** demo video (Tirth leads; doc 08 script); README, `docs/REFERENCES.md`, `docs/VALIDATION.md`, `docs/AI_USAGE.md`.
- **Final morning:** submission page filled from doc 08 checklist; every link tested from a phone and a laptop in incognito.
- **18:00 IST on the final day:** submitted. Everything after is buffer.

## Daily rhythm

- **10:30 standup, 10 minutes:** show working output (screen, plot, link), say what's next and name any blocker.
- **During the day:** push to GitHub at least once; one-line update in the group.
- **By 22:00:** push the day's work as a pull request.
- **By 23:30:** Rishabh posts tomorrow's tasks for each person.
- **Stuck > 2 hours:** post in the group immediately, with what you tried and the error text.

## Cut rules (decided in advance)

- A gate slips > 12 h → cut the lowest-priority item of the next phase. Never cut validation.
- Order of cuts if needed: sonification → mover search → known-asteroid overlay → thermometer (keep typer) → colour mode → Aladin panel.
- **Never cut:** coordinate input, time-lapse, flags, stacks/difference, URL params, spectrum on the fly, the 5 benchmarks.
- IRSA down → keep building on cached data. Nothing in the demo depends on a live call.

## Definition of done (any deliverable)

- [ ] Code merged by pull request (not just a notebook)
- [ ] Output validates against `contracts/`
- [ ] One screenshot/plot on **real** SPHEREx data in the PR
- [ ] Tests added/passing (`pytest` or Playwright)
- [ ] Owner has fact-checked the science (doc 04)
- [ ] Sources and AI tools used added to `docs/REFERENCES.md` and `docs/AI_USAGE.md`
