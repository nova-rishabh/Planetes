"use client";

import { useEffect, useState, type RefObject } from "react";
import { useReducedMotion } from "../useInView";

/**
 * Shared scroll machinery for the 3D scenes: one Lenis smooth-scroller and GSAP ScrollTrigger for the whole page,
 * created when the first scene needs it and torn down when the last one unmounts.
 */
type Tools = {
  ScrollTrigger: typeof import("gsap/ScrollTrigger").ScrollTrigger;
};
let tools: Promise<Tools> | null = null;
let users = 0;
let teardown: (() => void) | null = null;

async function acquire(): Promise<Tools> {
  users++;
  if (!tools) {
    tools = (async () => {
      const [{ gsap }, { ScrollTrigger }, { default: Lenis }] = await Promise.all([
        import("gsap"),
        import("gsap/ScrollTrigger"),
        import("lenis"),
      ]);
      gsap.registerPlugin(ScrollTrigger);
      const lenis = new Lenis({ lerp: 0.09 });
      lenis.on("scroll", ScrollTrigger.update);
      const raf = (t: number) => lenis.raf(t * 1000);
      gsap.ticker.add(raf);
      gsap.ticker.lagSmoothing(0);
      teardown = () => {
        gsap.ticker.remove(raf);
        lenis.destroy();
      };
      return { ScrollTrigger };
    })();
  }
  return tools;
}

function release() {
  users--;
  if (users <= 0) {
    teardown?.();
    teardown = null;
    tools = null;
    users = 0;
  }
}

/** Calls onUpdate(progress 0..1) as the section scrolls past (pinned from its top to its bottom). */
export function useScrollProgress(
  active: boolean,
  section: RefObject<HTMLElement | null>,
  onUpdate: (p: number) => void,
) {
  useEffect(() => {
    if (!active || !section.current) return;
    let alive = true;
    let kill = () => {};
    acquire().then(({ ScrollTrigger }) => {
      if (!alive || !section.current) return;
      const st = ScrollTrigger.create({
        trigger: section.current,
        start: "top top",
        end: "bottom bottom",
        onUpdate: (self) => onUpdate(self.progress),
      });
      onUpdate(st.progress);
      kill = () => st.kill();
    });
    return () => {
      alive = false;
      kill();
      release();
    };
  }, [active, section, onUpdate]);
}

function hasWebGL2(): boolean {
  try {
    return !!document.createElement("canvas").getContext("webgl2");
  } catch {
    return false;
  }
}

/**
 * Whether a 3D scene can run, and when to start it. The 3D layout is the first render (no layout jump); it
 * switches to flat with reduced motion or without WebGL2. The WebGL scene itself starts once the page is idle;
 * phones wait for the first touch or scroll (or a few seconds), since parsing three.js is slow on them.
 */
export function use3DMode(possible: boolean) {
  const reduced = useReducedMotion();
  const [mode, setMode] = useState<"flat" | "3d">(possible ? "3d" : "flat");
  const [narrow, setNarrow] = useState(false);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- one-time capability check after mount
    setMode(possible && !reduced && hasWebGL2() ? "3d" : "flat");
    setNarrow(window.matchMedia("(max-width: 768px)").matches);
  }, [possible, reduced]);

  useEffect(() => {
    if (mode !== "3d") return;
    let done = false;
    const start = () => {
      if (done) return;
      done = true;
      setReady(true);
    };
    const phone = window.matchMedia("(max-width: 768px)").matches;
    const events = ["pointerdown", "touchstart", "wheel", "scroll", "keydown"] as const;
    for (const e of events) window.addEventListener(e, start, { once: true, passive: true });
    const w = window as Window & { requestIdleCallback?: (cb: () => void, o?: { timeout: number }) => number };
    let idle = 0;
    const timer = window.setTimeout(
      () => {
        if (w.requestIdleCallback) idle = w.requestIdleCallback(start, { timeout: 2000 });
        else start();
      },
      phone ? 3500 : 0,
    );
    return () => {
      window.clearTimeout(timer);
      if (idle) window.cancelIdleCallback?.(idle);
      for (const e of events) window.removeEventListener(e, start);
    };
  }, [mode]);

  return { mode, narrow, ready };
}
