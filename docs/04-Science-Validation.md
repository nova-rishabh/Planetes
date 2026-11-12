# Planetes 04 — Science & Validation Brief

Nov 7, 2026 · v1.0 · Owner: Shimaya (science lead), with Shivaansh for motion. **Everything the app claims must trace back to this doc.**

**Rule for catalog numbers below:** they're here so we know what to expect. The code must **fetch the real values at build time** (SIMBAD/Gaia) and never hard-code them. Values marked **\[VERIFY\]** need a check against SIMBAD.

## 1. The five official test targets: what to expect

| Target | What it is | Position (J2000) | Motion | Distance | What SPHEREx should show |
| --- | --- | --- | --- | --- | --- |
| **Barnard's Star** | Red dwarf (M4V), 2nd-closest star system | 17h57m48.5s +04°41′36″ | \~10.4″/yr (fastest-moving star) | \~1.83 pc | Moves \~5″ per 6 months, \~15″ over the SPHEREx data so far (\~2.5 px). Visible in difference images. **Saturated** (far brighter than SPHEREx's limit), so use it for motion, not for spectra. Its position today is \~4.5′ from J2000; we must propagate. |
| **WISE 0855−0714** | Coldest known brown dwarf (Y dwarf, \~250 K) | 08h55m10.831s −07°14′42.53″ (as given in the challenge) | \~8.15″/yr | \~2.3 pc | Almost invisible below \~3.5 µm; emits mostly at 4–5 µm. Look in **detector-6 stacks**. Single frames may be too faint; stacking is the challenge's own tip. |
| **ε Indi Ba/Bb** | Pair of T dwarfs (T1 + T6) orbiting the star ε Indi A | \~22h04m10s −56°47′ **\[VERIFY\]** | \~4.7″/yr | \~3.6 pc | The pair is <1″ apart, so SPHEREx sees one dot. Not saturated (J≈12). Expect strong methane/water absorption. Bright ε Indi A is \~7′ away: watch for glare and ghosts. **Best target for the spectrum-based opinion.** |
| **RW Aurigae** | Young T Tauri binary with dusty disk; brightness dips | 05h07m49.5s +30°24′05″ | \~0.03″/yr (static) | \~164 pc | Doesn't move. Brightness can change between epochs; a major dimming event began in Feb 2025, during SPHEREx's mission. May saturate in some bands. |
| **R Draconis** | Mira variable (pulsating red giant), period \~245 days, V 6.7–13.2 | 16h32m40.2s +66°45′18″ | \~static | \~660 pc (Gaia DR2) | Doesn't move. Large brightness changes between epochs. Very bright in infrared, so **likely saturated**. It's within \~10° of the north ecliptic pole, where SPHEREx revisits often, so it may have many epochs **\[VERIFY coverage\]**. |

**What this means for the demo:**

- Barnard's Star = the cleanest **motion** demo.
- ε Indi B = the cleanest **Two Opinions** demo (motion + brown-dwarf spectrum).
- WISE 0855 = the **stacking** demo (invisible in single frames, visible in a detector-6 stack).
- RW Aur / R Dra = the **“changed but didn't move”** demo, and an honest **flags/saturation** demo.

## 2. Opinion A — nearby stars & brown dwarfs

**Motion opinion (proper motion):**

1. Measure the object's position in each epoch's detector stack (PSF-fit centroid; skip saturated or flagged cores).
2. Add earlier positions from Gaia DR3 (epoch 2016.0) and AllWISE (\~2010.5) when the object is in those catalogs. WISE 0855 is not in Gaia; use AllWISE/literature.
3. Fit a straight line (position vs time) → μ (″/yr) and direction. Report the error from the fit.
4. **Parallax:** at these distances it's 0.27–0.55″, under 0.1 SPHEREx pixel. We **do not** claim to measure parallax with SPHEREx alone; the app explains why.

**Spectrum opinion (type → distance):**

1. Build the spectrum (all points; drop flagged/saturated).
2. χ²-match against SPHEREx brown-dwarf and late-M templates (Gagné et al. 2026; Rustamkulov et al. 2026) → spectral type + uncertainty.
3. Spectral type → absolute magnitude using a published relation (e.g. Kirkpatrick et al. 2021 for brown dwarfs). Our apparent magnitude in the same band → **photometric distance** d = 10^((m − M + 5)/5) pc, with a range from the type uncertainty.

**Agreement test:** tangential speed v\_t = 4.74 × μ\[″/yr\] × d\[pc\] km/s.

- v\_t between 5 and 150 km/s → consistent with a normal nearby object (**agree**).
- 150–400 km/s → possible old/halo object (**agree, note**).
- Above 400 km/s, or no motion at all for a claimed nearby dwarf → **disagree** (wrong type, blend, or artifact).
- Validation only: compare d with the known parallax distance.

## 3. Opinion B — asteroids & comets

**Motion opinion (rate → distance range):** for trial circular orbits at heliocentric distance r = 0.8–60 AU (prograde, low inclination), compute the expected sky speed and direction at the observation time and position (Earth's position from astropy; observer ≈ geocentre, fine except for very near objects). Keep the r values that match the measured speed and direction within errors → distance range. **Validate against JPL Horizons** for known asteroids.

**Spectrum opinion (thermometer):**

- **Model** = reflected sunlight + thermal emission (NEATM, via `sbpy.thermal`).
- **Subsolar temperature:** T\_ss ≈ 393.6 K × \[(1 − A) / (η ε)\]^(1/4) / √(r / 1 AU), where A is Bond albedo (≈ 0.39 × geometric albedo p\_V), ε ≈ 0.9 is emissivity and η is the beaming parameter (\~0.8–2.5).
- **Observable:** thermal ratio TR = flux in D6 (4.42–5.00 µm) ÷ flux in D3 (1.63–2.41 µm), measured **in the same exposure pair** (D3 and D6 see the same sky at the same moment), so asteroid spin doesn't bias it. Also use D5/D2 pairs.
- **Fit:** r with priors p\_V 0.03–0.5 and η 0.8–2.5 → distance range.
- **Physics check:** main-belt asteroids (2–3 AU) are dominated by reflected light up to \~3.5 µm and by thermal emission at 4–5 µm; Trojans (5.2 AU) show little thermal emission even at 5 µm (Lisse et al. 2024). So TR alone separates “warm, near” from “cold, far.”
- **Limits:** D5/D6 are less sensitive (single visit \~AB 16.6–18), so the thermometer works only for brighter asteroids. Fainter ones get “can't tell.”

**Agreement test:** the motion range and the thermometer range overlap → **agree**; no overlap → **disagree** (wrong link, artifact, or unusual object); thermometer can't measure → **can't tell**.

## 4. Opinion C — variable stars

The object stays within 1 px across epochs, but its flux in the same detector at a similar wavelength changes by > 3σ between epochs → “**variable, not moving**.” Saturated in all bands → “can't tell (saturated)”, with the flags shown. Optional: compare R Dra's brightness with its known \~245-day cycle (AAVSO light curve).

## 5. Artifacts: how we reject them

- Appears in one frame only, or not in its simultaneous partner detector when it should be bright enough.
- Sits on flagged pixels (transient/cosmic ray, overflow, non-functional, persistence).
- Lies inside a bright star's bloom ring, or exactly 32 rows from a bright star in Band 1 (known crosstalk ghost).
- Spectrum is a single-channel spike.
- Motion would need an impossible speed or a non-straight path.

## 6. Planet X Reality Check (physics for the calculator)

- **Reflected light (scaled from Neptune):** V ≈ 7.8 − 5 log10(R/R\_Nep) − 2.5 log10(A/A\_Nep) + 5 log10(r·Δ / 29² AU²), with A\_Nep = 0.41 (Fortney et al. 2016). Twice as far is 16× fainter (+3.0 mag). (Corrected Nov 12: the earlier form put r⁴ inside 5 log10, which doubled the distance effect.) Published estimates put Planet Nine around V ≈ 21–25.
- **Internal heat:** some models predict extra glow near 3–5 µm, but the range is huge and uncertain. Show it as a range, clearly labelled “model-dependent.”
- **Compare** with SPHEREx single-visit depth (\~AB 18.5–19 at short wavelengths), and with deeper stacks (improves roughly with √(number of visits)).
- **Motion between 6-month epochs:** reflex parallax ≈ 2 × 206265 / r\[AU\] arcsec. At 500 AU that's \~825″ (\~14′), so a distant planet would **jump out of a small field** between epochs. The calculator explains why searches need large fields.
- **Honest conclusion shown in the app:** SPHEREx is not expected to detect the classic Planet Nine. It can rule out brighter or closer hypothetical planets in the fields it covers.

## 7. Validation protocol (published in the app and in docs/VALIDATION.md)

| ID | Test | Data | Pass threshold | Owner |
| --- | --- | --- | --- | --- |
| V1 | Barnard's Star proper motion | SPHEREx epochs + Gaia DR3 | μ within 10%; direction within 5° | Shivaansh |
| V2 | ε Indi B proper motion | SPHEREx + catalogs | within 15% of \~4.7″/yr | Shivaansh |
| V3 | WISE 0855 detection & motion | D6 stacks | ≥ 5σ in at least one stack, or an honest non-detection; if detected, μ within 20% of 8.15″/yr | Tirth + Shivaansh |
| V4 | Our photometry vs IRSA's tool | 3 unsaturated stars | median flux ratio 0.9–1.1 | Tirth |
| V5 | Brown-dwarf typing | ε Indi B (+ others from the Gagné catalog) | classified as T type; distance within 30% of known | Shimaya |
| V6 | Known asteroids | 2–3 ecliptic fields | ≥ 10 matched within 1 px of JPL | Shivaansh |
| V7 | Thermometer | ≥ 20 bright known asteroids | JPL distance inside our range for ≥ 70% | Shimaya |
| V8 | Variables | RW Aur, R Dra | labelled “variable, not moving” or “can't tell (saturated)”, with flags shown | Shimaya |
| V9 | False-alarm control | benchmark fields with time order shuffled | ≤ 2 false “movers” per field | Shivaansh |
| V10 | Reproducibility | re-run the bake | identical outputs (except timestamps) | Rishabh |

If a test fails, **the app says so on the Validation page.** An honest failure beats a hidden one.

## 8. How the app must word claims

- “Consistent with a brown dwarf about X–Y pc away,” not “This is a brown dwarf at X pc.”
- “Unexplained candidate, needs follow-up,” never “new discovery.”
- Always show the measurement, its uncertainty, and where the comparison value comes from.
- Saturated data is labelled saturated and never used in a verdict.

## Sources

- [Official challenge page](https://www.spaceappschallenge.org/2026/challenges/planet-x-and-spherex/)
- [Barnard's Star (Wikipedia)](https://en.wikipedia.org/wiki/Barnard%27s_Star)
- [WISE 0855−0714 (Wikipedia)](https://en.wikipedia.org/wiki/WISE_0855%E2%88%920714)
- [ε Indi Ba/Bb dynamical masses (Chen et al. 2022)](https://arxiv.org/pdf/2205.08077)
- [ε Indi Ba/Bb spectroscopy (King et al.)](https://arxiv.org/pdf/0810.4927)
- [RW Aurigae (Wikipedia)](https://en.wikipedia.org/wiki/RW_Aurigae)
- [Mira variables incl. R Draconis (Wikipedia)](https://en.wikipedia.org/wiki/Mira_variable)
- [SPHEREx saturation limits (POKEMON-DLC)](https://arxiv.org/pdf/2604.22983)
- [SPHEREx artifact bestiary](https://arxiv.org/pdf/2608.09862)
- [SPHEREx Ices overview (simultaneous detector pairs)](https://arxiv.org/pdf/2603.22135)
- [Lisse et al. 2024 (asteroid thermal emission with SPHEREx)](<https://epizodyspace.ru/bibl/inostr-yazyki/Lunar_and_Planetary_Science/2024/Lisse_et_al_Planetary_Science_with_SPHEREx_55th_LPSC_no_2039_(2024).pdf>)
- [sbpy (thermal models)](https://sbpy.readthedocs.io/en/latest/about.html)
- [Gagné et al. 2026 SPHEREx ultracool dwarfs](https://arxiv.org/abs/2604.22012)
- [Rustamkulov et al. 2026 SPHEREx brown dwarfs](https://arxiv.org/abs/2607.00543)
- [Fortney et al. 2016, Planet Nine detectability](https://arxiv.org/pdf/1604.07424)
- [The Planet Nine Hypothesis (review)](https://arxiv.org/pdf/1902.10103)
- [SPHEREx Sky Simulator (sensitivity)](https://arxiv.org/abs/2505.24856v1)
