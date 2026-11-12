"use client";

import { useMemo, useState } from "react";
import { EARTH_RADIUS_KM, abMag, evaluate, internalHeatUjy, reflectedUjy } from "@/lib/planetx";

/** SPHEREx cutouts in the viewer are a few arcminutes across; the time-lapse default is 0.1 deg. */
const VIEWER_FOV_ARCSEC = 0.1 * 3600;

function Slider(props: {
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  unit: string;
  onChange: (v: number) => void;
}) {
  return (
    <label className="field px-field">
      <span>
        {props.label}: <strong className="mono">{props.value}</strong> {props.unit}
      </span>
      <input
        type="range"
        min={props.min}
        max={props.max}
        step={props.step}
        value={props.value}
        onChange={(e) => props.onChange(Number(e.target.value))}
      />
    </label>
  );
}

const CHART_UM = 1.0;
const ab1um = (radiusKm: number, albedo: number, r: number, tK: number) =>
  abMag(reflectedUjy(CHART_UM, radiusKm, albedo, r) + internalHeatUjy(CHART_UM, radiusKm, r, tK));

/** AB magnitude at 1 µm against distance for the chosen planet, with the SPHEREx single-visit depth line. */
function DistanceChart(props: { radiusKm: number; albedo: number; rAu: number; tK: number; depth: number }) {
  const { radiusKm, albedo, rAu, tK, depth } = props;
  const W = 480;
  const Hh = 200;
  const pad = 36;
  const rs = Array.from({ length: 60 }, (_, i) => 100 + (i * 1400) / 59);
  const vs = rs.map((r) => ab1um(radiusKm, albedo, r, tK));
  const vMin = 12;
  const vMax = 30;
  const x = (r: number) => pad + ((r - 100) / 1400) * (W - pad * 1.5);
  const y = (v: number) => pad / 2 + ((Math.min(Math.max(v, vMin), vMax) - vMin) / (vMax - vMin)) * (Hh - pad);
  const path = rs.map((r, i) => `${i ? "L" : "M"}${x(r).toFixed(1)},${y(vs[i] ?? vMax).toFixed(1)}`).join(" ");
  return (
    <svg viewBox={`0 0 ${W} ${Hh}`} className="px-chart" role="img" aria-label="Brightness at 1 µm against distance">
      <line x1={pad} x2={W - pad / 2} y1={y(depth)} y2={y(depth)} className="px-depth" />
      <text x={W - pad / 2} y={y(depth) - 4} textAnchor="end" className="px-label">
        SPHEREx depth (AB {depth.toFixed(1)})
      </text>
      <path d={path} className="px-line" />
      <circle cx={x(rAu)} cy={y(ab1um(radiusKm, albedo, rAu, tK))} r={4} className="px-dot" />
      {[12, 16, 20, 24, 28].map((v) => (
        <text key={v} x={pad - 6} y={y(v) + 3} textAnchor="end" className="px-label">
          {v}
        </text>
      ))}
      {[100, 500, 1000, 1500].map((r) => (
        <text key={r} x={x(r)} y={Hh - 4} textAnchor={r === 1500 ? "end" : "middle"} className="px-label">
          {r} AU
        </text>
      ))}
    </svg>
  );
}

export function PlanetXCalculator() {
  const [radiusRe, setRadiusRe] = useState(2.6);
  const [albedo, setAlbedo] = useState(0.5);
  const [rAu, setRAu] = useState(600);
  const [tK, setTK] = useState(40);
  const radiusKm = radiusRe * EARTH_RADIUS_KM;
  const s = useMemo(() => evaluate(radiusKm, albedo, rAu, tK, 1), [radiusKm, albedo, rAu, tK]);
  const best = s.bands.reduce((a, b) => (b.ab < a.ab ? b : a));
  const visible = s.bands.some((b) => b.above);

  return (
    <div className="px">
      <div className="panel px-inputs">
        <Slider label="Size" value={radiusRe} min={1} max={10} step={0.1} unit="× Earth's radius" onChange={setRadiusRe} />
        <Slider label="Reflectivity (albedo)" value={albedo} min={0.05} max={0.9} step={0.05} unit="" onChange={setAlbedo} />
        <Slider label="Distance from the Sun" value={rAu} min={100} max={1500} step={10} unit="AU" onChange={setRAu} />
        <Slider label="Internal heat" value={tK} min={0} max={80} step={5} unit="K (model-dependent)" onChange={setTK} />
      </div>

      <div className="panel px-out">
        <p className="px-verdict">
          {visible ? (
            <>
              This planet would be <strong>bright enough</strong> for a single SPHEREx visit at{" "}
              {s.bands.filter((b) => b.above).map((b) => `${b.um} µm`).join(", ")}. SPHEREx covers the whole sky, so a
              planet like this could be searched for in its data.
            </>
          ) : (
            <>
              This planet would be <strong>too faint</strong> for a single SPHEREx visit: brightest at {best.um} µm, AB{" "}
              {best.ab.toFixed(1)}, against a depth of about AB {s.depth.toFixed(1)}.
            </>
          )}
        </p>
        <dl className="px-dl">
          <dt>Visible-light brightness</dt>
          <dd className="mono">V {s.v.toFixed(1)}</dd>
          <dt>Jump between visits six months apart</dt>
          <dd className="mono">
            {(s.shiftArcsec / 60).toFixed(1)}′ ({Math.round(s.shiftArcsec / VIEWER_FOV_ARCSEC)}× the viewer&apos;s
            0.1° field)
          </dd>
        </dl>
        <table className="px-table mono">
          <thead>
            <tr>
              <th>Band</th>
              <th>AB mag</th>
              <th>From internal heat</th>
              <th>Single visit</th>
            </tr>
          </thead>
          <tbody>
            {s.bands.map((b) => (
              <tr key={b.um} data-above={b.above}>
                <td>{b.um.toFixed(1)} µm</td>
                <td>{Number.isFinite(b.ab) ? b.ab.toFixed(1) : "—"}</td>
                <td>{Math.round(b.heatShare * 100)}%</td>
                <td>{b.above ? "brighter than depth" : "fainter"}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <DistanceChart radiusKm={radiusKm} albedo={albedo} rAu={rAu} tK={tK} depth={s.depth} />
        <p className="hint">Brightness at 1 µm (AB magnitude, lower is brighter) as the planet moves farther away; the dot is your choice.</p>
      </div>
    </div>
  );
}
