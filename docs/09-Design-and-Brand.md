# Planetes 09 — Design & Brand

Nov 8, 2026 · Owner: Rishabh · Applies to everything in `web/`, the demo video and slides.

## 1. Name and tagline

- **App name:** Planetes (from the Greek *planētēs*, "wanderer", the original word for planets: lights that move against the fixed stars).
- **Team name on Space Apps:** Team Planetes. (A different team called just "Planetes" exists on the same challenge. Always share our direct link.)
- **Tagline:** "Watch the infrared sky move."
- **Live URL:** `planetes.rishabhk.xyz` (custom domain on Vercel). The Vercel default URL stays as a fallback.

## 2. Look and feel

Dark, calm, scientific. The sky images are the hero, so the UI around them stays quiet: deep teal-black surfaces, one cool interactive colour, one warm accent reserved for **things that moved or changed**. No neon glows, no gradients behind data, no NASA insignia.

## 3. Colour palette ("Deep Infrared")

Built from the deep-teal palette (`#05161A → #6DA5C0`) with a burnt-orange accent taken from the teal-and-orange palette (`#0F3D3E / #C6601F`), lightened for contrast. All text pairs below meet WCAG AA (4.5:1) on `bg`.

| Token | Hex | Use | Contrast on bg |
|---|---|---|---|
| `bg` | `#05161A` | Page background | – |
| `surface` | `#072E33` | Panels, cards, player frame | – |
| `border` | `#294D61` | Dividers, input borders, chart grid | – |
| `primary` | `#0C7075` | Buttons (white text 5.9:1), selected states | – |
| `primary-bright` | `#14B8A6` | Links, focus ring, active tab, slider thumb | 7.4 |
| `primary-mid` | `#0F969C` | Hover, secondary chart lines | 5.2 |
| `text` | `#E6F1F2` | Body text, headings | 16.0 |
| `text-muted` | `#6DA5C0` | Labels, metadata, captions | 6.9 |
| `neutral` | `#9BA8AB` | Disabled, "can't tell" | 7.6 |
| `accent` | `#E07A35` | Movers, change highlights, the "moved" marker | 6.2 |
| `sand` | `#EADCC8` | Rare emphasis (numbers in the verdict card) | 13.7 |

**Semantic colours** (always with an icon and a word, never colour alone):

| Meaning | Colour | Icon + word |
|---|---|---|
| Opinions agree | `#14B8A6` | ✓ Agree |
| Opinions disagree | `#E07A35` | ✕ Disagree |
| Can't tell | `#9BA8AB` | ? Can't tell |
| Saturated pixels (flag overlay) | `#F4A62A` | legend: "Saturated" |
| Transient / cosmic ray (flag overlay) | `#F04770` | legend: "Cosmic ray" |
| Other flagged pixels | `#FFD167` | legend: "Flagged" |

**Sky images:** greyscale (asinh stretch) by default; optional `inferno` colormap. Detector colour composite stays fixed: D1+D2 blue, D3+D4 green, D5+D6 red (doc 02).

**Spectrum chart, one colour per epoch:** Okabe–Ito colour-blind-safe set in order: `#56B4E9`, `#E69F00`, `#009E73`, `#F0E442`, `#CC79A7`, `#D55E00`. Rejected points: hollow `#9BA8AB` with a tooltip giving the reason.

## 4. Typography

- Headings: **Space Grotesk** (600). Body and UI: **IBM Plex Sans** (400/500). Numbers, coordinates and hex codes: **IBM Plex Mono**.
- **Never Inter.**
- Scale: 12 / 14 / 16 (body) / 20 / 24 / 32 / 40 px. Line height 1.5 body, 1.2 headings.
- Coordinates always in mono, with units: `RA 269.4521°  Dec +4.6934°`.

## 5. Layout and components

- Desktop: player left (about 60 %), side panel right (spectrum, Two Opinions, metadata). Mobile: stacked; player first.
- Radius 12 px on panels, 8 px on controls, full pill on toggles. Spacing on a 4 px grid (8, 12, 16, 24, 32).
- Focus ring 2 px `primary-bright`, always visible. Tap targets at least 44 px.
- Motion: 150–200 ms ease-out for UI; the time-lapse itself is user-controlled (no auto-play loops on page load beyond the first benchmark).
- Copy follows doc 04 §8: "consistent with", never "discovered" or "confirmed".

## 6. Reference sites (what to borrow from each)

| Site | Borrow |
|---|---|
| [ESASky](https://sky.esa.int) | Multi-mission overlays, layer toggles, clean dark sky UI |
| [Legacy Survey Viewer](https://www.legacysurvey.org/viewer) | Fast, simple sky viewer; URL holds the whole view |
| [WiseView (Backyard Worlds)](http://byw.tools/wiseview) | The blink tool our users already know; keep blinking that simple |
| [Aladin Lite](https://aladin.cds.unistra.fr/AladinLite/) | Our context panel; match its controls rather than fight them |
| [NASA Eyes on the Solar System](https://eyes.nasa.gov/apps/solar-system/) | Calm dark space UI, good onboarding/tour pattern (no insignia) |
| [Linear](https://linear.app) | Dark-mode polish: spacing, muted borders, crisp type |
| [Vercel dashboard](https://vercel.com) | Status badges, empty/loading/error states |
| [Observable Plot gallery](https://observablehq.com/@observablehq/plot-gallery) | Clean scientific charts for the spectrum |
| [Figma colour combinations](https://www.figma.com/resource-library/color-combinations/) | Alternatives if we tweak: "Blue eclipse", "Under the moonlight", "Ocean tide" |

## 7. Implementation

- Tokens live as CSS variables in `web/src/styles/tokens.css` (and the Tailwind theme if Tailwind is used). Components never use raw hex.
- One dark theme only for the hackathon. No light mode.
- Check every new screen with Lighthouse accessibility ≥ 90.
