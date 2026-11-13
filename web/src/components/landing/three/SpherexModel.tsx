"use client";

import { useMemo } from "react";
import { DoubleSide, LatheGeometry, Vector2 } from "three";
import type { Palette } from "./palette";

/**
 * SPHEREx observatory, modelled in code (an illustration, not engineering data; no insignia).
 * Shape from NASA/JPL's published description: three nested conical photon shields around the telescope,
 * a hexagonal bus underneath and a fixed solar array. Sizes approximate, in metres (~2.6 m across, ~1.6 m tall).
 */
const SHIELDS = [
  // bottom radius, top radius, bottom y, height
  { rb: 0.36, rt: 0.78, y0: 0.52, h: 0.92 },
  { rb: 0.46, rt: 1.0, y0: 0.5, h: 1.02 },
  { rb: 0.56, rt: 1.22, y0: 0.48, h: 1.12 },
];
const PANEL_TILT = -0.32; // rad
const CELL_COLS = 8;
const CELL_ROWS = 4;

function radiusAt(s: (typeof SHIELDS)[number], y: number) {
  return s.rb + ((s.rt - s.rb) * (y - s.y0)) / s.h;
}

export function SpherexModel({ palette }: { palette: Palette }) {
  const shells = useMemo(
    () => SHIELDS.map((s) => new LatheGeometry([new Vector2(s.rb, s.y0), new Vector2(s.rt, s.y0 + s.h)], 128)),
    [],
  );

  const struts = useMemo(() => {
    const out: { x: number; z: number; len: number; rot: number; y: number }[] = [];
    const y = 0.75;
    for (let k = 0; k < 8; k++) {
      const a = (2 * Math.PI * k) / 8 + Math.PI / 8;
      for (let i = 0; i < SHIELDS.length - 1; i++) {
        const r1 = radiusAt(SHIELDS[i]!, y);
        const r2 = radiusAt(SHIELDS[i + 1]!, y);
        const r = (r1 + r2) / 2;
        out.push({
          x: r * Math.cos(a),
          z: r * Math.sin(a),
          len: r2 - r1,
          rot: -a,
          y,
        });
      }
    }
    return out;
  }, []);

  const cells = useMemo(() => {
    const W = 1.25;
    const H = 0.72;
    const cw = (W - 0.06) / CELL_COLS;
    const ch = (H - 0.06) / CELL_ROWS;
    const out: { x: number; y: number; w: number; h: number }[] = [];
    for (let c = 0; c < CELL_COLS; c++)
      for (let r = 0; r < CELL_ROWS; r++)
        out.push({
          x: -W / 2 + 0.03 + cw * (c + 0.5),
          y: -H / 2 + 0.03 + ch * (r + 0.5),
          w: cw * 0.92,
          h: ch * 0.9,
        });
    return out;
  }, []);

  return (
    <group>
      {/* Bus and deck */}
      <mesh position={[0, 0.23, 0]} castShadow>
        <cylinderGeometry args={[0.62, 0.62, 0.46, 6]} />
        <meshStandardMaterial color={palette.ink} metalness={0.25} roughness={0.55} flatShading />
      </mesh>
      <mesh position={[0, 0.475, 0]}>
        <cylinderGeometry args={[0.66, 0.66, 0.03, 6]} />
        <meshStandardMaterial color={palette.ui} metalness={0.8} roughness={0.35} flatShading />
      </mesh>

      {/* Photon shields with a rolled lip */}
      {SHIELDS.map((s, i) => (
        <group key={i}>
          <mesh geometry={shells[i]}>
            <meshStandardMaterial
              color={palette.border}
              metalness={0.92}
              roughness={0.3 + i * 0.05}
              side={DoubleSide}
              envMapIntensity={0.9}
            />
          </mesh>
          <mesh position={[0, s.y0 + s.h, 0]} rotation={[Math.PI / 2, 0, 0]}>
            <torusGeometry args={[s.rt, 0.014, 10, 128]} />
            <meshStandardMaterial color={palette.surface} metalness={1} roughness={0.18} />
          </mesh>
        </group>
      ))}
      {struts.map((s, k) => (
        <mesh key={k} position={[s.x, s.y, s.z]} rotation={[0, s.rot, 0]}>
          <boxGeometry args={[s.len, 0.03, 0.012]} />
          <meshStandardMaterial color={palette.ui} metalness={0.8} roughness={0.4} />
        </mesh>
      ))}

      {/* Telescope: barrel, dark aperture, spider and secondary */}
      <mesh position={[0, 0.84, 0]}>
        <cylinderGeometry args={[0.21, 0.21, 0.62, 64]} />
        <meshStandardMaterial color={palette.ui} metalness={0.6} roughness={0.4} />
      </mesh>
      <mesh position={[0, 1.152, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <circleGeometry args={[0.19, 64]} />
        <meshStandardMaterial color={palette.plate} roughness={0.9} />
      </mesh>
      {[0, 1, 2].map((k) => {
        const a = (2 * Math.PI * k) / 3;
        return (
          <mesh key={k} position={[0.1 * Math.cos(a), 1.17, 0.1 * Math.sin(a)]} rotation={[0, -a, 0]}>
            <boxGeometry args={[0.2, 0.008, 0.008]} />
            <meshStandardMaterial color={palette.ui} metalness={0.8} roughness={0.4} />
          </mesh>
        );
      })}
      <mesh position={[0, 1.18, 0]}>
        <cylinderGeometry args={[0.05, 0.05, 0.06, 32]} />
        <meshStandardMaterial color={palette.ui} metalness={0.6} roughness={0.4} />
      </mesh>

      {/* Solar array on an arm, tilted, with a cell grid */}
      <mesh position={[0, 0.22, 0.7]}>
        <boxGeometry args={[0.08, 0.05, 0.3]} />
        <meshStandardMaterial color={palette.ui} metalness={0.8} roughness={0.4} />
      </mesh>
      <group position={[0, 0.2, 1.18]} rotation={[-Math.PI / 2 - PANEL_TILT, 0, 0]}>
        <mesh>
          <boxGeometry args={[1.25, 0.72, 0.025]} />
          <meshStandardMaterial color={palette.ui} metalness={0.8} roughness={0.4} />
        </mesh>
        {cells.map((c, k) => (
          <mesh key={k} position={[c.x, c.y, 0.016]}>
            <boxGeometry args={[c.w, c.h, 0.006]} />
            <meshStandardMaterial color={palette.plate} metalness={0.4} roughness={0.25} />
          </mesh>
        ))}
      </group>
    </group>
  );
}
