"use client";

import type { LandingSpectrum } from "@/lib/landing";
import { useInView } from "./useInView";

/** Detector bands (docs/02) so the reader sees which camera each part of the spectrum came from. */
const BANDS: [string, number, number][] = [
  ["D1", 0.75, 1.09],
  ["D2", 1.1, 1.62],
  ["D3", 1.63, 2.41],
  ["D4", 2.42, 3.82],
  ["D5", 3.83, 4.41],
  ["D6", 4.42, 5.0],
];

/** Real measured points (used ones only) that draw in from short to long wavelength when scrolled into view. */
export function SpectrumSketch({ spectrum, label }: { spectrum: LandingSpectrum; label: string }) {
  const [ref, inView] = useInView<HTMLDivElement>(false, 0.3);
  const W = 560;
  const H = 240;
  const pad = { l: 44, r: 12, t: 12, b: 40 };
  const ys = spectrum.points.map((p) => p.ujy).sort((a, b) => a - b);
  const hi = ys[Math.floor(ys.length * 0.98)] ?? 1;
  const x = (um: number) => pad.l + ((um - 0.7) / (5.05 - 0.7)) * (W - pad.l - pad.r);
  const y = (v: number) => H - pad.b - (Math.max(0, Math.min(v, hi * 1.1)) / (hi * 1.1)) * (H - pad.t - pad.b);
  const n = spectrum.points.length;

  return (
    <div ref={ref} className="lp-spec" data-in={inView}>
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`${label}: ${spectrum.nUsed} measured SPHEREx points from 0.75 to 5 µm`}>
        {BANDS.map(([name, lo, hiUm], k) => (
          <g key={name}>
            <rect x={x(lo)} y={pad.t} width={x(hiUm) - x(lo)} height={H - pad.t - pad.b} className={k % 2 ? "lp-band-alt" : "lp-band"} />
            <text x={(x(lo) + x(hiUm)) / 2} y={H - pad.b + 14} textAnchor="middle" className="lp-axis">
              {name}
            </text>
          </g>
        ))}
        {[1, 2, 3, 4, 5].map((um) => (
          <text key={um} x={x(um)} y={H - 6} textAnchor="middle" className="lp-axis">
            {um} µm
          </text>
        ))}
        <text x={8} y={pad.t + 8} className="lp-axis">µJy</text>
        {spectrum.points.map((p, k) => (
          <circle
            key={k}
            cx={x(p.um)}
            cy={y(p.ujy)}
            r={2.2}
            className="lp-pt"
            style={{ transitionDelay: `${Math.round((k / Math.max(1, n)) * 1400)}ms` }}
          />
        ))}
      </svg>
    </div>
  );
}
