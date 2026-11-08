# References

Add every dataset, library, repo, image and paper you use, in the same PR that uses it.

## Data
- NASA SPHEREx Quick Release Spectral Images, NASA/IPAC Infrared Science Archive (IRSA). QR2: doi:10.26131/IRSA652; QR3: doi:10.26131/IRSA662. Use IRSA's acknowledgement sentence from the SPHEREx QR overview page.
- ESA Gaia DR3 (Gaia Collaboration); AllWISE (NASA/IPAC); unWISE imagery.
- CDS Strasbourg: SIMBAD, VizieR, Sesame, Aladin Lite, HiPS (incl. CDS-built SPHEREx HiPS).
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
- Space Grotesk (Florian Karsten) and IBM Plex Sans (IBM), both SIL Open Font License 1.1, via `next/font/google`.
- GNU Make (GPL-3, build tool only, not shipped).

## Science papers
See docs/04-Science-Validation.md, Sources section.
