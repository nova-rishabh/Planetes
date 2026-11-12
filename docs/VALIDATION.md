# Validation results

Tests are defined in docs/04-Science-Validation.md §7. Fill a row only with real results.

| ID | Test | Result | Pass? | Evidence |
|---|---|---|---|---|
| V1 | Barnard's Star proper motion | μ = 10.56 ± 0.33″/yr, PA 355.1° vs Gaia 10.39″/yr, 355.6° (1.6 %, 0.4°) | ✅ PASS (with Gaia epoch) | Shivaansh, Nov 12: Gaia DR3 2016.0 position + brightest pixel in 4 real frames (D3/D6, MJD 60902–61271), `motion.fit_proper_motion`. Re-run by Rishabh: same result. SPHEREx frames alone give 13.9 ± 3.0″/yr at 17.7° (whole-pixel positions on a saturated core), so the Gaia epoch carries this; sub-pixel centroids needed |
| V2 | ε Indi B proper motion | not run yet | | First attempt (Nov 12) used the baked `target_xy`, which is the Gaia-predicted position, not a measurement, so it was dropped. Needs positions measured in the SPHEREx frames |
| V3 | WISE 0855 detection & motion | not run yet | | |
| V4 | Our photometry vs IRSA tool | not run yet | | |
| V5 | Brown-dwarf typing | not run yet | | |
| V6 | Known asteroids | not run yet | | |
| V7 | Thermometer | not run yet | | |
| V8 | Variables | not run yet | | |
| V9 | False-alarm control | not run yet | | |
| V10 | Reproducibility | not run yet | | |
