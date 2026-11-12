# References

Add every dataset, library, repo, image and paper you use, in the same PR that uses it.

## Data
- NASA SPHEREx Quick Release Spectral Images, NASA/IPAC Infrared Science Archive (IRSA). QR2: doi:10.26131/IRSA652; QR3: doi:10.26131/IRSA662. Use IRSA's acknowledgement sentence from the SPHEREx QR overview page.
- ESA Gaia DR3 (Gaia Collaboration); AllWISE (NASA/IPAC); unWISE imagery.
- CDS Strasbourg: SIMBAD, VizieR, Sesame, Aladin Lite, HiPS (incl. CDS-built SPHEREx HiPS).
- Sky context panel: Aladin Lite 3.8.2 (CDS; npm `aladin-lite`, LGPL-3 files / GPL-3 per README), loaded unmodified from jsDelivr; HiPS surveys AllWISE colour, 2MASS colour, DSS2 colour (built by CDS), served from ESA ESASky (skies.esac.esa.int).
- JPL Solar System Dynamics: SBIdent, Horizons.

## Software
- astropy, astroquery, photutils, reproject, pyvo, numpy, scipy, Pillow, sbpy, scikit-learn, FastAPI, Next.js, React, Aladin Lite v3.
- xcavation (Brooks, Cushing, Kothari; MIT): forced photometry method reference.
- IRSA SPHEREx tutorials (intro, cutouts, PSF, Source Discovery Tool).

### Added in D1.1 (scaffold)
- IRSA TAP VOSI availability endpoint (https://irsa.ipac.caltech.edu/TAP/availability), IVOA VOSI 1.0: used by `/api/health`.
- JSON Schema draft 2020-12 (json-schema.org): contract format.
- datamodel-code-generator (MIT): JSON Schema -> pydantic v2 models.
- json-schema-to-typescript (MIT): JSON Schema -> TypeScript types.
- jsonschema + referencing (MIT): schema checks and `make validate`.
- pytest (MIT), ruff (MIT): tests and lint.
- FastAPI (MIT), uvicorn (BSD-3), httpx (BSD-3): API server and the IRSA health probe.
- Next.js (MIT), React (MIT), TypeScript (Apache-2.0), ESLint + eslint-config-next (MIT), Vitest (MIT): web app and checks.
- IBM Plex Sans, IBM Plex Sans Condensed and IBM Plex Mono (IBM), SIL Open Font License 1.1, via `next/font/google`.
- WiseView (Backyard Worlds): idea for the simple A/B blink control (no code used).
- google-cloud-storage (Apache-2.0): persistent cache in the `planetes-cache` bucket (`planetes/cache.py`).
- GNU Make (GPL-3, build tool only, not shipped).

## Science papers
See docs/04-Science-Validation.md, Sources section.

### Added in D3.1 (star resolution and epoch propagation)
- SIMBAD (CDS Strasbourg): https://simbad.cds.unistra.fr/simbad/ — object identification and fallback astrometry.
- ESA Gaia Archive, Gaia DR3: https://gea.esac.esa.int/archive/ — astrometric positions, proper motions, parallaxes and reference epochs.
- Astropy `SkyCoord.apply_space_motion`: https://docs.astropy.org/en/stable/coordinates/apply_space_motion.html — epoch propagation.
- Astroquery SIMBAD and Gaia modules: https://astroquery.readthedocs.io/en/latest/ — Python access to the catalog services.

### Added in D3.2 (overlays) and D3.3 (motion fit)
- IRSA TAP table `gaia_dr3_source`: Gaia DR3 astrometric catalog queried by cone search around each target for overlay markers; epoch-propagated to each frame's MJD using `SkyCoord.apply_space_motion`.
- IRSA TAP table `allwise_p3as_psd`: AllWISE Point Source Database queried by cone search around each target for near-infrared overlay markers.
- SPHEREx pixel scale ≈ 6.2 arcsec/px (all 4 tested frames): used as the accuracy threshold for overlay alignment.
- Astropy WCS `all_world2pix`: https://docs.astropy.org/en/stable/wcs/ — RA/Dec → pixel projection using the IMAGE-extension WCS (SIP distortions). D6 mirror handled automatically via the CD matrix; never flipped by hand.
- Astropy `solar_system_ephemeris` (built-in DE430 ephemeris): used by `trial_circular_orbit_rate` for approximate angular-rate range to distance conversion.
- Barnard's Star Gaia DR3 source ID 4472832130942575872: ra = 269.44850, dec = 4.73942, epoch = 2016.0, pmra = −801.551 mas/yr, pmdec = 10 362.394 mas/yr, parallax = 546.976 mas (from IRSA TAP `gaia_dr3_source`; corroborated by `web/public/data/targets/barnard/target.json`).

## Science papers
See docs/04-Science-Validation.md, Sources section.
### Added in D2.4 (interim) / D4.1 / D4.3 (photometry, spectrum, typer)
- photutils (Astropy affiliated, BSD-3): https://photutils.readthedocs.io/ — circular aperture and annulus photometry.
- SpeX Prism Library spectral standards M0–T9 (Burgasser 2014, ASInC 11, 7; IRTF SpeX), files and standards list from SPLAT: https://github.com/aburgasser/splat (MIT) — templates in `pipeline/src/planetes/data/spex_standards.csv`.
- Dupuy & Liu 2012, ApJS 201, 19 — absolute 2MASS J vs spectral type polynomial (M6–T9), coefficients as tabulated in SPLAT `initialize.py`.
- Cohen, Wheaton & Megeath 2003, AJ 126, 1090 — 2MASS zero points (J 1594 Jy) used for the apparent J magnitude and the 2MASS cross-check.
- 2MASS Point Source Catalog via IRSA TAP (`fp_psc`) — flux-scale cross-check of our photometry.
- Fortney et al. 2016, ApJL 824, L25 — Neptune geometric albedo 0.41 used to scale the Planet X calculator (docs/04 §6).
- IAU 2015 Resolution B3 — nominal solar radius and effective temperature (Sun as a 5772 K blackbody in planet_x).
- Harris 1998, Icarus 131, 291 — NEATM asteroid thermal model (integrated numerically in thermal.py; sbpy 0.6.0's NEATM has no flux method).
- Bowell et al. 1989, Asteroids II — H-G phase law and phase integral q = 0.290 + 0.684 G.
- Kopp & Lean 2011, GRL 38, L01706 — solar constant 1361 W/m².
