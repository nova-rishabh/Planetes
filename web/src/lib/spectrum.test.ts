/* Chart geometry tests. Points are shape-only inputs to the scale maths, not measurements shown anywhere. */
import { describe, expect, it } from "vitest";
import type { SpectrumPoint } from "@/types/contracts";
import { chartModel, epochIndices, niceTicks } from "./spectrum";

const BOX = { width: 500, height: 300, left: 50, right: 10, top: 10, bottom: 40 };

function pt(over: Partial<SpectrumPoint>): SpectrumPoint {
  return {
    obs_id: "ivo://test", mjd: 0, detector: 1, wavelength_um: 1, bandwidth_um: 0.02,
    flux_ujy: 0, flux_err_ujy: 1, snr: null, flags: 0, saturated: false, used: true,
    reject_reason: null, pair_id: null, method: null, ra: 0, dec: 0, ...over,
  };
}

describe("epochIndices", () => {
  it("starts a new visit after a gap", () => {
    expect(epochIndices([100, 101, 300, 102, 305])).toEqual([0, 0, 1, 0, 1]);
    expect(epochIndices([])).toEqual([]);
  });
});

describe("niceTicks", () => {
  it("gives round steps", () => {
    expect(niceTicks(0, 10)).toEqual([0, 2, 4, 6, 8, 10]);
    expect(niceTicks(-3, 7)).toEqual([-2, 0, 2, 4, 6]);
  });
});

describe("chartModel", () => {
  it("never draws points without a measured flux, and counts them", () => {
    const m = chartModel([pt({ flux_ujy: null }), pt({ wavelength_um: null }), pt({ flux_ujy: 5 })], BOX);
    expect(m.points).toHaveLength(1);
    expect(m.notMeasured).toBe(2);
  });

  it("maps wavelength left to right and flux bottom to top, with a zero line when it crosses zero", () => {
    const m = chartModel([pt({ wavelength_um: 1, flux_ujy: -2 }), pt({ wavelength_um: 4, flux_ujy: 8 })], BOX);
    const [a, b] = m.points;
    expect(a!.x).toBeLessThan(b!.x);
    expect(a!.y).toBeGreaterThan(b!.y);
    expect(m.zeroY).not.toBeNull();
    expect(m.bands.map((x) => x.label)).toEqual(["D1", "D2", "D3", "D4", "D5", "D6"]);
  });

  it("keeps the rejection reason in the label of unused points", () => {
    const m = chartModel([pt({ used: false, reject_reason: "saturated core", saturated: true, flux_ujy: 3 })], BOX);
    expect(m.points[0]!.label).toContain("not used: saturated core");
    expect(m.points[0]!.used).toBe(false);
  });

  it("scales to the used points and pins rejected outliers to the edge", () => {
    const m = chartModel([pt({ flux_ujy: 1 }), pt({ flux_ujy: 3 }), pt({ flux_ujy: -500, used: false, reject_reason: "flagged" })], BOX);
    expect(m.offScale).toBe(1);
    expect(m.points[2]!.y).toBe(BOX.height - BOX.bottom);
    expect(m.points[2]!.yLo).toBeNull();
  });
});
