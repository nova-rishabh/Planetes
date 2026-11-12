"use client";

import { useEffect, useState } from "react";
import type { LandingFrame } from "@/lib/landing";
import { useInView, useReducedMotion } from "./useInView";

const fmt = (utc: string) =>
  new Date(utc).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" });

/** The blink comparator: two real frames of the same patch, flipped back and forth; rings mark both positions. */
export function BlinkPlate({ a, b, naxis, label }: { a: LandingFrame; b: LandingFrame; naxis: [number, number]; label: string }) {
  const [ref, inView] = useInView<HTMLDivElement>(true, 0.4);
  const reduced = useReducedMotion();
  const [showB, setShowB] = useState(false);
  const auto = inView && !reduced;

  useEffect(() => {
    if (!auto) return;
    const t = window.setInterval(() => setShowB((s) => !s), 700);
    return () => window.clearInterval(t);
  }, [auto]);

  const [w, h] = naxis;
  const pos = (f: LandingFrame) => (f.xy ? ([f.xy[0] + 0.5, h - (f.xy[1] + 0.5)] as const) : null);
  const pa = pos(a);
  const pb = pos(b);
  const cur = showB ? b : a;

  return (
    <figure className="lp-plate-fig" ref={ref}>
      <div className="plate lp-plate lp-blink">
        {[a, b].map((f, k) => (
          // eslint-disable-next-line @next/next/no-img-element -- real baked WebP frames
          <img
            key={f.src}
            src={f.src}
            alt={`${label}, ${fmt(f.utc)}`}
            className="lp-frame lp-frame-hard"
            data-on={(k === 1) === showB}
            width={w}
            height={h}
          />
        ))}
        <svg className="lp-overlay" viewBox={`0 0 ${w} ${h}`} aria-hidden="true">
          {pa && pb && <line x1={pa[0]} y1={pa[1]} x2={pb[0]} y2={pb[1]} className="lp-trail" />}
          {pa && <circle cx={pa[0]} cy={pa[1]} r={3.2} className={showB ? "lp-ghost" : "lp-ring"} />}
          {pb && <circle cx={pb[0]} cy={pb[1]} r={3.2} className={showB ? "lp-ring" : "lp-ghost"} />}
        </svg>
        <span className="lp-stamp mono" aria-live="off">
          {showB ? "B" : "A"} · {fmt(cur.utc)}
        </span>
      </div>
      <div className="lp-blink-controls">
        <button type="button" className="toggle" aria-pressed={!showB} onClick={() => setShowB(false)}>
          A · {fmt(a.utc)}
        </button>
        <button type="button" className="toggle" aria-pressed={showB} onClick={() => setShowB(true)}>
          B · {fmt(b.utc)}
        </button>
      </div>
    </figure>
  );
}
