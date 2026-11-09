/** The shareable view (docs/03 §2): parse from and write to URL query parameters. */

import { BENCHMARK_IDS, type BenchmarkId } from "./benchmarks";

export const MODES = ["exposures", "stacks", "difference", "sum", "color"] as const;
export type Mode = (typeof MODES)[number];

export const FOV_MIN_DEG = 0.03;
export const FOV_MAX_DEG = 0.5;
export const FOV_DEFAULT_DEG = 0.1;

export interface ViewState {
  target: BenchmarkId | null;
  ra_deg: number | null;
  dec_deg: number | null;
  fov_deg: number;
  mode: Mode;
  detectors: number[];
  frame: number;
  a: number | null;
  b: number | null;
}

export const DEFAULT_VIEW: ViewState = {
  target: null,
  ra_deg: null,
  dec_deg: null,
  fov_deg: FOV_DEFAULT_DEG,
  mode: "stacks",
  detectors: [1, 2, 3, 4, 5, 6],
  frame: 0,
  a: null,
  b: null,
};

function num(v: string | null): number | null {
  if (v === null || v.trim() === "") return null;
  const n = Number(v);
  return Number.isFinite(n) ? n : null;
}

function index(v: string | null): number | null {
  const n = num(v);
  return n !== null && Number.isInteger(n) && n >= 0 ? n : null;
}

/** Invalid or out-of-range values fall back to the defaults instead of breaking the page. */
export function parseView(params: URLSearchParams): ViewState {
  const target = params.get("target");
  const ra = num(params.get("ra"));
  const dec = num(params.get("dec"));
  const fov = num(params.get("fov"));
  const mode = params.get("mode");
  const det = (params.get("det") ?? "")
    .split(",")
    .map(Number)
    .filter((d) => Number.isInteger(d) && d >= 1 && d <= 6);
  const hasPos = ra !== null && dec !== null && ra >= 0 && ra < 360 && dec >= -90 && dec <= 90;
  return {
    target: BENCHMARK_IDS.includes(target as BenchmarkId) ? (target as BenchmarkId) : null,
    ra_deg: hasPos ? ra : null,
    dec_deg: hasPos ? dec : null,
    fov_deg: fov !== null && fov >= FOV_MIN_DEG && fov <= FOV_MAX_DEG ? fov : FOV_DEFAULT_DEG,
    mode: MODES.includes(mode as Mode) ? (mode as Mode) : DEFAULT_VIEW.mode,
    detectors: det.length ? [...new Set(det)].sort() : DEFAULT_VIEW.detectors,
    frame: index(params.get("frame")) ?? 0,
    a: index(params.get("a")),
    b: index(params.get("b")),
  };
}

/** Only non-default values are written, so links stay short. */
export function serializeView(v: ViewState): URLSearchParams {
  const p = new URLSearchParams();
  if (v.target) p.set("target", v.target);
  else if (v.ra_deg !== null && v.dec_deg !== null) {
    p.set("ra", String(Number(v.ra_deg.toFixed(6))));
    p.set("dec", String(Number(v.dec_deg.toFixed(6))));
  }
  if (v.fov_deg !== FOV_DEFAULT_DEG) p.set("fov", String(v.fov_deg));
  if (v.mode !== DEFAULT_VIEW.mode) p.set("mode", v.mode);
  if (v.detectors.join(",") !== DEFAULT_VIEW.detectors.join(",")) p.set("det", v.detectors.join(","));
  if (v.frame) p.set("frame", String(v.frame));
  if (v.a !== null) p.set("a", String(v.a));
  if (v.b !== null) p.set("b", String(v.b));
  return p;
}
