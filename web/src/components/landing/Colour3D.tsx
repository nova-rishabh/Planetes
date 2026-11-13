"use client";

import dynamic from "next/dynamic";
import { useCallback, useRef, type ReactNode } from "react";
import type { DetectorTile, SpecPoint } from "./three/SpectrumScene";
import { use3DMode, useScrollProgress } from "./three/scroll";

const SpectrumScene = dynamic(() => import("./three/SpectrumScene"), { ssr: false });

/**
 * Scroll-driven colour scene: ε Indi B's six detector frames fly in and light up, every measured point leaves its
 * detector for its place in the spectrum, and the frames collapse into coloured wavelength bands under the axis.
 * Falls back to the flat colour section (children) with reduced motion or without WebGL2.
 */
export function Colour3D({
  flat,
  tiles,
  points,
  nUsed,
  nTotal,
  spectrumLine,
}: {
  flat: ReactNode;
  tiles: DetectorTile[];
  points: SpecPoint[];
  nUsed: number;
  nTotal: number;
  spectrumLine: string | null;
}) {
  const { mode, narrow, ready } = use3DMode(tiles.length > 0 && points.length > 0);
  const section = useRef<HTMLElement>(null);
  const sticky = useRef<HTMLDivElement>(null);
  const progress = useRef(0);
  const onProgress = useCallback((p: number) => {
    progress.current = p;
    sticky.current?.style.setProperty("--p", p.toFixed(4));
  }, []);
  useScrollProgress(mode === "3d", section, onProgress);

  if (mode === "flat") return <>{flat}</>;

  return (
    <section ref={section} className="s3d" aria-label="ε Indi B in six detectors, then its spectrum">
      <div ref={sticky} className="h3d-sticky s3d-sticky">
        <div className="h3d-canvas s3d-canvas" aria-hidden="true">
          {ready && <SpectrumScene tiles={tiles} points={points} progress={progress} narrow={narrow} />}
        </div>
        <div className="h3d-note s3d-note-a app">
          <p className="lp-step mono">02 · Colour</p>
          <h2>One patch of sky, six slices of infrared.</h2>
          <p>
            SPHEREx splits the light onto six detectors, from 0.75 to 5 µm. These are ε Indi B, a pair of brown dwarfs,
            on each of them.
          </p>
        </div>
        <div className="h3d-note s3d-note-b app">
          <h2>Every visit is one measurement.</h2>
          <p>Each dot is the brightness of ε Indi B in one real exposure, at the exact wavelength that pixel saw.</p>
        </div>
        <div className="h3d-note s3d-note-c app">
          <h2>Put them together: a spectrum, measured.</h2>
          <p>
            {nUsed} of {nTotal} points are used; the rest were set aside for a stated reason (flags, saturation, a
            neighbour star).
            {spectrumLine && (
              <>
                {" "}
                Our typer reads it as <strong className="lp-accent">{spectrumLine}</strong>.
              </>
            )}
          </p>
        </div>
      </div>
    </section>
  );
}
