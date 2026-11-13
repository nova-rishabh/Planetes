"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useEffect, useId, useMemo, useRef, useState, type ReactNode } from "react";
import { EARTH_RADIUS_KM, SPHEREX_SINGLE_VISIT_AB, evaluate } from "@/lib/planetx";
import { LazyScene } from "./LazyScene";

const OrbitScene = dynamic(() => import("./three/OrbitScene"), { ssr: false });

// Same assumptions as the /planet-x page defaults: albedo 0.5, 40 K internal heat, one SPHEREx visit.
const ALBEDO = 0.5;
const TEMP_K = 40;

/**
 * Planet X teaser with live controls: distance and size sliders drive our brightness model (lib/planetx), and a
 * 3D solar system (log-scaled) shows where that orbit sits. The planet turns orange when one SPHEREx visit could
 * see it. `flatFigure` is shown when 3D can't run.
 */
export function PlanetX3D({ flatFigure }: { flatFigure: ReactNode }) {
  const [au, setAu] = useState(700);
  const [earths, setEarths] = useState(2.6);
  const r = useMemo(() => evaluate(earths * EARTH_RADIUS_KM, ALBEDO, au, TEMP_K, 1), [au, earths]);
  const best = r.bands.reduce((a, b) => (b.ab < a.ab ? b : a));
  const seen = best.ab <= SPHEREX_SINGLE_VISIT_AB;
  const auRef = useRef(au);
  const seenRef = useRef(seen);
  useEffect(() => {
    auRef.current = au;
    seenRef.current = seen;
  }, [au, seen]);
  const idA = useId();
  const idS = useId();

  return (
    <section className="ed-sec ed-wrap ed-split">
      <div className="lp-scene-text">
        <p className="ed-num mono">04 — Planet X</p>
        <h2 className="ed-h2">Could SPHEREx see a hidden planet?</h2>
        <p>
          Move a planet out past Neptune and make it bigger or smaller. Our model gives its brightness in each SPHEREx
          band; one visit reaches about <strong className="mono">AB {SPHEREX_SINGLE_VISIT_AB}</strong> (lower is
          brighter).
        </p>
        <div className="px3d-controls">
          <label htmlFor={idA} className="field">
            <span>
              Distance <strong className="mono">{au} AU</strong>
            </span>
            <input
              id={idA}
              type="range"
              min={150}
              max={1500}
              step={10}
              value={au}
              onChange={(e) => setAu(Number(e.target.value))}
            />
          </label>
          <label htmlFor={idS} className="field">
            <span>
              Size <strong className="mono">{earths.toFixed(1)} × Earth</strong>
            </span>
            <input
              id={idS}
              type="range"
              min={1}
              max={10}
              step={0.1}
              value={earths}
              onChange={(e) => setEarths(Number(e.target.value))}
            />
          </label>
        </div>
        <p className="px3d-readout" aria-live="polite">
          Brightest at {best.um} µm: <strong className="mono">AB {best.ab.toFixed(1)}</strong>.{" "}
          {seen ? (
            <strong className="lp-accent">One SPHEREx visit could see it.</strong>
          ) : (
            <>One visit would miss it.</>
          )}{" "}
          Between visits six months apart it jumps {(r.shiftArcsec / 60).toFixed(0)}′.
        </p>
        <Link href="/planet-x" className="ed-btn mono">
          Open the full Planet X check →
        </Link>
      </div>
      <LazyScene
        className="px3d-figure"
        label="Solar system to scale on a log axis, with the chosen planet's orbit"
        flat={flatFigure}
      >
        {({ narrow, progress }) => <OrbitScene au={auRef} seen={seenRef} progress={progress} narrow={narrow} />}
      </LazyScene>
    </section>
  );
}
