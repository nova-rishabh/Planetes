# What's left — Planetes

Owner: Rishabh · Tick items here as they land (and update docs/STATUS.md).

**Target: everything below finished before the last two days.** Those two days then go to polish, the video
and the submission only. Internal deadline: 18:00 IST on the final day; the official Submission and Judging
guides come out around now and may change the video length or form fields.

Split is a proposal (Rishabh decides). Each person has about 8–9 focused hours, sized for working with AI tools.

---

## 1. Already done

| Area | What works today |
|---|---|
| Website | Live at https://planetes.divergit.com: coordinate input, 5 benchmarks, time-lapse player (play/step/blink/scrub, flags, catalogue stars), spectrum chart, About, Validation, Planet X calculator |
| API | Live on Render: time-lapse, spectrum, opinions, resolve, overlays, jobs |
| Data | All 5 benchmarks baked: time-lapse frames, catalogue stars, spectra |
| Science | Resolve (D3.1), overlays (D3.2), motion fitter (D3.3 part 1), spectrum layer (D4.1), typer (D4.3), verdict rules (D4.4), thermometer model (D4.2), Planet X physics (D4.5), quality report (D2.5, in PR #16) |
| Validation | V1 pass, V5 pass (ε Indi B typed T3 at 2.6–3.7 pc vs 3.64 pc) |

## 2. What's left, by priority

🔴 = needed to submit well · 🟡 = adds to the win · 🟢 = only if time

| # | Item | Pri | Owner | Hours | Done when | Waits on |
|---|---|---|---|---|---|---|
| 1 | **D3.3 measured positions** + V2 (ε Indi B motion) | 🔴 | Shivaansh | 5 | PR "D3.3 – measured positions & motion fit": total within 15 % of 4.68″/yr, SPHEREx-only number reported | — |
| 2 | **Two Opinions verdicts for the 5 benchmarks** (`opinions.json` baked, panel shows real verdicts) | 🔴 | Rishabh | 2 | Panel shows Agree / Disagree / Can't tell with reasons on all 5 | #1 |
| 3 | **Homepage redesign**: animated scroll story (real frames blinking, the 1930 blink-comparator idea), better first impression | 🔴 | Rishabh | 6 | Looks finished on phone and laptop; reduced-motion works; docs/09 rules kept | — |
| 4 | **Merge Tirth's stacks/difference** (PR #16 via integration branch) | 🔴 | Rishabh | 1 | Merged, CI green | — |
| 5 | **Stacks/difference fast enough + screenshot** on real Barnard frames (a 6-frame job took > 5 min) | 🔴 | Tirth | 3 | Job finishes in < 2 min; screenshot of stack + difference in PR | #4 |
| 6 | **Bake stacks/difference** for the 5 targets + mode switcher in the player | 🔴 | Rishabh | 2 | Switching modes on each benchmark shows real stacks | #5 |
| 7 | **SPHEREx DR1 support** (IRSA added a new release `spherex_dr1_*`; access.py only knows QR2/QR3 and crashes on DR1 files) | 🔴 | Rishabh | 2 | Contract + access accept DR1; live time-lapse works where DR1 exists | — |
| 8 | **Demo video**: 30 s and ~2 min cuts (docs/08 §3), English | 🔴 | Tirth | 5 | Public links play without login | #3 for final shots (first cut can start now) |
| 9 | **Pitch slides** (docs/08 §4) | 🔴 | Tirth | 2 | 6–8 slides, no NASA logo, real images only | — |
| 10 | **About page science fact-check** + the two open [VERIFY] questions (pm_ra × cos δ; `bands_covered` = detectors 1–6) | 🔴 | Role 4 (Amish) · backup Shivaansh | 1 | List of fixes sent; answers written in docs/STATUS.md | — |
| 11 | **Submission package**: read the official guides, finalise docs/SUBMISSION.md, README, checklist in docs/08 §6 | 🔴 | Rishabh | 2 | Every box in docs/08 §6 ticked | Official guides |
| 12 | **D3.4 known asteroids** + V6 (`known.py` drafted: JPL SBIdent from SPHEREx's own position in the FITS header) | 🟡 | Shivaansh (review + V6) · Rishabh (code) | 3 | ≥ 10 known asteroids matched within 1 px in real frames | — |
| 13 | **V7 thermometer** on real asteroid D3/D6 pairs from #12 | 🟡 | Role 4 (Amish) · backup Rishabh | 3 | ≥ 70 % of JPL distances inside our ranges, or an honest "not passed" with numbers | #12 |
| 14 | **V4 photometry vs IRSA's tool** on 3 unsaturated stars | 🟡 | Tirth | 2 | Ratios table in docs/VALIDATION.md | — |
| 15 | **V8 variables** (R Dra / RW Aur brightness changes) | 🟡 | Role 4 (Amish) · backup Tirth | 2 | Light curve plot + result row in VALIDATION | — |
| 16 | **V9 false-alarm control** (shuffled frames → no fake movers) | 🟡 | Shivaansh | 2 | ≤ 2 false movers per shuffled field | #1 |
| 17 | **V10 reproducibility** (re-bake one target from a clean checkout, same numbers) | 🟡 | Rishabh | 1 | Result row in VALIDATION | — |
| 18 | **Guided tour** (D1.6) | 🟡 | Rishabh | 2 | < 2 min tour over a benchmark | #3 |
| 19 | **Sonified blink + accessibility pass** (D1.7) | 🟢 | Rishabh | 2 | Lighthouse a11y ≥ 90; blink has sound toggle | — |
| 20 | **Mover search** (D3.5) on 2–3 ecliptic fields + fake-object recovery | 🟢 | Shivaansh | 3 | Recovery curve; candidates labelled honestly ("consistent with", never "discovered") | #1, #16 |
| 21 | **Team page + registration**: About text without discovery claims; everyone registered and joined; under-18s registered by a parent/guardian (Space Apps rule) | 🔴 | Tirth (page owner) + everyone | 0.5 | All 4 on Team Planetes; guardian step done | — |

## 3. Per person (balanced)

| Person | Items | ≈ Hours |
|---|---|---|
| **Rishabh** (with the agent doing most of the build) | 2, 3, 4, 6, 7, 11, 17, 18, 19 + code for 12 + all reviews/merges | 9 of your own (agent builds the rest) |
| **Tirth** | 5, 8, 9, 14, 21 | 12.5 (video is the big one; can spill into the second-to-last day) |
| **Shivaansh** | 1, 12 (V6), 16, 20 | 13 (1 first; 20 only if time) |
| **Role 4 (Amish)** | 10, 13, 15 | 6 (each has a named backup) |

## 4. Order and checkpoints (final build day)

1. **By 12:00:** #1 progress pushed (Shivaansh) · #4, #7 merged (Rishabh) · #10 sent (Amish) · video script draft (Tirth).
2. **By 18:00:** #1 merged → #2 baked · #5 merged → #6 baked · #3 first version live · #12 V6 run.
3. **End of day:** all 🔴 done; 🟡 as far as they go; VALIDATION page up to date; submission draft final except the video link.

**Critical path:** #1 → #2. The headline feature (Two Opinions) waits on Shivaansh's measured positions.

## 5. Rules for the last stretch

- Real data only; "consistent with", never "discovered/confirmed" (docs/04 §8).
- PR by the checkpoint with a real-data screenshot. Stuck > 2 h → post in the group.
- Cut order if late (docs/05): mover search → sonified blink → guided tour → V8. **Never cut** validation that's already running, the 5 benchmarks, or the verdicts.
- No AI attribution in commits/PRs/docs; AI use goes in docs/AI_USAGE.md only.
