import type { Grid, Overlays } from "@/types/contracts";

export type Marker = { catalog: string; id: string; x: number; y: number; mag: number | null };

const D2R = Math.PI / 180;

/**
 * Sky position -> 0-based pixel on the north-up TAN grid of a time-lapse (the same projection as astropy's
 * RA---TAN/DEC--TAN with cdelt = [-s, s]); +y is north, like Frame.target_xy. Null if behind the tangent point.
 */
export function skyToGrid(raDeg: number, decDeg: number, grid: Grid): [number, number] | null {
  const [ra0, dec0] = grid.crval_deg.map((v) => v * D2R) as [number, number];
  const ra = raDeg * D2R;
  const dec = decDeg * D2R;
  const cosc = Math.sin(dec0) * Math.sin(dec) + Math.cos(dec0) * Math.cos(dec) * Math.cos(ra - ra0);
  if (cosc <= 0) return null;
  const xi = (Math.cos(dec) * Math.sin(ra - ra0)) / cosc / D2R;
  const eta = ((Math.cos(dec0) * Math.sin(dec) - Math.sin(dec0) * Math.cos(dec) * Math.cos(ra - ra0)) / cosc) / D2R;
  const s = grid.cdelt_deg;
  return [grid.crpix[0] - 1 - xi / s, grid.crpix[1] - 1 + eta / s];
}

/** Position at the observing date closest to `mjd` (positions are baked per day of observation). */
export function positionNear(atMjd: Record<string, number[]>, mjd: number): number[] | null {
  let best: number[] | null = null;
  let gap = Infinity;
  for (const [k, v] of Object.entries(atMjd)) {
    const d = Math.abs(Number(k) - mjd);
    if (d < gap) {
      gap = d;
      best = v;
    }
  }
  return best;
}

/** Catalogue markers inside the grid for one frame date. */
export function markersFor(overlays: Overlays, grid: Grid, mjd: number): Marker[] {
  const [w, h] = grid.naxis;
  const out: Marker[] = [];
  for (const cat of overlays.catalogs) {
    for (const src of cat.sources) {
      const [ra = src.ra, dec = src.dec] = positionNear(src.at_mjd, mjd) ?? [];
      const xy = skyToGrid(ra, dec, grid);
      if (!xy) continue;
      const [x, y] = xy;
      if (x < -0.5 || y < -0.5 || x > w - 0.5 || y > h - 0.5) continue;
      out.push({ catalog: cat.name, id: src.id, x, y, mag: src.mag });
    }
  }
  return out;
}

export function parseOverlays(body: unknown): Overlays | null {
  if (typeof body !== "object" || body === null) return null;
  const b = body as Record<string, unknown>;
  if (b.schema_version !== "1.0" || !Array.isArray(b.catalogs)) return null;
  return body as Overlays;
}
