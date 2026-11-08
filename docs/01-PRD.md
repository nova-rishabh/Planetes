# Planetes 01 — PRD (Product Requirements)

Nov 7, 2026 · Team Planetes · NASA Space Apps 2026, Challenge “Planet X and SPHEREx” · v2 (final for build)

**Doc set:** 01 PRD (what & why) · 02 TRD (how) · 03 Data Contract & API · 04 Science & Validation · 05 Phases & Timeline · 06 Role Guide · 07 AI Build Playbook · 08 Demo, Pitch & Submission Kit

## 1. One-line summary

**Planetes is a public web tool where anyone types sky coordinates and watches real NASA SPHEREx infrared images of that spot play like a short video. Moving and changing objects pop out, and for every object Planetes gives two independent opinions — one from how it moves, one from its 102-colour spectrum — and shows whether they agree.**

## 2. The official challenge (what the judges will check)

**Task (from the official statement):** create a public-facing web tool that displays SPHEREx images of the sky, making it easy for anyone to quickly see how they change over time. Users enter the RA and Dec of a patch of sky, and the tool shows a series of images of that patch like a little video, so moving objects are easy to spot.

**Required test targets:** Barnard's Star, Epsilon Indi B (a pair of brown dwarfs orbiting a star), WISE 0855 (a fast-moving brown dwarf), and the variable stars RW Aurigae and R Draconis.

**“Potential considerations” in the statement, and how we answer each:**

| # | Consideration (official) | Our feature | Priority |
| --- | --- | --- | --- |
| C1 | Easy to update with the latest data releases | Live queries to IRSA with automatic QR3 → QR2 fallback; nothing is hard-coded to one release | Must |
| C2 | Display the 102 bands creatively; e.g. add together data from each of the 6 detectors to improve signal-to-noise | “Detector stack” view (sum per detector per epoch) and a false-colour composite of the 6 detectors | Must |
| C3 | Extra kudos for spectra on the fly | Click any point → its SPHEREx spectrum is measured live | Must |
| C4 | Add together or subtract images taken at different times | Sum mode and Difference mode (later epoch minus earlier, same detector) | Must |
| C5 | Let users choose the field of view | FOV control (about 2′ to 30′), with a speed/size warning for large fields | Must |
| C6 | Overlay data from other telescopes such as Gaia or WISE | Gaia DR3 and AllWISE positions, moved to each image's date; unWISE and SPHEREx all-sky maps in an Aladin Lite context panel | Must |
| C7 | Coordinates in the URL so the tool can be embedded elsewhere | Shareable links and an /embed page with all settings in the URL | Must |
| C8 | Display metadata like contamination flags | Flag overlay with a plain-language legend, and per-frame metadata panel | Must |
| C9 | Use public tools like Astropy and Aladin (CDS) | Astropy-based pipeline; Aladin Lite v3 for sky context | Must |

The statement also stresses that nearby objects shift because the Earth orbits the Sun (parallax), that this helps measure distances, and that volunteers find comets and brown dwarfs this way (Backyard Worlds). **Our Two Opinions feature is built exactly on that idea.**

## 3. The problem

1. **SPHEREx data is powerful but hard to use.** It's released as large calibrated image files (about 70 MB each, 6 per pointing). Each detector sees a different colour at each position. Images taken at different times have different orientations and colours. A curious person cannot just “blink” them.
2. **“Something changed” is not enough.** Cosmic-ray hits, saturated bright stars, detector artifacts and variable stars all look like changes. People need help telling real movers from glitches.
3. **SPHEREx's superpower, its spectrum, is usually ignored** by simple blink tools.

## 4. Our solution and what makes it unique

**Core (what the challenge asks for):** a fast, beautiful, live SPHEREx time-lapse for any coordinates, with stacking, differencing, overlays, flags, adjustable field of view, shareable URLs and on-the-fly spectra.

**Differentiator: “Two Opinions.”** For any object a user clicks, Planetes forms two independent opinions and shows whether they agree:

| Object kind | Motion opinion | Spectrum opinion | Agreement means |
| --- | --- | --- | --- |
| Nearby star / brown dwarf | Proper motion measured from SPHEREx positions over \~1.5 years, plus Gaia/WISE earlier positions | Spectral type from its SPHEREx spectrum → how bright that type really is → distance | Motion × distance gives a believable space speed → consistent nearby object |
| Asteroid / comet | Fast motion (arcsec per hour) → range of possible distances from the Sun | Heat glow at 3.8–5 µm vs reflected sunlight at 1.6–2.4 µm (taken at the same instant) → temperature → distance from the Sun | Both distance ranges overlap → real object, roughly located |
| Variable star | Does not move | Same spectral shape, brightness changes between epochs | “Changed but didn't move” → variable |
| Artifact | Motion not physical (one frame, impossible jump) | No real spectrum (single-channel spike, flagged pixels) | Both fail → rejected, with the reason shown |

**Competitive position:** more than 10 public repos target this challenge. Most offer blink viewers, the five test targets, catalog overlays and spectra. **None we found combines motion and spectrum into a single cross-checked verdict.** That, plus polish and validation shown inside the app, is how we stand out.

## 5. Users and what they need

| User | Need | Success looks like |
| --- | --- | --- |
| Curious public, students | See something real move in NASA's newest data, fast | Sees a mover within 30 seconds of landing on the site |
| Teachers | A ready classroom demo of proper motion, parallax, brown dwarfs, variable stars | Shareable links to each benchmark with plain explanations |
| Citizen scientists (Backyard Worlds-style) | Check any coordinates; tell real from fake | Coordinates in, time-lapse + flags + overlays + spectrum + verdict out |
| NASA judges | Validity, relevance, impact, creativity, presentation | All five test targets work; validation plots in the app; honest limits |

## 6. Features and acceptance criteria

Priority: **Must** = required to submit · **Should** = strongly wanted · **Could** = only if time allows.

### F1. Coordinate search & target list — Must

- Input RA/Dec in degrees or sexagesimal, or an object name (resolved via CDS Sesame/SIMBAD). One-click buttons for the five official test targets.
- **High proper-motion fix:** for named stars, the tool moves the search position to the current epoch using the catalog proper motion. (Barnard's Star has moved about 4.5′ since its J2000 position.) Show a note when this happens.
- **Accept when:** all 5 benchmarks and any valid coordinate return results; invalid input shows a helpful error.

### F2. Time-lapse player — Must

- Frames sorted by time; play, pause, step, scrub, speed control, loop, and A/B blink between any two frames.
- Every frame is reprojected to the same north-up grid so stars stay still.
- Each frame shows date/time, detector, wavelength at the centre, release (QR2/QR3), and flagged-pixel percentage.
- Shared brightness stretch across frames (auto, plus manual sliders); log/asinh options.
- **Accept when:** Barnard's Star and ε Indi B visibly move across epochs; the player stays smooth (no jank) on a mid-range phone.

### F3. View modes (stack / sum / difference / colour) — Must

- **Exposures:** every individual image.
- **Detector stacks:** for each survey pass (epoch), sum all images from the same detector → 6 cleaner images per epoch. This is the challenge's own tip and makes faint objects like WISE 0855 visible at 4–5 µm.
- **Difference:** later epoch minus earlier epoch, same detector. Movers appear as a dark/bright pair; static stars cancel.
- **Colour composite:** map short / middle / long detectors to blue / green / red so cold brown dwarfs look red.
- **Accept when:** the difference image of Barnard's Star shows a clear +/− pair; WISE 0855 is visible in the detector-6 stack.

### F4. Field of view control — Must

- Preset sizes from about 2′ to 30′; warning that bigger fields load slower.
- **Accept when:** changing FOV re-queries and redraws correctly.

### F5. Overlays — Must

- Gaia DR3 and AllWISE source markers on each frame, **moved to that frame's date** using proper motion; toggles; click a marker for details.
- Aladin Lite context panel with SPHEREx per-detector all-sky maps (CDS HiPS), unWISE and DSS.
- Optional: known asteroids/comets in the frame (Should).
- **Accept when:** markers sit on the stars in every frame for the benchmark fields.

### F6. Flags & metadata — Must

- Toggle a coloured overlay of SPHEREx quality flags (e.g. saturation/overflow, transient/cosmic ray, non-functional pixel, persistence), with a plain-language legend.
- A metadata drawer per frame (observation ID, time, detector, wavelength range, release, flagged %).
- **Accept when:** the saturated core of Barnard's Star shows as flagged and the legend explains why.

### F7. Spectra on the fly — Must

- Click any point → forced photometry at that position in every image → interactive spectrum (flux vs wavelength), coloured by epoch; flagged/saturated points greyed out with reasons.
- Progress indicator; results cached.
- **Accept when:** a spectrum for ε Indi B shows the expected brown-dwarf shape (strong absorption bands, especially methane near 3.3 µm), or the app clearly marks why not.

### F8. Shareable URL & embed — Must

- Every setting in the URL (`ra`, `dec`, `fov`, `mode`, `det`, `frame`, `stretch`, `overlays`), plus an `/embed` page and a copy-embed-code button.
- **Accept when:** opening a copied link reproduces the exact view.

### F9. Two Opinions verdict — Must (our differentiator)

- For a selected object: Motion opinion card, Spectrum opinion card, and a verdict (Agree / Disagree / Can't tell) with confidence and plain-language reasons.
- **Accept when:** verdicts exist for all five benchmarks (with saturation explained where it applies) plus the validation set in doc 04; each reason is understandable without astronomy knowledge.

### F10. Validation & limits page — Must

- Plots comparing our measurements to known truth (proper motions vs Gaia/literature, asteroid distances vs JPL, brown dwarf types vs literature), plus what SPHEREx can and can't detect.

### F11. Guided tour — Should

- A 2-minute story through the five benchmarks for first-time visitors.

### F12. Planet X Reality Check — Should

- Calculator: size, distance, reflectivity → predicted SPHEREx brightness and motion per visit, versus SPHEREx's limits. An honest explainer that SPHEREx is not expected to see a classic Planet Nine.

### F13. Mover search on ecliptic fields — Could

- Automatic search for moving dots in a few fields near the ecliptic, labelling known asteroids, with a fake-object recovery test.

### F14. Sonified blink & accessibility — Could

- Sound that changes when something moves or brightens; full keyboard control; high contrast; alt text.

## 7. Non-goals

- No accounts, leaderboards or voting.
- No native mobile app (the site works on mobile browsers).
- No reports to the Minor Planet Center.
- No custom 3D globe.
- **No claim of discovering Planet X or any new object.** Unknown candidates are labelled “unexplained, needs follow-up.”
- No made-up data, demo numbers or synthetic images shown as real.

## 8. Success metrics

| Judging criterion | Our target |
| --- | --- |
| Relevance | Every official consideration C1–C9 implemented; all 5 test targets work end-to-end |
| Validity | Validation plots in the app; Barnard's Star proper motion within 10% of Gaia; known-asteroid positions within 1 pixel |
| Creativity | Two Opinions verdict; detector-colour composite; sonified blink (if time) |
| Influence | Anyone can use any coordinates; embeddable links for citizen-science projects |
| Presentation | Under 30 s to first “wow”; clear demo video; honest limits page |
| Reliability | Benchmarks load from pre-baked data in under 3 s even if the API is cold |

## 9. Rules we follow

- Real NASA data only; every number traceable to a SPHEREx observation ID or a catalog record.
- Cite every source (data, code, images, AI tools) in the README and the submission References. Small credits in the app footer are fine, but the full list is mandatory.
- Public open-source repo with a license.
- No NASA insignia (“meatball”) or anything implying NASA endorsement.
- Use SPHEREx DOIs and IRSA's acknowledgement text.

## 10. Open items

- Official challenge **Resources tab opens Nov 13**: re-check this PRD against it that day.
- Submission deadline and time zone for our registered event (Tirth).
- Registered under Universal Event; global deadline (confirm Nov 13).
- Hosting decided: website on Vercel (free), API on Render Starter (team credits). See doc 02.

## Sources

- [Official challenge page](https://www.spaceappschallenge.org/2026/challenges/planet-x-and-spherex/)
- [IRSA SPHEREx](https://irsa.ipac.caltech.edu/Missions/spherex.html)
- [Space Apps FAQ and dates](https://www.spaceappschallenge.org/resources/participant-faqs/)
- [Backyard Worlds](https://en.wikipedia.org/wiki/Backyard_Worlds)
- [Space Apps judging criteria](https://spaceappschallenge.org/resources/judging-awards-guide)
