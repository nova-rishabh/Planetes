# Submission draft (paste into the Space Apps form)

Draft Nov 11. Check every field against the official Submission guide on Nov 13 (docs/08 §6) and update the feature list at the freeze (Sat 14, 18:00): **only list what works on the live site then.** Lines marked [AT FREEZE] depend on work still in progress.

## Project title
Planetes

## High-level summary (≤ 200 words)
Pluto was found by blinking two photographs. NASA's SPHEREx now photographs the whole sky in 102 infrared colours every six months, far too much to blink by hand. Planetes turns any patch of sky into a SPHEREx time-lapse: type a position (or pick one of the five challenge targets) and real SPHEREx images of that spot play like a short video, on a shared brightness scale, with SPHEREx's own quality flags and the date, detector and wavelength of every frame. Objects that move or change stand out. For an object, Planetes then asks two independent questions: how does it move, and what does its light say? A star's spectrum gives its type and so its distance; together with its motion that gives a speed that either makes sense or doesn't. When both opinions agree, the result is consistent with a real object; when they don't, Planetes says so and explains why. Everything shown is real NASA data, with its source on screen, and the tool can be shared or embedded with one link.

## Project details
**What it does.** A public web tool for the "Planet X and SPHEREx" challenge: SPHEREx time-lapses of any sky position, the five test targets ready to play instantly, frame-by-frame metadata and flags, blink comparison, a sky-context map, shareable/embeddable links, and the Two Opinions check (motion vs spectrum). [AT FREEZE: add detector stacks and difference images, Gaia/AllWISE overlays, spectra on the fly, Two Opinions results for the five targets, the Validation page.]

**How it works.** A Python pipeline queries the NASA/IPAC Infrared Science Archive (IRSA) for every SPHEREx exposure covering the position (Quick Releases 2 and 3), downloads small cutouts instead of full images, subtracts the zodiacal light, aligns each frame to north-up, and renders them with one shared stretch. A FastAPI service runs these jobs and caches results; a Next.js site plays them. Star positions come from SIMBAD and Gaia DR3 and are moved to each frame's date. The verdict follows written rules (docs/04), and every number keeps its SPHEREx observation ID and code version.

**Benefits.** Anyone can see how the sky changes in SPHEREx data in seconds, and learn why a "change" can be a moving star, a variable star or a glitch, without installing anything.

**Tools and languages.** Python (Astropy, astroquery, pyvo, NumPy, SciPy, Pillow, FastAPI), TypeScript (Next.js, React), Aladin Lite. Hosted on Vercel (site) and Render (API), with a Google Cloud Storage cache.

## Links
- Live site: https://planetes.divergit.com
- Code: https://github.com/nova-rishabh/Planetes
- Demo video: [AT FREEZE, owner Tirth]

## Space agency data used
- NASA SPHEREx Quick Release spectral images, QR2 (doi:10.26131/IRSA652) and QR3 (doi:10.26131/IRSA662), via NASA/IPAC IRSA. [Add IRSA's exact acknowledgement sentence.]
- ESA Gaia DR3 (via IRSA). [AT FREEZE: AllWISE (NASA/IPAC) once overlays ship.]

## References and AI use
Paste docs/08 §7, checked against docs/REFERENCES.md on the day. AI tools: list from docs/AI_USAGE.md.

## Before pressing Submit
English throughout · links open in a private window · terms box ticked · submitted before Sun Nov 15, 18:00 IST.
