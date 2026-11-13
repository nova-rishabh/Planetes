/**
 * Build-time data for the landing page. Everything comes from the baked benchmark files in public/data/targets
 * (real SPHEREx frames and measurements). A missing file gives null so the page shows nothing rather than a guess.
 */
import { readFileSync } from "node:fs";
import { join } from "node:path";

export type LandingFrame = {
  src: string; // public URL of the WebP
  utc: string;
  detector: number;
  wavelength_um: number | null;
  xy: [number, number] | null; // target pixel, 0-based, y north (as in the baked file)
  saturated: boolean;
  obs_id: string;
};

export type LandingTarget = { id: string; naxis: [number, number]; cdeltArcsec: number; frames: LandingFrame[] };

type BakedFrame = {
  obs_id: string;
  utc: string;
  detector: number;
  wavelength_um: number | null;
  image_url: string;
  target_xy: [number, number] | null;
  saturated_near_center: boolean;
  epoch_index: number;
};

const ROOT = join(process.cwd(), "public", "data", "targets");

function readJson<T>(...parts: string[]): T | null {
  try {
    return JSON.parse(readFileSync(join(ROOT, ...parts), "utf8")) as T;
  } catch {
    return null;
  }
}

export function loadTarget(id: string): LandingTarget | null {
  const d = readJson<{ grid: { naxis: [number, number]; cdelt_deg: number }; frames: BakedFrame[] }>(
    id,
    "timelapse_exposures.json",
  );
  if (!d) return null;
  const frames = [...d.frames]
    .sort((a, b) => a.utc.localeCompare(b.utc))
    .map((f) => ({
      src: `/data/targets/${id}/${f.image_url.replace(/^\.\//, "")}`,
      utc: f.utc,
      detector: f.detector,
      wavelength_um: f.wavelength_um,
      xy: f.target_xy,
      saturated: f.saturated_near_center,
      obs_id: f.obs_id,
    }));
  return { id, naxis: d.grid.naxis, cdeltArcsec: d.grid.cdelt_deg * 3600, frames };
}

/** All frames of the detector with the most frames, oldest first: a clean single-colour time-lapse. */
export function oneDetectorRun(t: LandingTarget): LandingFrame[] {
  const counts = new Map<number, number>();
  for (const f of t.frames) counts.set(f.detector, (counts.get(f.detector) ?? 0) + 1);
  const det = [...counts.entries()].sort((a, b) => b[1] - a[1])[0]?.[0];
  return t.frames.filter((f) => f.detector === det);
}

/** Earliest and latest frame on the same detector, and how far the target moved between them (arcsec). */
export function blinkPair(t: LandingTarget): { a: LandingFrame; b: LandingFrame; movedArcsec: number | null } | null {
  const run = oneDetectorRun(t);
  const a = run[0];
  const b = run[run.length - 1];
  if (!a || !b || a === b) return null;
  const moved =
    a.xy && b.xy ? Math.hypot(b.xy[0] - a.xy[0], b.xy[1] - a.xy[1]) * t.cdeltArcsec : null;
  return { a, b, movedArcsec: moved };
}

/** One frame per detector D1..D6, each the earliest on that detector: the same patch in six colour ranges. */
export function acrossDetectors(t: LandingTarget): LandingFrame[] {
  const out: LandingFrame[] = [];
  for (let d = 1; d <= 6; d++) {
    const f = t.frames.find((x) => x.detector === d);
    if (f) out.push(f);
  }
  return out;
}

export type LandingSpectrum = {
  points: { um: number; ujy: number; err: number; det: number }[];
  nUsed: number;
  nTotal: number;
};

export function loadSpectrum(id: string): LandingSpectrum | null {
  const d = readJson<{
    points: {
      used: boolean;
      detector: number;
      wavelength_um: number | null;
      flux_ujy: number | null;
      flux_err_ujy: number | null;
    }[];
    summary: { n_used: number; n_points: number };
  }>(id, "spectrum.json");
  if (!d) return null;
  const points = d.points
    .filter((p) => p.used && p.wavelength_um !== null && p.flux_ujy !== null)
    .map((p) => ({
      um: p.wavelength_um as number,
      ujy: p.flux_ujy as number,
      err: p.flux_err_ujy ?? 0,
      det: p.detector,
    }))
    .sort((a, b) => a.um - b.um);
  return { points, nUsed: d.summary.n_used, nTotal: d.summary.n_points };
}

export type LandingOpinions = {
  label: "agree" | "disagree" | "cant_tell";
  reasons: string[];
  motion: string | null; // e.g. "4.71 ± 0.12 ″/yr"
  spectrum: string | null; // e.g. "T3, 2.6–3.7 pc"
} | null;

/** Baked Two Opinions for a target (opinions.json, Opinions contract), if it exists. */
export function loadOpinions(id: string): LandingOpinions {
  const d = readJson<{
    verdict: { label: "agree" | "disagree" | "cant_tell"; reasons: string[] };
    motion: { value: number | null; err: number | null; unit: string | null };
    spectrum: { class: string | null; distance: { lo: number | null; hi: number | null; unit: string | null } };
  }>(id, "opinions.json");
  if (!d) return null;
  const m = d.motion;
  const s = d.spectrum;
  const unit = m.unit === "arcsec/yr" ? "″/yr" : m.unit === "arcsec/hr" ? "″/h" : "";
  const dist =
    s.distance.lo !== null && s.distance.hi !== null
      ? `${s.distance.lo.toFixed(1)}–${s.distance.hi.toFixed(1)} ${s.distance.unit ?? ""}`
      : null;
  return {
    label: d.verdict.label,
    reasons: d.verdict.reasons,
    motion: m.value !== null ? `${m.value.toFixed(2)}${m.err !== null ? ` ± ${m.err.toFixed(2)}` : ""} ${unit}` : null,
    spectrum: s.class ? [s.class, dist].filter(Boolean).join(", ") : dist,
  };
}

export const fmtDate = (utc: string): string =>
  new Date(utc).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" });
