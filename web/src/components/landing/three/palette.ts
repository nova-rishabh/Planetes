import { Color } from "three";

/** Design tokens (docs/09) read from CSS at runtime, so the 3D scene never carries its own colours. */
export type Palette = {
  bg: Color;
  surface: Color;
  ink: Color;
  ui: Color;
  plate: Color;
  accent: Color;
  border: Color;
};

function token(name: string): Color {
  const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return new Color(v || undefined);
}

export function readPalette(): Palette {
  return {
    bg: token("--bg"),
    surface: token("--surface"),
    ink: token("--ink"),
    ui: token("--ui"),
    plate: token("--plate"),
    accent: token("--accent-fill"),
    border: token("--border"),
  };
}

/** One colour per detector D1..D6, from the colour-blind-safe series tokens (--epoch-1..6). */
export function readDetectorColours(): Color[] {
  return [1, 2, 3, 4, 5, 6].map((k) => token(`--epoch-${k}`));
}
