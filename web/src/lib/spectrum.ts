/** Turns a SpectrumResult into chart geometry. Pure, so the scales and grouping are testable. */

import type { SpectrumPoint } from "@/types/contracts";

/** SPHEREx covers 0.75–5.00 µm; the axis is fixed so spectra of different objects compare at a glance. */
export const WAVELENGTH_RANGE_UM: [number, number] = [0.7, 5.1];
/** Detector band edges (docs/02), used for the D1–D6 labels under the axis. */
export const BAND_EDGES_UM = [0.75, 1.11, 1.64, 2.42, 3.82, 4.42, 5.0] as const;
export const EPOCH_COLOURS = 6;

/** Index of the SPHEREx visit each date belongs to: a new visit starts after a gap longer than gapDays. */
export function epochIndices(mjds: number[], gapDays = 30): number[] {
  const order = mjds.map((m, i) => [m, i] as const).sort((a, b) => a[0] - b[0]);
  const out = new Array<number>(mjds.length).fill(0);
  let epoch = 0;
  order.forEach(([m, i], k) => {
    if (k > 0 && m - order[k - 1]![0] > gapDays) epoch++;
    out[i] = epoch;
  });
  return out;
}

/** About five round tick values covering [lo, hi]. */
export function niceTicks(lo: number, hi: number, count = 5): number[] {
  if (!(hi > lo)) return [lo];
  const raw = (hi - lo) / count;
  const mag = 10 ** Math.floor(Math.log10(raw));
  const step = [1, 2, 2.5, 5, 10].map((f) => f * mag).find((s) => s >= raw) ?? 10 * mag;
  const ticks: number[] = [];
  for (let v = Math.ceil(lo / step) * step; v <= hi + step * 1e-9; v += step) ticks.push(Number(v.toPrecision(12)));
  return ticks;
}

export interface ChartPoint {
  x: number;
  y: number;
  yLo: number | null;
  yHi: number | null;
  halfWidth: number;
  epoch: number;
  used: boolean;
  saturated: boolean;
  /** Outside the axis range: drawn pinned to the edge, without error bars. */
  offScale: boolean;
  label: string;
  key: string;
}

export interface ChartModel {
  points: ChartPoint[];
  xTicks: number[];
  yTicks: { value: number; y: number }[];
  zeroY: number | null;
  bands: { label: string; x0: number; x1: number }[];
  notMeasured: number;
  offScale: number;
  epochs: number;
}

export interface Box {
  width: number;
  height: number;
  left: number;
  right: number;
  top: number;
  bottom: number;
}

/** Points without a measured flux or wavelength are counted, never drawn or guessed. */
export function chartModel(points: SpectrumPoint[], box: Box): ChartModel {
  const measured = points.filter((p) => p.flux_ujy !== null && p.wavelength_um !== null);
  const epochs = epochIndices(measured.map((p) => p.mjd));
  // The axis follows the points that are used; rejected outliers would otherwise flatten the real data.
  const scaleFrom = measured.some((p) => p.used) ? measured.filter((p) => p.used) : measured;
  const ys = scaleFrom.flatMap((p) => {
    const e = p.flux_err_ujy ?? 0;
    return [p.flux_ujy! - e, p.flux_ujy! + e];
  });
  let yMin = ys.length ? Math.min(...ys) : 0;
  let yMax = ys.length ? Math.max(...ys) : 1;
  if (yMin === yMax) [yMin, yMax] = [yMin - 1, yMax + 1];
  const pad = (yMax - yMin) * 0.08;
  yMin -= pad;
  yMax += pad;

  const [x0, x1] = WAVELENGTH_RANGE_UM;
  const plotW = box.width - box.left - box.right;
  const plotH = box.height - box.top - box.bottom;
  const sx = (um: number) => box.left + ((um - x0) / (x1 - x0)) * plotW;
  const sy = (v: number) => box.top + (1 - (v - yMin) / (yMax - yMin)) * plotH;
  const syClamped = (v: number) => Math.min(Math.max(sy(v), box.top), box.top + plotH);

  const chartPoints = measured.map((p, i): ChartPoint => {
    const f = p.flux_ujy!;
    const e = p.flux_err_ujy;
    const why = p.used ? "" : ` · not used: ${p.reject_reason ?? "no reason given"}`;
    const offScale = f < yMin || f > yMax;
    return {
      x: sx(p.wavelength_um!),
      y: syClamped(f),
      yLo: e === null || offScale ? null : syClamped(f - e),
      yHi: e === null || offScale ? null : syClamped(f + e),
      offScale,
      halfWidth: p.bandwidth_um ? (sx(p.wavelength_um! + p.bandwidth_um / 2) - sx(p.wavelength_um!)) : 0,
      epoch: epochs[i]!,
      used: p.used,
      saturated: p.saturated,
      label: `${offScale ? "off scale · " : ""}${p.wavelength_um!.toFixed(3)} µm · ${f.toFixed(1)}${e !== null ? ` ± ${e.toFixed(1)}` : ""} µJy · D${p.detector}${p.saturated ? " · saturated" : ""}${why}`,
      key: `${p.obs_id}-${i}`,
    };
  });

  return {
    points: chartPoints,
    xTicks: [1, 2, 3, 4, 5].map(sx),
    yTicks: niceTicks(yMin, yMax).map((value) => ({ value, y: sy(value) })),
    zeroY: yMin < 0 && yMax > 0 ? sy(0) : null,
    bands: BAND_EDGES_UM.slice(0, -1).map((lo, i) => ({ label: `D${i + 1}`, x0: sx(lo), x1: sx(BAND_EDGES_UM[i + 1]!) })),
    notMeasured: points.length - measured.length,
    offScale: chartPoints.filter((p) => p.offScale).length,
    epochs: measured.length ? Math.max(...epochs) + 1 : 0,
  };
}
