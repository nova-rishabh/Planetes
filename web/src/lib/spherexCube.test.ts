import { describe, expect, it } from "vitest";
import { CHANNEL_DETECTOR, CHANNEL_UM, locate, tileUrl } from "./spherexCube";

// Expected values were computed with astropy-healpix and checked against each tile's own HPX WCS.
const CASES: [number, number, number, number, number][] = [
  [269.452, 4.6934, 7945, 118, 81],
  [331.0765, -56.7938, 11391, 409, 101],
  [133.79, -7.245, 10226, 233, 206],
  [10, 40, 654, 8, 446],
  [200, -70, 10381, 499, 300],
];

describe("spherexCube.locate", () => {
  it.each(CASES)("ra %f dec %f -> tile %i row %i col %i", (ra, dec, tile, row, col) => {
    expect(locate(ra, dec)).toEqual({ tile, row, col });
  });
  it("builds the open-data tile URL", () => {
    expect(tileUrl(11391)).toMatch(/Norder5\/Dir10000\/Npix11391_cube\.fits$/);
  });
  it("has 102 channels in rising wavelength, 17 per detector", () => {
    expect(CHANNEL_UM).toHaveLength(102);
    expect(CHANNEL_DETECTOR).toHaveLength(102);
    expect(CHANNEL_UM.every((w, i) => i === 0 || w > CHANNEL_UM[i - 1]!)).toBe(true);
    for (let d = 1; d <= 6; d++) expect(CHANNEL_DETECTOR.filter((x) => x === d)).toHaveLength(17);
  });
});
