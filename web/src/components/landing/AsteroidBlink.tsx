"use client";

import { useEffect, useState } from "react";
import type { AsteroidFigure } from "@/lib/landing";
import { useInView, useReducedMotion } from "./useInView";

/**
 * Two real SPHEREx frames of a known asteroid, flipped like a blink comparator. The ring marks the position JPL
 * predicted for the frame on screen; the dashed ring marks its predicted position in the other frame.
 */
export function AsteroidBlink({ fig }: { fig: AsteroidFigure }) {
  const [ref, inView] = useInView<HTMLDivElement>(true);
  const reduced = useReducedMotion();
  const [paused, setPaused] = useState(false);
  const [i, setI] = useState(0);
  const running = inView && !reduced && !paused;

  useEffect(() => {
    if (!running) return;
    const t = setInterval(() => setI((v) => 1 - v), 900);
    return () => clearInterval(t);
  }, [running]);

  const n = fig.grid_px;
  const pos = (xy: [number, number]) => ({ cx: ((xy[0] + 0.5) / n) * 100, cy: ((n - (xy[1] + 0.5)) / n) * 100 });
  const here = fig.frames[i]!;
  const there = fig.frames[1 - i]!;
  const a = pos(here.jpl_xy);
  const b = pos(there.jpl_xy);

  return (
    <div className="ed-ast-fig" ref={ref}>
      <div className="ed-ast-plate">
        {fig.frames.map((f, k) => (
          // eslint-disable-next-line @next/next/no-img-element -- real SPHEREx frame, drawn pixel for pixel
          <img
            key={f.image}
            src={f.image}
            alt={`SPHEREx detector ${f.detector} frame with asteroid ${fig.name}`}
            width={n}
            height={n}
            style={{ opacity: k === i ? 1 : 0 }}
          />
        ))}
        <svg viewBox="0 0 100 100" aria-hidden="true">
          <circle cx={b.cx} cy={b.cy} r={6} className="ed-ast-was" />
          <circle cx={a.cx} cy={a.cy} r={6} className="ed-ast-now" />
        </svg>
      </div>
      <div className="ed-ast-bar mono">
        <span>
          {"AB"[i]} · {here.utc.slice(11, 16)} UTC · D{here.detector} · {here.wavelength_um?.toFixed(2)} µm
        </span>
        <span className="ed-ast-btns">
          <button type="button" className="ed-btn mono" onClick={() => setI(1 - i)} aria-label="Flip to the other frame">
            Flip
          </button>
          {!reduced && (
            <button type="button" className="ed-btn mono" aria-pressed={paused} onClick={() => setPaused((p) => !p)}>
              {paused ? "Play" : "Pause"}
            </button>
          )}
        </span>
      </div>
      <p className="ed-ast-key mono">
        <span className="ed-ast-k-now" /> JPL predicted position in this frame · <span className="ed-ast-k-was" /> in the
        other frame
      </p>
    </div>
  );
}
