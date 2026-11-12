import { describe, expect, it } from "vitest";
import { gainFor, pitchHz } from "./sound";

describe("sonification mapping", () => {
  it("maps short wavelengths to high notes", () => {
    expect(pitchHz(0.75)).toBeCloseTo(880, 6);
    expect(pitchHz(5)).toBeCloseTo(220, 6);
    expect(pitchHz(2)).toBeLessThan(pitchHz(1));
    expect(pitchHz(null)).toBe(440);
  });
  it("keeps the gain gentle and ordered by brightness", () => {
    expect(gainFor(0)).toBeCloseTo(0.03, 6);
    expect(gainFor(255)).toBeCloseTo(0.25, 6);
    expect(gainFor(300)).toBeCloseTo(0.25, 6);
    expect(gainFor(10)).toBeLessThan(gainFor(200));
  });
});
