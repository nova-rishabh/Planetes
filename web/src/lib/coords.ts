/** Parse and format sky coordinates (ICRS, degrees). RA in sexagesimal input is in hours. */

export interface SkyPosition {
  ra_deg: number;
  dec_deg: number;
}

export type ParseResult = { ok: true; pos: SkyPosition } | { ok: false; reason: string };

const NUM = String.raw`[+-]?\d+(?:\.\d+)?`;

/** Split "a b c" / "a:b:c" / "12h34m56s" into numeric parts. */
function sexParts(text: string): number[] | null {
  const cleaned = text
    .trim()
    .replace(/[hdms°'′″"]/gi, " ")
    .replace(/:/g, " ")
    .trim();
  if (!cleaned) return null;
  const parts = cleaned.split(/\s+/);
  if (parts.length > 3 || !parts.every((p) => new RegExp(`^${NUM}$`).test(p))) return null;
  return parts.map(Number);
}

function fromSex(parts: number[], negative: boolean): number {
  const [a = 0, b = 0, c = 0] = parts.map(Math.abs);
  const value = a + b / 60 + c / 3600;
  return negative ? -value : value;
}

/** Split the input into its RA and Dec halves. */
function splitHalves(text: string): [string, string] | null {
  const t = text.trim();
  if (t.includes(",")) {
    const parts = t.split(",");
    return parts.length === 2 ? [parts[0]!.trim(), parts[1]!.trim()] : null;
  }
  // Dec starts at the first explicit sign after the RA, e.g. "17 57 48.5 +04 41 36".
  const signed = t.search(/\s[+-]/);
  if (signed > 0) return [t.slice(0, signed).trim(), t.slice(signed).trim()];
  const tokens = t.split(/\s+/);
  if (tokens.length === 2) return [tokens[0]!, tokens[1]!];
  if (tokens.length === 6) return [tokens.slice(0, 3).join(" "), tokens.slice(3).join(" ")];
  return null;
}

/**
 * Accepts decimal degrees ("269.4521 4.6934", "269.4521, -7.2"),
 * or sexagesimal with RA in hours ("17 57 48.5 +04 41 36", "17:57:48.5, +04:41:36", "17h57m48.5s +4d41m36s").
 */
export function parsePosition(text: string): ParseResult {
  const halves = splitHalves(text);
  if (!halves) return { ok: false, reason: "Type RA and Dec, e.g. 269.4521 4.6934 or 17 57 48.5 +04 41 36" };
  const [raText, decText] = halves;
  const raParts = sexParts(raText);
  const decParts = sexParts(decText);
  if (!raParts || !decParts) return { ok: false, reason: "Could not read the numbers" };

  const ra0 = raParts[0]!;
  const dec0 = decParts[0]!;
  const sexagesimal = raParts.length > 1 || decParts.length > 1 || /[hms:]/i.test(raText);
  const ra_deg = sexagesimal ? fromSex(raParts, false) * 15 : ra0;
  const dec_deg = decParts.length > 1 || /[dms:°]/i.test(decText)
    ? fromSex(decParts, decText.trim().startsWith("-"))
    : dec0;

  if (ra0 < 0) return { ok: false, reason: "RA cannot be negative" };
  if (!(ra_deg >= 0 && ra_deg < 360)) return { ok: false, reason: "RA must be 0–360° (or 0–24 h)" };
  if (!(dec_deg >= -90 && dec_deg <= 90)) return { ok: false, reason: "Dec must be between −90° and +90°" };
  return { ok: true, pos: { ra_deg, dec_deg } };
}

/** "RA 269.4521°  Dec +4.6934°" (docs/09 §4). */
export function formatPosition(pos: SkyPosition, digits = 4): string {
  const sign = pos.dec_deg < 0 ? "−" : "+";
  return `RA ${pos.ra_deg.toFixed(digits)}°  Dec ${sign}${Math.abs(pos.dec_deg).toFixed(digits)}°`;
}
