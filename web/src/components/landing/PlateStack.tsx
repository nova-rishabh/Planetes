"use client";

import { useEffect, useRef, useState } from "react";
import type { LandingFrame } from "@/lib/landing";
import { useReducedMotion } from "./useInView";

const fmt = (utc: string) =>
  new Date(utc).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" });

/** Ring position on a plate, in % (baked xy is 0-based with y north-up). */
function ringAt(f: LandingFrame, naxis: [number, number]) {
  if (!f.xy) return null;
  return { left: ((f.xy[0] + 0.5) / naxis[0]) * 100, top: 100 - ((f.xy[1] + 0.5) / naxis[1]) * 100 };
}

function Plate({
  f,
  naxis,
  k,
  cross,
  className,
  label = true,
}: {
  f: LandingFrame;
  naxis: [number, number];
  k: number;
  cross?: { left: number; top: number } | null;
  className?: string;
  label?: boolean;
}) {
  const r = ringAt(f, naxis);
  return (
    <div className={`ps-plate ${className ?? ""}`} style={{ ["--k" as string]: k }}>
      {/* eslint-disable-next-line @next/next/no-img-element -- real baked SPHEREx WebP, shown pixel for pixel */}
      <img src={f.src} alt="" width={naxis[0]} height={naxis[1]} decoding="async" />
      {cross && <i className="ps-cross" style={{ left: `${cross.left}%`, top: `${cross.top}%` }} />}
      {r && <i className="ps-ring" style={{ left: `${r.left}%`, top: `${r.top}%` }} />}
      {label && <span className="ps-date mono">{fmt(f.utc)}</span>}
    </div>
  );
}

/**
 * Hero figure: real SPHEREx exposures of one target as a tower of printed plates in CSS 3D. The top plate plays
 * the whole time-lapse; the ring marks the measured position in each frame.
 */
export function PlateStack({ frames, naxis, label }: { frames: LandingFrame[]; naxis: [number, number]; label: string }) {
  const reduced = useReducedMotion();
  const [i, setI] = useState(0);
  useEffect(() => {
    if (reduced || frames.length < 2) return;
    const t = window.setInterval(() => setI((k) => (k + 1) % frames.length), 650);
    return () => window.clearInterval(t);
  }, [reduced, frames.length]);
  // Six plates under the top one, spread evenly through the run, oldest at the bottom.
  const under = Array.from({ length: Math.min(6, frames.length - 1) }, (_, j) =>
    Math.round((j * (frames.length - 1)) / Math.max(1, Math.min(6, frames.length - 1))),
  );
  const top = frames[i]!;
  return (
    <figure className="ps" aria-label={`${label}: ${frames.length} real SPHEREx exposures stacked by date`}>
      <div className="ps-scene">
        <div className="ps-tower">
          {under.map((idx, k) => (
            <Plate key={frames[idx]!.src} f={frames[idx]!} naxis={naxis} k={k} label={k === 0} />
          ))}
          <Plate f={top} naxis={naxis} k={under.length} className="ps-top" />
        </div>
      </div>
    </figure>
  );
}

/**
 * Scroll scene: a flip-book. All exposures sit in one stack, oldest on top; scrolling peels them off one by one so
 * each is seen whole. The cross on every plate marks where the target sat in the first frame, so its drift shows.
 */
export function PlateFan({ frames, naxis }: { frames: LandingFrame[]; naxis: [number, number] }) {
  const box = useRef<HTMLDivElement>(null);
  const counter = useRef<HTMLSpanElement>(null);
  const date = useRef<HTMLSpanElement>(null);
  const reduced = useReducedMotion();
  const first = ringAt(frames[0]!, naxis);

  useEffect(() => {
    const el = box.current;
    if (!el) return;
    let raf = 0;
    const update = () => {
      raf = 0;
      const r = el.getBoundingClientRect();
      const span = el.offsetHeight - window.innerHeight;
      const p = reduced ? 1 : Math.min(1, Math.max(0, -r.top / Math.max(1, span)));
      // --pos runs 0..n-1: plates above it peel away, so each exposure is seen whole in turn.
      el.style.setProperty("--pos", (p * (frames.length - 1)).toFixed(3));
      const k = Math.min(frames.length - 1, Math.round(p * (frames.length - 1)));
      if (counter.current) counter.current.textContent = `${String(k + 1).padStart(2, "0")} / ${frames.length}`;
      if (date.current) date.current.textContent = fmt(frames[k]!.utc);
    };
    const onScroll = () => {
      if (!raf) raf = requestAnimationFrame(update);
    };
    update();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll);
    return () => {
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onScroll);
      if (raf) cancelAnimationFrame(raf);
    };
  }, [frames, reduced]);

  return (
    <div ref={box} className="pf" style={{ ["--n" as string]: frames.length }}>
      <div className="pf-sticky">
        <div className="pf-scene" aria-hidden="true">
          <div className="pf-row">
            {frames.map((f, k) => (
              <Plate key={f.src} f={f} naxis={naxis} k={k} cross={first} className="pf-plate" />
            ))}
          </div>
        </div>
        <p className="pf-read mono">
          <span ref={counter}>01 / {frames.length}</span>
          <span ref={date}>{fmt(frames[0]!.utc)}</span>
          <span>D{frames[0]!.detector}</span>
        </p>
      </div>
    </div>
  );
}
