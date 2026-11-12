# Validation results

Tests are defined in docs/04-Science-Validation.md §7. Fill a row only with real results.

| ID | Test | Result | Pass? | Evidence |
|---|---|---|---|---|
| V1 | Barnard's Star proper motion | μ = 10.56 ± 0.33″/yr, PA 355.1° vs Gaia 10.39″/yr, 355.6° (1.6 %, 0.4°) | ✅ PASS (with Gaia epoch) | Shivaansh, Nov 12: Gaia DR3 2016.0 position + brightest pixel in 4 real frames (D3/D6, MJD 60902–61271), `motion.fit_proper_motion`. Re-run by Rishabh: same result. SPHEREx frames alone give 13.9 ± 3.0″/yr at 17.7° (whole-pixel positions on a saturated core), so the Gaia epoch carries this; sub-pixel centroids needed |
| V2 | ε Indi B proper motion | not run yet | | First attempt (Nov 12) used the baked `target_xy`, which is the Gaia-predicted position, not a measurement, so it was dropped. Needs positions measured in the SPHEREx frames |
| V3 | WISE 0855 detection & motion | not run yet | | |
| V4 | Our photometry vs IRSA tool | not run as defined yet | | Interim cross-check (Nov 12): isolated 2MASS stars in Barnard cutouts, our flux / 2MASS = 0.96 and 0.99 (J 11.74). The IRSA-tool comparison on 3 unsaturated stars is still to do |
| V5 | Brown-dwarf typing | ε Indi B typed T3 (unresolved T1+T6 pair); distance 2.55–3.69 pc vs 3.64 pc from Gaia parallax | ✅ PASS | Rishabh, Nov 12: 304 of 445 real SPHEREx points (QR2+QR3, D1–D6), `typing.spectrum_opinion`, SpeX standards + Dupuy & Liu 2012; baked in `web/public/data/targets/epsindib/spectrum.json` |
| V6 | Known asteroids | cut | — | D3.4 known asteroids cut on Nov 12 (docs/DECISIONS.md) |
| V7 | Thermometer | cut | — | D4.2 thermometer cut on Nov 12 (docs/DECISIONS.md) |
| V8 | Variables | not run yet | | |
| V9 | False-alarm control | not run yet | | |
| V10 | Reproducibility | not run yet | | |
