# Submission draft (paste into the Space Apps form)

Draft Nov 11, updated Nov 13 00:30 IST. Check every field against the official Submission guide on Nov 13 (docs/08 §6) and update the feature list at the freeze (Sat 14, 18:00): **only list what works on the live site then.** Lines marked [AT FREEZE] depend on work still in progress.

## Project title
Planetes

## High-level summary (≤ 200 words)
Pluto was found by blinking two photographs. NASA's SPHEREx now photographs the whole sky in 102 infrared colours every six months, far too much to blink by hand. Planetes turns any patch of sky into a SPHEREx time-lapse: type a position (or pick one of the five challenge targets) and real SPHEREx images of that spot play like a short video, on a shared brightness scale, with SPHEREx's own quality flags and the date, detector and wavelength of every frame. Objects that move or change stand out. For an object, Planetes then asks two independent questions: how does it move, and what does its light say? A star's spectrum gives its type and so its distance; together with its motion that gives a speed that either makes sense or doesn't. When both opinions agree, the result is consistent with a real object; when they don't, Planetes says so and explains why. Everything shown is real NASA data, with its source on screen, and the tool can be shared or embedded with one link.

## Project details
**What it does.** A public web tool for the "Planet X and SPHEREx" challenge:
- **Time-lapse of any sky position** from every SPHEREx visit, on a shared brightness scale, with SPHEREx's own quality flags and the date, detector and wavelength of each frame; the five challenge benchmarks play instantly.
- **Blink comparator** (the way Pluto was found), detector **stacks, difference and colour** views [AT FREEZE: once PR #20 + the stacks bake land], a **sound** mode that plays each frame as a note, and a 1-minute **guided tour**.
- **Catalogue stars** (Gaia DR3, AllWISE) moved to each frame's date, and a sky-context map.
- **Spectrum on the fly** from 0.75 to 5 µm with every rejected point explained (saturation, flags, a neighbour star in the aperture).
- **Two Opinions:** motion vs spectrum. The spectrum is typed against standard brown-dwarf/star spectra (ε Indi B: T3 at 2.5–3.7 pc vs 3.64 pc from Gaia) or, for asteroids, read with a thermal model; the verdict says Agree, Disagree or Can't tell, with reasons. [AT FREEZE: motion opinions from measured SPHEREx positions.]
- **Known asteroids** predicted by JPL for SPHEREx's exact position in orbit [AT FREEZE: if V6 passes].
- **Planet X reality check:** a calculator showing how bright a hypothetical distant planet would be in SPHEREx bands and how far it would jump between visits.
- **Validation page** that publishes every test against a known answer, including what has not passed.

**How it works.** A Python pipeline queries the NASA/IPAC Infrared Science Archive (IRSA) for every SPHEREx exposure covering the position (Quick Releases 2 and 3 and Data Release 1), downloads small cutouts instead of full images, subtracts the zodiacal light, aligns each frame to north-up, and renders them with one shared stretch. A FastAPI service runs these jobs and caches results; a Next.js site plays them. Star positions come from SIMBAD and Gaia DR3 and are moved to each frame's date. The verdict follows written rules (docs/04), and every number keeps its SPHEREx observation ID and code version.

**Benefits.** Anyone can see how the sky changes in SPHEREx data in seconds, and learn why a "change" can be a moving star, a variable star or a glitch, without installing anything.

**Tools and languages.** Python (Astropy, astroquery, pyvo, photutils, NumPy, SciPy, Pillow, FastAPI), TypeScript (Next.js, React), Aladin Lite. Hosted on Vercel (site) and Render (API), with a Google Cloud Storage cache.

## Links
- Live site: https://planetes.divergit.com
- Code: https://github.com/nova-rishabh/Planetes
- Demo video: [AT FREEZE, owner Tirth]

## Space agency data used
- NASA SPHEREx spectral images: Quick Releases QR2 (doi:10.26131/IRSA652) and QR3 (doi:10.26131/IRSA662), and Data Release 1 [add the DR1 DOI from IRSA], via NASA/IPAC IRSA. [Add IRSA's exact acknowledgement sentence.]
- ESA Gaia DR3 and NASA AllWISE (via IRSA).
- NASA JPL Solar System Dynamics: Small-Body Identification API (known asteroids).

## References and AI use
Paste docs/08 §7, checked against docs/REFERENCES.md on the day. AI tools: list from docs/AI_USAGE.md.

## Before pressing Submit
English throughout · links open in a private window · terms box ticked · submitted before Sun Nov 15, 18:00 IST.
