"use client";

import { useEffect, useRef } from "react";
import { useReducedMotion } from "./useInView";

const GLYPHS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789·µ–";

/** Text that resolves from scrambled glyphs, left to right, once on load. The server renders the final text. */
export function ScrambleText({ text, durationMs = 1100 }: { text: string; durationMs?: number }) {
  const el = useRef<HTMLSpanElement>(null);
  const reduced = useReducedMotion();
  useEffect(() => {
    const node = el.current;
    if (!node || reduced) return;
    let raf = 0;
    const t0 = performance.now();
    const step = (now: number) => {
      const t = Math.min(1, (now - t0) / durationMs);
      const fixed = Math.floor(t * text.length);
      let out = text.slice(0, fixed);
      for (let i = fixed; i < text.length; i++) {
        const c = text[i]!;
        out += c === " " ? " " : GLYPHS[Math.floor(Math.random() * GLYPHS.length)];
      }
      node.textContent = out;
      if (t < 1) raf = requestAnimationFrame(step);
      else node.textContent = text;
    };
    raf = requestAnimationFrame(step);
    return () => {
      cancelAnimationFrame(raf);
      node.textContent = text;
    };
  }, [text, durationMs, reduced]);
  return (
    <>
      <span className="sr-only">{text}</span>
      <span ref={el} aria-hidden="true">
        {text}
      </span>
    </>
  );
}
