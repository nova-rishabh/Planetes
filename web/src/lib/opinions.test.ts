/* Wording tests: inputs are shape-only, to check the sentences follow docs/04 §8. */
import { describe, expect, it } from "vitest";
import type { MotionOpinion, SpectrumOpinion } from "@/types/contracts";
import { distanceText, motionLines, parseOpinions, spectrumLines, verdictView } from "./opinions";

const none = { lo: null, hi: null, unit: null } as const;
const motion = (o: Partial<MotionOpinion>): MotionOpinion => ({
  kind: "proper_motion", value: 1, unit: "arcsec/yr", err: 0.1, pa_deg: null, distance: none,
  truth: { value: null, source: null }, quality: "good", method: "line fit", ...o,
});
const spec = (o: Partial<SpectrumOpinion>): SpectrumOpinion => ({
  kind: "template", class: null, temperature_k: null, distance: none, quality: "fair", method: "template χ²", ...o,
});

describe("opinion wording", () => {
  it("formats distances as ranges", () => {
    expect(distanceText({ lo: 3.2, hi: 4.1, unit: "pc" })).toBe("about 3.2–4.1 pc");
    expect(distanceText(none)).toBeNull();
  });

  it("says what was measured, with its error and source", () => {
    const m = motionLines(motion({ value: 2.5, err: 0.25, truth: { value: 2.4, source: "Gaia DR3" } }));
    expect(m.headline).toBe("Moves 2.5 ± 0.25 ″/yr");
    expect(m.details).toContain("Catalogue value: 2.4 ″/yr (Gaia DR3)");
    expect(motionLines(motion({ kind: "unknown", value: null })).headline).toBe("Motion could not be measured");
  });

  it("uses 'consistent with' and never claims a discovery", () => {
    const all = [
      spectrumLines(spec({ class: "T8" })).headline,
      verdictView({ label: "agree", class: "brown_dwarf", confidence: null, reasons: [] }).headline,
      verdictView({ label: "disagree", class: "unknown", confidence: null, reasons: [] }).headline,
      verdictView({ label: "cant_tell", class: "unknown", confidence: null, reasons: [] }).headline,
    ];
    expect(all[0]).toBe("Spectrum consistent with type T8");
    expect(all[1]).toBe("The two opinions agree: consistent with a brown dwarf");
    expect(all[2]).toContain("needs follow-up");
    for (const line of all) expect(line).not.toMatch(/discover|confirm/i);
  });

  it("checks the Opinions shape", () => {
    expect(parseOpinions({ schema_version: "1.0", motion: {}, spectrum: {}, verdict: {} })).not.toBeNull();
    expect(parseOpinions({ schema_version: "1.0", motion: {} })).toBeNull();
  });
});
