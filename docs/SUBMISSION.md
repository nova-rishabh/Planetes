# Submission (paste into the Space Apps form)

One section per form field, in the form's order. Only list what works on the live site when you press Submit.

## Project Name
Planetes: Watch the Infrared Sky Move

## Summary (50–200 words, max 1500 characters)
Pluto was found by blinking two photographs of the same patch of sky. NASA's SPHEREx now photographs the whole sky in 102 infrared colours every six months, far too much to blink by hand. Planetes turns any position on the sky into a SPHEREx time-lapse: type coordinates or pick one of five benchmark objects, and every real SPHEREx exposure of that spot plays like a short film on one shared brightness scale, with SPHEREx's own quality flags. Stars that move, brighten or fade stand out at once. For an object, Planetes then forms two independent opinions: how it moves, and what its light says. The spectrum gives a type and a distance; with the motion that gives a speed that either makes sense or doesn't, and Planetes says which and why. A Planet X calculator shows how bright a distant planet would look to SPHEREx and how far it would jump between visits. Every image and number is real archive data, every result is checked against known answers on a public Validation page, and the tool runs in any browser with nothing to install.

## Project Demonstration
Rule: a video of **30 seconds or less**, or **7 slides or fewer** (title and intro included). Public link, no login.
- Link: [Tirth: YouTube unlisted or Google Drive "anyone with the link"]
- Any AI-generated image or clip in it needs a visible "AI-generated" watermark. Screen recordings of the site need none.

## Project
- https://planetes.divergit.com
- Code: https://github.com/nova-rishabh/Planetes

## Project Details
**What it does.** Planetes is a public web tool for the "Planet X and SPHEREx" challenge.
- **Time-lapse of any sky position** from every SPHEREx visit, aligned north-up on one shared brightness scale, with SPHEREx's quality flags and the detector and wavelength of each frame. Five benchmark objects (Barnard's Star, ε Indi B, WISE 0855, R Draconis, RW Aurigae) play instantly.
- **Blink comparator** (the method that found Pluto), plus **stack, difference and colour** views that make faint motion and colour changes visible.
- **Catalogue stars** from Gaia DR3 and AllWISE moved to each frame's date, and a sky-context map.
- **Spectrum from 0.75 to 5 µm** built from SPHEREx's own pixels, with every rejected point explained (saturation, flags, a neighbouring star).
- **Two Opinions:** motion vs spectrum. The spectrum is matched to standard brown-dwarf and star spectra (ε Indi B: type T3 at 2.55–3.69 pc vs 3.64 pc from Gaia), and the verdict says Agree, Disagree or Can't tell, with reasons.
- **Planet X calculator:** brightness in SPHEREx bands and the six-month jump for any distance and size.
- **Validation page:** each measurement checked against a known answer (Barnard's Star motion within 1.6 % of Gaia; ε Indi B distance; a clean re-run reproduces the same answer).

**How it works.** A Python pipeline asks the NASA/IPAC Infrared Science Archive (IRSA) for every SPHEREx exposure covering the position (Data Release 1 and Quick Releases 2–3), downloads small cutouts instead of full images, subtracts the zodiacal light, aligns each frame to the sky and renders all frames with one shared stretch. A FastAPI service runs these jobs and caches results; a Next.js site plays them. Every number keeps its SPHEREx observation ID.

**Benefits and impact.** Anyone — a student, a citizen scientist, a teacher — can see how the infrared sky changes in seconds, and learn why a "change" can be a moving star, a variable star or an instrument glitch. It brings the WiseView-style blink search that found hundreds of brown dwarfs in WISE data to SPHEREx's 102 colours.

**Creativity.** It pairs two independent lines of evidence (motion and colour) and only calls something interesting when they agree, and it publishes its own test results.

**Tools.** Python (Astropy, astroquery, pyvo, photutils, NumPy, SciPy, FastAPI), TypeScript (Next.js, React, three.js), Aladin Lite. Hosted on Vercel and Render.

**Factors we considered.** Saturated pixels are never used in a verdict; SPHEREx pixels are about 6″, so we do not claim parallax; claims are worded "consistent with", never "discovered".

## Use of Super Intelligence (SI)
Tick: **code**, **text** (documentation). Not images, video or audio: every image on the site is real SPHEREx data.
On the site: About page, section "How we used AI tools". Full record: docs/AI_USAGE.md.

## NASA Data (Link Text | Link URL)
- SPHEREx Data Release 1 Spectral Images (doi:10.26131/IRSA678) | https://irsa.ipac.caltech.edu/data/SPHEREx/docs/overview_dr1.html
- SPHEREx Quick Release Spectral Images QR2 and QR3 (doi:10.26131/IRSA652, IRSA662) | https://irsa.ipac.caltech.edu/data/SPHEREx/docs/overview_qr.html
- NASA/IPAC Infrared Science Archive: SPHEREx | https://irsa.ipac.caltech.edu/Missions/spherex.html
- IRSA SPHEREx Tutorial Notebooks | https://caltech-ipac.github.io/irsa-tutorials/spherex/
- AllWISE Source Catalog (via IRSA) | https://irsa.ipac.caltech.edu/Missions/wise.html
- JPL Small-Body Identification API | https://ssd-api.jpl.nasa.gov/doc/sb_ident.html
- WiseView (idea for the blink control, no code used) | http://byw.tools/wiseview

## Space Agency Partner & Other Data (Link Text | Link URL)
- ESA Gaia Data Release 3 (IRSA copy, table gaia_dr3_source) | https://irsa.ipac.caltech.edu/Missions/gaia.html
- SIMBAD Astronomical Database (CDS) | https://simbad.cds.unistra.fr/
- Aladin Lite (CDS) | https://aladin.cds.unistra.fr/AladinLite/
- ESA ESASky sky images | https://sky.esa.int/
- SpeX Prism Library (standard spectra) | https://cass.ucsd.edu/~ajb/browndwarfs/spexprism/
- Astropy | https://www.astropy.org/
- astroquery | https://astroquery.readthedocs.io/
- Next.js | https://nextjs.org/
- three.js | https://threejs.org/
- Project code | https://github.com/nova-rishabh/Planetes

## Before pressing Submit
English throughout · every link opens in a private window without login · demo ≤ 30 s or ≤ 7 slides · no NASA logo anywhere · both boxes ticked · submitted before the internal deadline (18:00 IST on the final day).
