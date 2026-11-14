# Planetes 08 — Demo, Pitch & Submission Kit

Owner: Tirth (pitch & video), with Rishabh (submission) and Shimaya (fact-check). **Re-check everything here against the official Project Submission Guide and Judging Guide when they come out.**

## 1. How we'll be judged

Space Apps judges use five criteria: **Influence, Creativity, Validity, Relevance, Presentation.** The guide reminds teams not to neglect Presentation.

| Criterion | What judges ask | Our evidence |
| --- | --- | --- |
| **Relevance** | Does it answer the challenge? | Coordinates → SPHEREx time-lapse; all five test targets; every “consideration” C1–C9 (doc 01 §2) |
| **Validity** | Is it scientifically sound and working? | Real data only; Validation page (V1–V10); honest saturation/limits; no discovery claims |
| **Creativity** | Is it original? | Two Opinions verdict; detector colour composite; stacking reveals WISE 0855; sonified blink (if built) |
| **Influence** | How many could it help? | Any coordinates, any visitor; embeddable links for citizen-science projects like Backyard Worlds; works on phones |
| **Presentation** | Is the story clear? | 30-second hook; clean UI; short video; plain language |

## 2. The story in one breath

> “Pluto was found by blinking two photos. NASA's SPHEREx now photographs the whole sky in 102 infrared colours every six months — too much for anyone to blink by hand. **Planetes** turns any patch of sky into a SPHEREx time-lapse in seconds, and for anything that moves or changes, it asks two independent questions: how does it move, and what does its light say? When both answers agree, you can trust what you're seeing.”

## 3. Demo video

**Length:** confirm once the guide is out. Some past guides asked for a very short video (about 30 s) for global judging. **Prepare two cuts:** 30 s and \~2 min. English voice or English subtitles.

### 30-second cut

| Time | Screen | Voice-over |
| --- | --- | --- |
| 0–5 s | Barnard's Star blinking across SPHEREx epochs | “This is Barnard's Star, moving across NASA SPHEREx images.” |
| 5–12 s | Type coordinates → time-lapse appears; switch to detector-6 stack → WISE 0855 appears | “Type any coordinates. Planetes fetches SPHEREx data live, aligns it, and stacks it to reveal faint, cold worlds.” |
| 12–22 s | Click ε Indi B → spectrum + Two Opinions panel → “Agree” | “For every mover, two independent opinions: its motion and its 102-colour spectrum. When they agree, it's real.” |
| 22–30 s | Flags overlay on R Draconis; Validation page; logo/name | “Honest flags, validated against Gaia and JPL. Planetes — Space Apps 2026.” |

### 2-minute cut

1. **Hook** (0:00–0:15): blink comparator → Pluto → SPHEREx.
2. **Problem** (0:15–0:30): SPHEREx data is huge and tricky (6 detectors, changing colours, artifacts).
3. **Live demo** (0:30–1:20): coordinates in, modes, overlays, flags, spectrum on the fly, Two Opinions on ε Indi B, WISE 0855 stack, RW Aur/R Dra “changed but didn't move.”
4. **Trust** (1:20–1:40): Validation page; what SPHEREx can't do (Planet X Reality Check).
5. **Impact + team** (1:40–2:00): embeddable for citizen science; four students; open source.

**Recording tips:**

- Record on the **baked** benchmarks (instant, no waiting).
- 1080p, cursor highlighted, no notifications.
- Every claim in the voice-over must match doc 04 §8 wording.

## 4. Live presentation (if our event has one)

- **3 minutes:** hook (20 s) → demo (100 s) → validation (30 s) → impact (30 s).
- Tirth presents; Rishabh drives the demo; Shimaya and Shivaansh take science questions.
- Backup: the recorded video on a local file, in case Wi-Fi or the API fails.

## 5. Judge Q&A prep

| Likely question | Answer |
| --- | --- |
| Did you find Planet X? | No, and SPHEREx isn't expected to see the classic Planet Nine. Our Reality Check shows why, and what SPHEREx *can* rule out. |
| Why do stars stay still while the images change colour? | Each frame is reprojected to the same grid, and every frame is labelled with its wavelength. Stacks combine one detector at a time. |
| How do you know a mover is real? | Two independent opinions must agree; artifacts fail both. Validation page shows false-alarm tests. |
| Why is Barnard's Star's spectrum missing? | It saturates SPHEREx. We show the flags and use it only for motion. |
| How is this different from other blink tools? | Live for any coordinates, stacking per detector, spectra on the fly, and the Two Opinions verdict, validated in-app. |
| Did you use AI? | Yes, for coding assistance; humans checked all science. Details in AI\_USAGE.md. |
| Can others use it? | Yes: URL parameters and an embed page; open-source code. |

## 6. Submission checklist (fields to confirm against the official guide)

From past guides, expect fields like these:

- [ ] Project title: **Planetes**
- [ ] High-level summary (≤ \~200 words): use §2, plus features
- [ ] Project details: what it does, how it works, benefits, tools/languages used
- [ ] **Link to final project** (live site: https://planetes.divergit.com) + **public GitHub repo**
- [ ] Demo video link (YouTube/Drive, public)
- [ ] **Space agency data used:** SPHEREx QR2/QR3 via IRSA; plus Gaia DR3 (ESA), AllWISE (NASA), JPL SSD services
- [ ] **References:** every dataset, library, tool, image (§7)
- [ ] AI use disclosure (if asked)
- [ ] English throughout (or English subtitles)
- [ ] Terms & Conditions box checked
- [ ] Submitted before the deadline in **our event's time zone**

## 7. References template (paste into the submission and README)

**Data**

- NASA SPHEREx Quick Release Spectral Images, NASA/IPAC Infrared Science Archive (IRSA). QR2: doi:10.26131/IRSA652; QR3: doi:10.26131/IRSA662. Use IRSA's exact acknowledgement sentence from the SPHEREx QR overview page.
- ESA Gaia DR3 (Gaia Collaboration); AllWISE (NASA/IPAC); unWISE imagery.
- CDS Strasbourg: SIMBAD, VizieR, Sesame, Aladin Lite, HiPS (including the CDS-built SPHEREx HiPS).
- JPL Solar System Dynamics: SBIdent, Horizons. IMCCE SkyBoT (if used).

**Software**

- astropy, astroquery, photutils, reproject, pyvo, numpy, scipy, Pillow, sbpy, scikit-learn, FastAPI, Next.js, React, Aladin Lite v3.
- xcavation (Brooks, Cushing, Kothari; MIT): method reference for forced photometry.
- IRSA SPHEREx tutorials (intro, cutouts, PSF, Source Discovery Tool).
- Anything else added in `docs/REFERENCES.md` during the week.

**Science**

- The papers listed in doc 04 (Lisse et al. 2024; Gagné et al. 2026; Rustamkulov et al. 2026; Fortney et al. 2016; the Planet Nine review; SPHEREx instrument and saturation papers).

**AI tools:** list tools used (e.g. Antigravity / Gemini, Codex, Claude) and what for.

## 8. Brand and legal rules

- **No NASA insignia (“meatball”) or NASA logotype** in the app, video or slides, and nothing implying NASA endorsement.
- The NASA Space Apps Challenge logo may be used per the Space Apps brand guidelines (don't distort it).
- Only images we made or that are openly licensed and credited. No copyrighted music in the video.

## 9. Final QA (final morning)

- [ ] Open the live site in incognito on a phone and a laptop; all 5 benchmarks work.
- [ ] Type a random coordinate; a time-lapse appears (or a clear “no SPHEREx coverage” message).
- [ ] Copy a link → opens the same view; `/embed` works in an iframe.
- [ ] Validation page loads; numbers match `docs/VALIDATION.md`.
- [ ] No “discovered/confirmed” wording anywhere; no placeholder text; no console errors.
- [ ] README: what it is, live link, how to run, data credits, licence.
- [ ] Video plays publicly without login.

## Sources

- [Space Apps Judging & Awards Guide](https://spaceappschallenge.org/resources/judging-awards-guide)
- [Space Apps 2022 Project Submission Guide (field reference)](https://spaceapps-prod.s3.amazonaws.com/media/documents/Space_Apps_2022_Project_Submission_Guide.pdf)
- [Space Apps Participant Terms (citation rule)](https://spaceappschallenge.org/legal)
- [Space Apps brand guidelines](https://spaceappschallenge.org/brand)
- [Navigator terms: NASA logo restrictions](https://www.spaceappschallenge.org/navigator-terms-conditions/)
- [SPHEREx QR overview (DOIs, acknowledgement)](https://irsa.ipac.caltech.edu/data/SPHEREx/docs/overview_qr.html)
