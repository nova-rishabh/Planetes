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

**Official rule:** a video of **30 seconds or less** (or 7 slides or fewer), on a public link with no login (YouTube unlisted or Google Drive "anyone with the link"). English voice or English subtitles. A plain screen recording needs no "AI-generated" watermark; any AI-generated image or clip does.

### 30-second script (matches the live site)

| Time | Screen | Voice-over |
| --- | --- | --- |
| 0–5 s | Homepage, click **"Take the 1-minute tour"**; Barnard's Star plays | "Pluto was found by blinking two photos. NASA's SPHEREx now photographs the whole sky in 102 infrared colours." |
| 5–12 s | Tour stop 3: it blinks the first and last visit; Barnard's Star jumps | "Planetes turns any spot on the sky into a SPHEREx time-lapse. Blink two visits, and Barnard's Star moves." |
| 12–20 s | Pick **ε Indi B**; scroll to the spectrum and Two Opinions | "From SPHEREx's own pixels it builds a spectrum: ε Indi B comes out as a T-type brown dwarf, 2.6 to 3.7 parsecs away, consistent with Gaia's 3.6." |
| 20–26 s | **Validation** page, passed rows | "Every result is checked against known answers: Gaia, JPL asteroids, false-alarm tests. Six of ten pass so far." |
| 26–30 s | Back to the homepage title | "Planetes. Real NASA data, honest answers." |

Keep the spoken numbers in step with the site: if motion lands for ε Indi B, mention it; if more validation tests pass, say the new count.

**Recording tips:**

- Record on the **baked** benchmarks (instant, no waiting).
- 1080p, cursor highlighted, no notifications.
- Every claim must match doc 04 §8 wording: "consistent with", never "discovered" or "confirmed". No NASA logo.

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
