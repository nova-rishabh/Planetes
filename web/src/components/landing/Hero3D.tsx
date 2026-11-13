"use client";

import dynamic from "next/dynamic";
import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";
import { pitchHz, tone } from "@/lib/sound";
import type { StackFrame } from "./three/Scene";
import { use3DMode, useScrollProgress } from "./three/scroll";

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
  const { mode, narrow, ready } = use3DMode(frames.length > 1);
  const section = useRef<HTMLElement>(null);
  const sticky = useRef<HTMLDivElement>(null);
  const tickDate = useRef<HTMLSpanElement>(null);
  const tickIdx = useRef<HTMLSpanElement>(null);
  const progress = useRef(0);
  const [soundOn, setSoundOn] = useState(false);
  const sound = useRef(false);
  const lastPlate = useRef(-1);
  useEffect(() => {
    sound.current = soundOn;
  }, [soundOn]);

  const onProgress = useCallback(
    (p: number) => {
      progress.current = p;
      sticky.current?.style.setProperty("--p", p.toFixed(4));
      // Which plate the camera is passing (the stack runs from p = 0.4 to 1).
      const k = Math.min(frames.length - 1, Math.max(0, Math.round(((p - 0.4) / 0.6) * (frames.length - 1))));
      const f = frames[k];
      if (f && tickDate.current && tickIdx.current) {
        tickDate.current.textContent = fmt(f.utc);
        tickIdx.current.textContent = `${k + 1}/${frames.length}`;
      }
      // Optional sound: a soft tone each time the camera reaches a new plate (pitch from wavelength).
      if (p > 0.4 && k !== lastPlate.current) {
        if (sound.current && f) tone(pitchHz(f.wavelength_um), 0.06, 0.18);
        lastPlate.current = k;
      }
    },
    [frames],
  );
  useScrollProgress(mode === "3d", section, onProgress);

  if (mode === "flat") return <>{flat}</>;

  const first = frames[0]!;
  const last = frames[frames.length - 1]!;
  return (
    <section ref={section} className="h3d" aria-label="SPHEREx and a year of Barnard's Star">
      <div ref={sticky} className="h3d-sticky">
        <div className="h3d-canvas">
          {ready && <Scene frames={frames} naxis={naxis} progress={progress} narrow={narrow} />}
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
        <button
          type="button"
          className="h3d-sound mono"
          aria-pressed={soundOn}
          onClick={() => {
            if (!soundOn) tone(pitchHz(first.wavelength_um), 0.05, 0.12);
            setSoundOn((v) => !v);
          }}
        >
          Sound {soundOn ? "on" : "off"}
        </button>
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
