"use client";

import dynamic from "next/dynamic";
import { useEffect, useRef, useState, type ReactNode } from "react";
import type { StackFrame } from "./three/Scene";
import { useReducedMotion } from "./useInView";

const Scene = dynamic(() => import("./three/Scene"), { ssr: false });

export type Hero3DFrame = StackFrame & {
  utc: string;
  detector: number;
  wavelength_um: number | null;
};

const fmt = (utc: string) =>
  new Date(utc).toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
    timeZone: "UTC",
  });

function hasWebGL2(): boolean {
  try {
    return !!document.createElement("canvas").getContext("webgl2");
  } catch {
    return false;
  }
}

/**
 * Scroll-driven 3D opening: the SPHEREx observatory (modelled in code), then the camera dives through the
 * telescope into a stack of real exposures of Barnard's Star, one glass plate per visit.
 * Falls back to the flat hero (children) with reduced motion, without WebGL2, or before the client loads.
 */
export function Hero3D({
  heroText,
  flat,
  frames,
  naxis,
  movedArcsec,
  days,
}: {
  heroText: ReactNode;
  flat: ReactNode;
  frames: Hero3DFrame[];
  naxis: [number, number];
  movedArcsec: number | null;
  days: number | null;
}) {
  const reduced = useReducedMotion();
  const [mode, setMode] = useState<"flat" | "3d">("flat");
  const [narrow, setNarrow] = useState(false);
  const section = useRef<HTMLElement>(null);
  const sticky = useRef<HTMLDivElement>(null);
  const tickDate = useRef<HTMLSpanElement>(null);
  const tickIdx = useRef<HTMLSpanElement>(null);
  const progress = useRef(0);

  useEffect(() => {
    // Decided after mount: the server render is always the flat hero.
    // eslint-disable-next-line react-hooks/set-state-in-effect -- one-time capability check
    setMode(!reduced && frames.length > 1 && hasWebGL2() ? "3d" : "flat");
    setNarrow(window.matchMedia("(max-width: 768px)").matches);
  }, [reduced, frames.length]);

  useEffect(() => {
    if (mode !== "3d" || !section.current) return;
    let alive = true;
    let cleanup = () => {};
    (async () => {
      const [{ gsap }, { ScrollTrigger }, { default: Lenis }] = await Promise.all([
        import("gsap"),
        import("gsap/ScrollTrigger"),
        import("lenis"),
      ]);
      if (!alive || !section.current) return;
      gsap.registerPlugin(ScrollTrigger);
      const lenis = new Lenis({ lerp: 0.09 });
      lenis.on("scroll", ScrollTrigger.update);
      const raf = (t: number) => lenis.raf(t * 1000);
      gsap.ticker.add(raf);
      gsap.ticker.lagSmoothing(0);
      const st = ScrollTrigger.create({
        trigger: section.current,
        start: "top top",
        end: "bottom bottom",
        onUpdate: (self) => {
          const p = self.progress;
          progress.current = p;
          sticky.current?.style.setProperty("--p", p.toFixed(4));
          // Which plate the camera is passing (the stack runs from p = 0.4 to 1).
          const k = Math.min(frames.length - 1, Math.max(0, Math.round(((p - 0.4) / 0.6) * (frames.length - 1))));
          const f = frames[k];
          if (f && tickDate.current && tickIdx.current) {
            tickDate.current.textContent = fmt(f.utc);
            tickIdx.current.textContent = `${k + 1}/${frames.length}`;
          }
        },
      });
      cleanup = () => {
        st.kill();
        gsap.ticker.remove(raf);
        lenis.destroy();
      };
    })();
    return () => {
      alive = false;
      cleanup();
    };
  }, [mode, frames]);

  if (mode === "flat") return <>{flat}</>;

  const first = frames[0]!;
  const last = frames[frames.length - 1]!;
  return (
    <section ref={section} className="h3d" aria-label="SPHEREx and a year of Barnard's Star">
      <div ref={sticky} className="h3d-sticky">
        <div className="h3d-canvas">
          <Scene frames={frames} naxis={naxis} progress={progress} narrow={narrow} />
        </div>
        <div className="h3d-hero app">{heroText}</div>
        <p className="h3d-label mono">SPHEREx · illustration, modelled from NASA/JPL&apos;s description</p>
        <div className="h3d-note h3d-note-a app">
          <p className="lp-step mono">A year of visits</p>
          <h2>Look up through the telescope.</h2>
          <p>
            Above it sit {frames.length} real SPHEREx exposures of Barnard&apos;s Star, one glass plate per visit, from{" "}
            {fmt(first.utc)} to {fmt(last.utc)}.
          </p>
        </div>
        <div className="h3d-note h3d-note-b app">
          <p className="lp-step mono">It moved</p>
          <h2>Follow the orange line.</h2>
          <p>
            The ring marks the star on each plate.
            {movedArcsec !== null && days !== null && (
              <>
                {" "}
                In {days} days it moved <strong className="lp-accent">{movedArcsec.toFixed(1)}″</strong>: the stars
                behind it stayed put.
              </>
            )}
          </p>
        </div>
        <p className="h3d-ticker mono" aria-live="off">
          <span ref={tickDate}>{fmt(first.utc)}</span>
          <span>
            D{first.detector}
            {first.wavelength_um ? ` · ${first.wavelength_um.toFixed(2)} µm` : ""}
          </span>
          <span ref={tickIdx}>1/{frames.length}</span>
        </p>
      </div>
    </section>
  );
}
