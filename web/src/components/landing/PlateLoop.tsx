"use client";

import { useEffect, useState } from "react";
import type { LandingFrame } from "@/lib/landing";
import { useInView, useReducedMotion } from "./useInView";

const fmt = (utc: string) =>
  new Date(utc).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" });

/**
 * A real SPHEREx time-lapse on a dark plate: frames step on their own while the plate is on screen.
 * The orange ring follows the target's position in each frame (from the baked file).
 */
export function PlateLoop({
  frames,
  naxis,
  stepMs = 450,
  label,
  showTrail = true,
}: {
  frames: LandingFrame[];
  naxis: [number, number];
  stepMs?: number;
  label: string;
  showTrail?: boolean;
}) {
  const [ref, inView] = useInView<HTMLDivElement>(true, 0.2);
  const reduced = useReducedMotion();
  const [i, setI] = useState(0);
  const [paused, setPaused] = useState(false);
  const playing = inView && !reduced && !paused && frames.length > 1;

  useEffect(() => {
    if (!playing) return;
    const t = window.setInterval(() => setI((k) => (k + 1) % frames.length), stepMs);
    return () => window.clearInterval(t);
  }, [playing, frames.length, stepMs]);

  const [w, h] = naxis;
  const f = frames[i];
  if (!f) return null;
  const toSvg = (xy: [number, number]) => [xy[0] + 0.5, h - (xy[1] + 0.5)] as const;
  const trail = showTrail
    ? frames
        .slice(0, i + 1)
        .filter((x) => x.xy)
        .map((x) => toSvg(x.xy!))
    : [];

  return (
    <figure className="lp-plate-fig" ref={ref}>
      <div className="plate lp-plate">
        {frames.map((fr, k) => (
          // eslint-disable-next-line @next/next/no-img-element -- real baked WebP frames, shown pixel-for-pixel
          <img
            key={fr.src}
            src={fr.src}
            alt={k === i ? `${label}, SPHEREx detector D${fr.detector}, ${fmt(fr.utc)}` : ""}
            aria-hidden={k !== i}
            className="lp-frame"
            data-on={k === i}
            width={w}
            height={h}
            decoding="async"
          />
        ))}
        <svg className="lp-overlay" viewBox={`0 0 ${w} ${h}`} aria-hidden="true">
          {trail.length > 1 && <polyline points={trail.map(([x, y]) => `${x},${y}`).join(" ")} className="lp-trail" />}
          {f.xy && <circle cx={toSvg(f.xy)[0]} cy={toSvg(f.xy)[1]} r={3.2} className="lp-ring" />}
        </svg>
        <button
          type="button"
          className="lp-pause"
          onClick={() => setPaused((p) => !p)}
          aria-label={paused || reduced ? "Play time-lapse" : "Pause time-lapse"}
        >
          {paused || reduced ? "▶" : "❚❚"}
        </button>
      </div>
      <figcaption className="lp-cap mono">
        <span>{fmt(f.utc)}</span>
        <span>D{f.detector}</span>
        <span>{f.wavelength_um ? `${f.wavelength_um.toFixed(2)} µm` : ""}</span>
        <span>
          {i + 1}/{frames.length}
        </span>
      </figcaption>
      {reduced && frames.length > 1 && (
        <input
          type="range"
          min={0}
          max={frames.length - 1}
          value={i}
          onChange={(e) => setI(Number(e.target.value))}
          aria-label="Step through frames"
          className="lp-scrub"
        />
      )}
    </figure>
  );
}
