/**
 * Plain-language wording for the Two Opinions panel. Follows docs/04 §8: "consistent with", never
 * "discovered" or "confirmed"; always the measurement, its uncertainty and the comparison source.
 */

import type { Distance, MotionOpinion, Opinions, SpectrumOpinion, Verdict } from "@/types/contracts";

const CLASS_NAME: Record<Verdict["class"], string> = {
  nearby_star: "a nearby star",
  brown_dwarf: "a brown dwarf",
  asteroid: "an asteroid",
  variable: "a variable star",
  artifact: "an image artifact",
  unknown: "an unexplained object",
};

const unitText = (u: string | null) => (u === "arcsec/yr" ? "″/yr" : u === "arcsec/hr" ? "″/hr" : "");

/** Three significant figures, no trailing zeros; whole numbers from 100 up. */
function num(v: number): string {
  return Math.abs(v) >= 100 ? v.toFixed(0) : Number(v.toPrecision(3)).toString();
}

export function distanceText(d: Distance): string | null {
  if (d.lo === null && d.hi === null) return null;
  const unit = d.unit ?? "";
  if (d.lo !== null && d.hi !== null) return `about ${num(d.lo)}–${num(d.hi)} ${unit}`.trim();
  return d.lo !== null ? `more than ${num(d.lo)} ${unit}`.trim() : `less than ${num(d.hi!)} ${unit}`.trim();
}

export interface OpinionLines {
  headline: string;
  details: string[];
}

export function motionLines(m: MotionOpinion): OpinionLines {
  const u = unitText(m.unit);
  let headline: string;
  if (m.kind === "unknown" || m.value === null) headline = "Motion could not be measured";
  else if (m.kind === "static") headline = m.err !== null ? `No motion seen (below ${num(m.err)} ${u})` : "No motion seen";
  else headline = `Moves ${num(m.value)}${m.err !== null ? ` ± ${num(m.err)}` : ""} ${u}${m.pa_deg !== null ? ` toward PA ${m.pa_deg.toFixed(0)}°` : ""}`;
  const details: string[] = [];
  const d = distanceText(m.distance);
  if (d) details.push(`Distance from the motion: ${d}`);
  if (m.truth.value !== null) details.push(`Catalogue value: ${num(m.truth.value)} ${u}${m.truth.source ? ` (${m.truth.source})` : ""}`);
  details.push(`Quality: ${m.quality} · ${m.method}`);
  return { headline, details };
}

export function spectrumLines(s: SpectrumOpinion): OpinionLines {
  let headline: string;
  if (s.kind === "none") headline = "The spectrum can't tell";
  else if (s.kind === "thermal")
    headline = s.temperature_k !== null ? `Warmth consistent with about ${s.temperature_k.toFixed(0)} K` : "Thermal signal too weak to read";
  else headline = s.class ? `Spectrum consistent with type ${s.class}` : "No template matched well";
  const details: string[] = [];
  const d = distanceText(s.distance);
  if (d) details.push(`Distance from the spectrum: ${d}`);
  details.push(`Quality: ${s.quality} · ${s.method}`);
  return { headline, details };
}

export interface VerdictView {
  tone: "agree" | "disagree" | "cant_tell";
  symbol: "✓" | "✕" | "?";
  headline: string;
  reasons: string[];
}

export function verdictView(v: Verdict): VerdictView {
  const what = CLASS_NAME[v.class];
  const conf = v.confidence !== null ? ` (confidence ${Math.round(v.confidence * 100)} %)` : "";
  if (v.label === "agree")
    return { tone: "agree", symbol: "✓", headline: `The two opinions agree: consistent with ${what}${conf}`, reasons: v.reasons };
  if (v.label === "disagree")
    return {
      tone: "disagree",
      symbol: "✕",
      headline: v.class === "unknown" ? "The two opinions disagree: unexplained candidate, needs follow-up" : `The two opinions disagree${conf}`,
      reasons: v.reasons,
    };
  return { tone: "cant_tell", symbol: "?", headline: "Can't tell from SPHEREx data alone", reasons: v.reasons };
}

/** Accept a body only if it has the Opinions fields the panel reads. */
export function parseOpinions(body: unknown): Opinions | null {
  if (typeof body !== "object" || body === null) return null;
  const b = body as Record<string, unknown>;
  if (b.schema_version !== "1.0") return null;
  for (const k of ["motion", "spectrum", "verdict"]) if (typeof b[k] !== "object" || b[k] === null) return null;
  return body as Opinions;
}
