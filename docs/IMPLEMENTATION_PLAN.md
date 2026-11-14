# Implementation plan — Rishabh's items (with the agent building)

Covers every item owned by Rishabh in docs/REMAINING_WORK.md (#2, #3, #4, #6, #7,
#11, #12 code, #17, #18, #19). Target: all done by the end of the final build day.

Working rules for every step: one PR per step, CI green, real-data screenshot in the PR, Rishabh approves each merge,
a DOC_UPDATES row for any doc change, no AI attribution outside docs/AI_USAGE.md.

---

## Order at a glance

| Step | Item | Order | Est. | Depends on |
|---|---|---|---|---|
| A | #4 Merge Tirth's D2.3–D2.6 (integration PR) | first | 1 h | — |
| B | #7 SPHEREx DR1 support | early on the final build day | 2 h | A (same files nearby) |
| C | #6 Bake stacks / difference / sum / colour for 5 targets | morning | 2 h | A, B, Tirth's speed fix (#5) or a smaller bake |
| D | #3 Homepage redesign (scroll story) + viewer polish | main block | 6 h | — (runs alongside C) |
| E | #12 Known asteroids: finish `known.py` + V6 run | afternoon | 2 h | B |
| F | #2 Two Opinions verdicts baked | as soon as D3.3 lands | 2 h | Shivaansh's D3.3 PR |
| G | #18 Guided tour | evening | 2 h | D |
| H | #17 V10 reproducibility | evening | 1 h | C |
| I | #19 Sonified blink + accessibility pass | night | 2 h | D |
| J | #11 Submission package | when the guides are out, then after | 2 h | everything above |

---

## A. Merge Tirth's work (PR #16) — integration PR

Branch `rishabh/integrate-tirth-d2` (already prepared locally in the `pr16wt` worktree).

1. Keep from Tirth: `stack.py`, `quality.py`, `api/timelapse.py` (stacks / difference / sum / colour modes), tests.
2. His photometry → `psf_photometry.py` (not used by the live spectrum yet); `photometry.py` and `spectrum.py` stay
   as in main (blend check, all frames, exposure-level `pair_id`, no silent drops).
3. Removed the `sys.path` hacks; ruff clean; `quality.py` labels pairs as `D3&D6` from the exposure-level ids.
4. Replace the outdated "views not built yet" test with a live (network-marked) stacks/difference test on Barnard.
5. Run: `pytest -q -m "not network"` (121 pass so far) and `make validate`.
6. Real-data check: run stacks + difference on Barnard D3 (needs B first, the live run hit a DR1 file). Screenshot.
7. Open PR "Integrate D2.3–D2.6 (Tirth)" crediting Tirth; close #16 with a thank-you comment linking it.

**Done when:** CI green, a real stack + difference image of Barnard in the PR.

## B. SPHEREx DR1 support

IRSA now lists a new release (`ivo://irsa.ipac/spherex_dr1_deep?…`, files under `ibe/data/spherex/dr1/…`).
`access.extract_release` raises on it.

1. Print first (AGENTS rule 2): one real DR1 cutout — all HDU names, FLAGS keys (MP_* or MSKN/MSKM), PSF extension
   and VERSION, spacecraft keys, WCS keys. Code only against what is printed.
2. Contracts: add `"DR1"` to the release enum (common schema) → `make contracts` (regenerates pydantic + TS).
3. `access.py`: `extract_release` returns `DR1` for `/dr1/` or `spherex_dr1`; the "same exposure" preference becomes
   DR1 > QR3 > QR2; `release="auto"` keeps all three; record the release on each frame.
4. `frames.py` / `photometry.py`: confirm flag and PSF handling works on the printed DR1 header (add a branch only if the
   keys differ).
5. Web: release label shows DR1; About/Validation text mentions DR1 where it lists QR2/QR3.
6. Tests: release parsing for all three URI forms; one network test that a DR1 cutout measures.
7. Docs: AGENTS gotchas line, docs/02 data section, DOC_UPDATES row.

**Done when:** live time-lapse works on a field with DR1 files; CI green.

## C. Bake stacks / difference / sum / colour

1. Extend `api/bake.py`: `--modes` writes `timelapse_stacks.json`, `timelapse_difference.json`, `timelapse_sum.json`,
   `timelapse_color.json` + frames for each target (the viewer already loads `timelapse_<mode>.json`).
2. If Tirth's speed fix (#5) is not in yet, bake with a capped frame count per epoch and say so in the notes field.
3. `make validate` → commit one target per commit → PR. Also add the modes to the GitHub "Bake benchmarks" workflow.
4. Check each mode on each benchmark in the browser; screenshot Barnard stack vs difference.

**Done when:** the mode switcher shows real images on all 5 benchmarks.

## D. Homepage redesign + viewer polish (the big one)

Concept: **"the blink comparator, reborn."** In 1930 Clyde Tombaugh found Pluto by flipping between two photographic
plates; Planetes does the same with every SPHEREx image. Keep docs/09 (palette C "Plate Archive", light paper,
dark sky plates, IBM Plex, orange only for things that move, no Inter, nothing AI-looking). Motion always shows
real data, never decoration.

Structure (new `/` landing; the tool moves to `/viewer`, all old links and `/embed` keep working via URL params):

1. **Hero:** a large dark plate playing the real Barnard's Star frames (baked WebPs), the star sliding; headline
   "Every SPHEREx image of one patch of sky, played as a time-lapse"; coordinate box + "Try Barnard's Star" button.
2. **Scroll story** (4 short scenes, scroll-driven, each pinned with one sentence):
   1. *Blink:* two real frames a year apart blink; an orange ring marks the star that moved (Tombaugh reference).
   2. *102 colours:* the same patch steps through detectors D1→D6 (0.75 → 5 µm); points fly into the spectrum chart.
   3. *Two Opinions:* motion card and spectrum card slide in and meet in the verdict (real ε Indi B numbers).
   4. *Planet X:* small orbit diagram; drag the planet outward, it fades below SPHEREx's depth (links to /planet-x).
3. **Benchmarks strip:** 5 cards with a real thumbnail each, one line on why it's there.
4. **Honesty strip:** what SPHEREx can't do (saturation, 6″ pixels, one-year baseline) + link to /validation.
5. **Footer:** data credits (IRSA/SPHEREx, Gaia, AllWISE, JPL), repo link, no NASA logo.

Viewer polish: plate with a frame timeline under it (dots per epoch, coloured by detector), smoother play/blink,
animated spectrum points on load, verdict card with a short reveal, loading skeletons instead of blank space,
mobile layout pass.

Tech: GSAP 3 + ScrollTrigger (or Motion), loaded only on the landing page; `prefers-reduced-motion` → static
frames and no scroll pinning; images from `web/public/data` only (real frames); no new fonts.

Process: take 4–5 references first (NYT/Guardian science interactives, The Pudding, Ciechanowski, Stripe Press,
ESASky) → build in the browser preview → screenshot on laptop + phone widths → Rishabh reviews before merge.

**Done when:** looks finished on phone and laptop; Lighthouse performance ≥ 80 on the landing; reduced-motion OK;
lint/typecheck/tests/build pass.

## E. Known asteroids (`known.py`) + V6

1. Run the drafted `known.py` on 30–40 real ecliptic frames (around RA 30°, Dec +12°, D1–D3): SBIdent with
   `xobs` = the header's X_SC…VZ_SC (geocentric ICRF, km, km/s). Print the real response field names first and
   confirm the rate units.
2. For predicted asteroids with V ≤ 17: measure the offset between prediction and the image peak/centroid.
3. V6 pass if ≥ 10 asteroids are matched within 1 px. Record numbers in docs/VALIDATION.md.
4. Tests: header → `xobs` string; SBIdent response parsing on a saved real response (stored as a test fixture).
5. PR in Shivaansh's area (`known.py`): say so in the PR; Shivaansh reviews.
6. Produces the real D3/D6 asteroid pairs that Amish needs for V7.

## F. Two Opinions verdicts baked

1. When D3.3 lands: implement `measure_motion(req)` in `api/opinions.py` with Shivaansh's `measure_positions` +
   fit; `measure_spectrum(req)` with `spectrum.build_spectrum` → `typing.spectrum_opinion` (stars/brown dwarfs) or
   `thermal.thermal_opinion` (moving objects); saturated flag from the points.
2. `api/bake.py --opinions` → `opinions.json` for the 5 targets; `make validate`.
3. Expected: ε Indi B Agree (T3, ~3 pc, normal speed); Barnard / R Dra / RW Aur Can't tell (saturated spectra);
   WISE 0855 Can't tell (blended). Whatever comes out is shown as it is.
4. Screenshot the panel for each target.

## G. Guided tour

A 5-stop overlay on the viewer (Barnard): plate → blink → flags → spectrum → verdict. Under 2 minutes, skippable,
keyboard accessible, remembered in localStorage (wrapped in try/catch).

## H. V10 reproducibility

Fresh clone → `pip install -e pipeline[dev]` → re-bake ε Indi B spectrum → compare `n_used`, type and distance with
the committed file. Result row in docs/VALIDATION.md.

## I. Sonified blink + accessibility

Web Audio: each frame's target brightness → pitch; a short tick on every blink; off by default, toggle in the player.
Accessibility: keyboard map for the player, ARIA labels, focus rings, colour contrast check; Lighthouse a11y ≥ 90.

## J. Submission package

1. Read the official Project Submission and Judging guides; update docs/01 and docs/08 (video length,
   fields, AI disclosure).
2. Finalise docs/SUBMISSION.md and README (live link, repo, how to run, data credits, licence, references).
3. Run the docs/08 §6 pre-submit checklist in an incognito window on phone and laptop.
4. Rishabh fills the form on the final day with the video link from Tirth.

---

## Risks

| Risk | Plan |
|---|---|
| D3.3 late → no real verdicts | F waits; the panel keeps honest "can't tell" with reasons; demo uses ε Indi B spectrum + motion fitter output |
| Stacks too slow to bake | Bake with a frame cap and say so in the notes; Tirth's speed fix later |
| DR1 headers differ | Print first; if FLAGS/PSF differ a lot, accept DR1 for time-lapse only and keep spectra on QR2/QR3 |
| Homepage overruns | Ship hero + scenes 1–2 first; scenes 3–4 and the tour only if time |
