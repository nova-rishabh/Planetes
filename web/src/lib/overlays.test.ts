import { describe, expect, it } from "vitest";
import type { Grid, Overlays } from "@/types/contracts";
import { markersFor, positionNear, skyToGrid } from "./overlays";

// The real Barnard's Star baked grid.
const grid: Grid = {
  projection: "TAN",
  crval_deg: [269.44622196336434, 4.768800930254672],
  crpix: [30, 30],
  cdelt_deg: 0.0017222222222222222,
  naxis: [59, 59],
  north_up: true,
};

describe("catalogue overlays", () => {
  it("projects like astropy RA---TAN/DEC--TAN", () => {
    expect(skyToGrid(grid.crval_deg[0], grid.crval_deg[1], grid)).toEqual([29, 29]);
    // astropy world_to_pixel_values for (crval + 0.03 deg RA, -0.02 deg Dec): (11.64043908, 17.38747255)
    const [x, y] = skyToGrid(grid.crval_deg[0] + 0.03, grid.crval_deg[1] - 0.02, grid)!;
    expect(x).toBeCloseTo(11.64043908, 5);
    expect(y).toBeCloseTo(17.38747255, 5);
  });

  it("uses the position at the nearest observing date and drops stars off the grid", () => {
    expect(positionNear({ "60900.1": [1, 2], "61270.4": [3, 4] }, 61268)).toEqual([3, 4]);
    const ov = {
      schema_version: "1.0",
      catalogs: [
        {
          name: "Gaia DR3",
          vizier: null,
          ref_epoch_jyear: 2016,
          sources: [
            { id: "in", ra: grid.crval_deg[0], dec: grid.crval_deg[1], pm_ra_masyr: null, pm_dec_masyr: null, mag: 10, band: "G", at_mjd: {} },
            { id: "out", ra: grid.crval_deg[0] + 1, dec: grid.crval_deg[1], pm_ra_masyr: null, pm_dec_masyr: null, mag: 10, band: "G", at_mjd: {} },
          ],
        },
      ],
    } as unknown as Overlays;
    expect(markersFor(ov, grid, 61000).map((m) => m.id)).toEqual(["in"]);
  });
});
