import { describe, expect, it } from "vitest";
import { abMag, evaluate, reflectedUjy, sixMonthShiftArcsec, stackedDepthAb, vMagnitude } from "./planetx";

describe("planet x physics (same anchors as pipeline/tests/test_planet_x.py)", () => {
  it("recovers Neptune", () => {
    expect(vMagnitude(24622, 0.41, 29)).toBeCloseTo(7.8, 6);
    expect(Math.abs(abMag(reflectedUjy(0.55, 24622, 0.41, 29)) - 7.8)).toBeLessThan(0.1);
  });
  it("scales the right way", () => {
    const base = vMagnitude(10000, 0.3, 300);
    expect(vMagnitude(20000, 0.3, 300)).toBeCloseTo(base - 5 * Math.log10(2), 6);
    expect(vMagnitude(10000, 0.3, 600)).toBeCloseTo(base + 10 * Math.log10(2), 6);
  });
  it("puts a Planet-Nine-like case at V 21-25", () => {
    for (const r of [550, 700, 1000]) {
      const v = vMagnitude(16600, 0.5, r);
      expect(v).toBeGreaterThanOrEqual(21);
      expect(v).toBeLessThanOrEqual(25);
    }
  });
  it("stacks and shifts", () => {
    expect(stackedDepthAb(18.5, 100)).toBeCloseTo(21, 6);
    expect(sixMonthShiftArcsec(500)).toBeCloseTo(825.06, 1);
    expect(evaluate(16600, 0.5, 700, 40, 1).bands.some((b) => b.above)).toBe(false);
  });
});
