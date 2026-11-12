# Validation results

Tests are defined in docs/04-Science-Validation.md §7. Fill a row only with real results.

| ID | Test | Result | Pass? | Evidence |
|---|---|---|---|---|
| V1 | Barnard's Star proper motion | μ = 10.56 ± 0.33″/yr, PA 355.1° vs Gaia 10.39″/yr, 355.6° (1.6 %, 0.4°) | ✅ PASS (with Gaia epoch) | Shivaansh, Nov 12: Gaia DR3 2016.0 position + brightest pixel in 4 real frames (D3/D6, MJD 60902–61271), `motion.fit_proper_motion`. Re-run by Rishabh: same result. SPHEREx frames alone give 13.9 ± 3.0″/yr at 17.7° (whole-pixel positions on a saturated core), so the Gaia epoch carries this; sub-pixel centroids needed |
| V2 | ε Indi B proper motion | not run yet | | First attempt (Nov 12) used the baked `target_xy`, which is the Gaia-predicted position, not a measurement, so it was dropped. Needs positions measured in the SPHEREx frames |
| V3 | WISE 0855 detection & motion | not run yet | | Finding (Nov 12): a Gaia DR3 star (G 16.3) sits 5–9″ from WISE 0855 during the SPHEREx year, inside our 3-pixel measuring circle. Before the blend check, its light gave a false 1 mJy “spectrum”. Now all 256 points are rejected (blend, too faint or flagged), so the spectrum says “not measured” rather than showing the neighbour's light. Motion still to test |
| V4 | Our photometry vs IRSA tool | not run as defined yet | | Interim cross-check (Nov 12): isolated 2MASS stars in Barnard cutouts, our flux / 2MASS = 0.96 and 0.99 (J 11.74). The IRSA-tool comparison on 3 unsaturated stars is still to do |
| V5 | Brown-dwarf typing | ε Indi B typed T3 (unresolved T1+T6 pair); distance 2.55–3.69 pc vs 3.64 pc from Gaia parallax | ✅ PASS | Rishabh, Nov 12: 304 of 445 real SPHEREx points (QR2+QR3, D1–D6), `typing.spectrum_opinion`, SpeX standards + Dupuy & Liu 2012; baked in `web/public/data/targets/epsindib/spectrum.json` |
| V6 | Known asteroids | not passed yet (8 of 10 asteroids) | | Nov 13: JPL SBIdent from SPHEREx's own position (`known.py`, PR #27). Ten ecliptic fields, 25 real D1–D3 frames each (DR1 + QR3): 8 asteroids predicted at V ≤ 17.5 (10 detections); 7 found (9 detections) within 1 px at S/N ≥ 5, median offset 0.07 px, max 0.79 px. With 73 Klytia from the first run that makes 8 different asteroids. Needs more fields to reach 10; rows in `docs/evidence/v6_known_asteroids.csv` (PR #27) |
| V7 | Thermometer | not run yet | | D4.2 back in scope (Nov 12, DECISIONS). `thermal.py` built and model-tested (geometry, recovery of a model distance); V7 needs real D3/D6 pairs of ≥ 20 known asteroids from D3.4 |
| V8 | Variables | not run yet | | |
| V9 | False-alarm control | not run yet | | |
| V10 | Reproducibility | not run yet | | Attempted Nov 13 from a clean clone with an empty cache: IRSA TAP returned 503 (archive outage). Note: IRSA no longer lists QR2 (DR1 replaced it), so a re-bake can't be byte-identical; the test is now whether the type and distance hold on DR1 data |
