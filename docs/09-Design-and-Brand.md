# Planetes 09 — Design & Brand

Nov 8, 2026 · Owner: Rishabh · Applies to everything in `web/`, the demo video and slides.

## 1. Name and tagline

- **App name:** Planetes (from the Greek *planētēs*, "wanderer", the original word for planets: lights that move against the fixed stars).
- **Team name on Space Apps:** Team Planetes. (A different team called just "Planetes" exists on the same challenge. Always share our direct link.)
- **Tagline:** "Watch the infrared sky move."
- **Live URL:** `planetes.divergit.com` (subdomain on Vercel). The Vercel default URL stays as a fallback.

## 2. Look and feel

**Light theme.** Dark space UIs are what every AI-made astronomy site looks like, so we go the other way: a printed-journal look. Warm off-white paper, near-black ink, thin rules, and the dark SPHEREx frames sitting on the page like photographic plates in a paper. One warm accent is reserved for **things that moved or changed**. No gradients, no glows, no NASA insignia.

## 3. Colour palette: C "Plate Archive" (locked Nov 9 by team vote)

Options A Lab Notebook and B Clear Sky were dropped in the vote. All text pairs below meet WCAG AA (4.5:1) on the background. Accent colours come in two shades: a **fill** for markers and shapes, and a darker **text** shade for words.

| Token | Value | Use |
|---|---|---|
| `bg` | `#F4F2EF` | Page |
| `surface` | `#FFFFFF` | Panels, cards |
| `border` | `#DEDCDC` | Rules, inputs, chart grid |
| `ink` | `#191D23` | Text, primary buttons (white text) |
| `ink-muted` | `#57707A` | Labels, metadata |
| `ui` | `#7B919C` (fills) / `#57707A` (text) | Links, focus ring, active states |
| `accent-fill` | `#E07A35` | "Moved" marker, change highlights |
| `accent-text` | `#C2410C` | Accent words |

**Semantic colours** (always with an icon and a word, never colour alone): Agree = `ui` colour + ✓, Disagree = `accent-text` + ✕, Can't tell = `ink-muted` + ?.
**Flag overlay** on sky frames: saturated `#F4A62A`, cosmic ray `#F04770`, other flagged `#FFD167` (these sit on the dark frame, not on the page).

**Sky frames:** greyscale (asinh stretch) on a dark `#191D23` plate with a thin border; optional `inferno` colormap. The detector colour composite stays fixed: D1+D2 blue, D3+D4 green, D5+D6 red (doc 02).

**Spectrum chart, one colour per epoch:** Okabe–Ito colour-blind-safe set: `#0072B2`, `#E69F00`, `#009E73`, `#CC79A7`, `#D55E00`, `#56B4E9`. Rejected points are hollow `ink-muted` circles with a tooltip giving the reason.

## 3b. It must not look AI-generated

- No dark-mode-by-default, no purple-to-blue gradients, no glowing blobs, no glassmorphism, no emoji in the UI, no stock space photos or starfield backgrounds.
- No default fonts (Inter, Roboto, Poppins, Montserrat, Space Grotesk) and no untouched default Tailwind/shadcn look.
- Real data is the decoration: the first thing on screen is a real SPHEREx frame, not a hero banner.
- Specific, plain copy written by us ("Barnard's Star moved 15″ between these frames"), never filler like "Unlock the universe".
- Our own details: coordinate readouts in mono, detector labels, tick marks, figure-style captions ("Fig. 1 · D6 stack, epoch 2"), a custom favicon drawn from the detector colour bands.
- Review rule: before merging any UI, ask "would this look the same on any other AI-made site?" If yes, change it.

## 4. Typography

- One superfamily, like labels on a scientific instrument: headings **IBM Plex Sans Condensed** (600), body and UI **IBM Plex Sans** (400/500), numbers, coordinates and hex codes **IBM Plex Mono**.
- Space Grotesk (used in the D1.1 scaffold) is replaced: it is one of the most common AI-site fonts.
- **Never Inter** (or Roboto, Poppins, Montserrat).
- Scale: 12 / 14 / 16 (body) / 20 / 24 / 32 / 40 px. Line height 1.5 body, 1.2 headings.
- Coordinates always in mono, with units: `RA 269.4521°  Dec +4.6934°`.

## 5. Layout and components

- Desktop: player left (about 60 %), side panel right (spectrum, Two Opinions, metadata). Mobile: stacked; player first.
- Radius 12 px on panels, 8 px on controls, full pill on toggles. Spacing on a 4 px grid (8, 12, 16, 24, 32).
- Focus ring 2 px `ui`, always visible. Tap targets at least 44 px.
- Motion: 150–200 ms ease-out for UI; the time-lapse itself is user-controlled (no auto-play loops on page load beyond the first benchmark).
- Copy follows doc 04 §8: "consistent with", never "discovered" or "confirmed".

## 6. Reference sites (what to borrow from each)

| Site | Borrow |
|---|---|
| [ESASky](https://sky.esa.int) | Multi-mission overlays and layer toggles (not its dark look) |
| [Legacy Survey Viewer](https://www.legacysurvey.org/viewer) | Fast, simple sky viewer; URL holds the whole view |
| [WiseView (Backyard Worlds)](http://byw.tools/wiseview) | The blink tool our users already know; keep blinking that simple |
| [Aladin Lite](https://aladin.cds.unistra.fr/AladinLite/) | Our context panel; match its controls rather than fight them |
| [NASA Eyes on the Solar System](https://eyes.nasa.gov/apps/solar-system/) | Onboarding/tour pattern only (not its dark look; no insignia) |
| [Linear](https://linear.app) | Polish: spacing, muted borders, crisp type |
| [Distill](https://distill.pub) | Journal-style light pages where figures and data lead |
| [Our World in Data](https://ourworldindata.org) | Light, honest data UI: clear charts, sources under every figure |
| [Vercel dashboard](https://vercel.com) | Status badges, empty/loading/error states |
| [Observable Plot gallery](https://observablehq.com/@observablehq/plot-gallery) | Clean scientific charts for the spectrum |
| [Igloo Inc](https://www.igloo.inc) | Homepage base: scroll moves a camera through objects in glass/ice; pale, cool palette fits ours |
| [100,000 Stars](https://stars.chromeexperiments.com) | 3D built on real catalogue data, zooming between scales |
| [Figma colour combinations](https://www.figma.com/resource-library/color-combinations/) | Alternatives if we tweak: "Blue eclipse", "Under the moonlight", "Ocean tide" |

## 7. Implementation

- Tokens live as CSS variables in `web/src/styles/tokens.css` (and the Tailwind theme if Tailwind is used). Components never use raw hex.
- One light theme only for the hackathon. No dark mode.
- Check every new screen with Lighthouse accessibility ≥ 90.

## 8. 3D homepage (Nov 13)

- Opening: SPHEREx modelled in code (an illustration, labelled so), then the camera dives through the telescope into a stack of real SPHEREx exposures, one glass plate per visit.
- Every image on a plate is a real baked frame; the ring and line come from the baked target positions. No invented imagery.
- Colours in 3D are read from the tokens at runtime (`three/palette.ts`); no hex in the scene.
- Fallbacks: reduced motion or no WebGL2 → the flat hero with the 2D time-lapse. Phones: lower pixel ratio, simpler glass, wider lens.
- Libraries load after first paint (`next/dynamic`, `ssr: false`).
