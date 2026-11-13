"use client";

import { Canvas, useFrame } from "@react-three/fiber";
import { Html, Line, useTexture } from "@react-three/drei";
import { useMemo, useRef, type RefObject } from "react";
import {
  Color,
  DoubleSide,
  MathUtils,
  NearestFilter,
  Object3D,
  SRGBColorSpace,
  Vector3,
  type Group,
  type InstancedMesh,
  type Mesh,
  type MeshBasicMaterial,
  type Texture,
} from "three";
import { readPalette, readDetectorColours } from "./palette";

export type DetectorTile = { src: string; detector: number; wavelength_um: number | null };
export type SpecPoint = { um: number; ujy: number; det: number };

const UM_MIN = 0.7;
const UM_MAX = 5.05;
const CHART_W = 6;
const CHART_H = 3;
const CHART_Y0 = -1.5;
const TILE = 1.2;

const clamp01 = (x: number) => MathUtils.clamp(x, 0, 1);
const ease = (t: number) => t * t * (3 - 2 * t);
/** Window [a, b] of progress p mapped to 0..1, eased. */
const win = (p: number, a: number, b: number) => ease(clamp01((p - a) / (b - a)));

function chartX(um: number) {
  return -CHART_W / 2 + ((um - UM_MIN) / (UM_MAX - UM_MIN)) * CHART_W;
}

/** Grid slot of a detector: D1–D3 on top, D4–D6 below (the two sides of SPHEREx's focal plane). */
function gridPos(det: number): [number, number] {
  const col = (det - 1) % 3;
  const row = det <= 3 ? 0 : 1;
  return [(col - 1) * (TILE + 0.18), row === 0 ? 0.62 : -0.82];
}

/** Deterministic jitter so each point leaves its detector from a different spot. */
function hash(i: number) {
  const s = Math.sin(i * 12.9898) * 43758.5453;
  return s - Math.floor(s);
}

function Tiles({
  tiles,
  ranges,
  progress,
}: {
  tiles: DetectorTile[];
  ranges: Map<number, [number, number]>;
  progress: RefObject<number>;
}) {
  const colours = useMemo(() => readDetectorColours(), []);
  const textures = useTexture(
    tiles.map((t) => t.src),
    (loaded) => {
      for (const t of [loaded].flat() as Texture[]) {
        t.magFilter = NearestFilter;
        t.minFilter = NearestFilter;
        t.colorSpace = SRGBColorSpace;
        t.generateMipmaps = false;
        t.needsUpdate = true;
      }
    },
  ) as Texture[];
  const groups = useRef<(Group | null)[]>([]);
  const imgs = useRef<(MeshBasicMaterial | null)[]>([]);
  const bands = useRef<(MeshBasicMaterial | null)[]>([]);

  useFrame(() => {
    const p = progress.current ?? 0;
    tiles.forEach((t, i) => {
      const g = groups.current[i];
      if (!g) return;
      const [gx, gy] = gridPos(t.detector);
      const fly = win(p, 0.02 + i * 0.035, 0.16 + i * 0.035);
      const collapse = win(p, 0.56, 0.7);
      const r = ranges.get(t.detector);
      const sx = r ? Math.max(0.05, chartX(r[1]) - chartX(r[0])) : TILE;
      const cx = r ? (chartX(r[0]) + chartX(r[1])) / 2 : gx;
      g.position.set(
        MathUtils.lerp(gx, cx, collapse),
        MathUtils.lerp(gy, CHART_Y0 - 0.22, collapse),
        MathUtils.lerp(-9, 0, fly),
      );
      g.rotation.y = (1 - fly) * 1.1;
      g.scale.set(MathUtils.lerp(1, sx / TILE, collapse), MathUtils.lerp(1, 0.07, collapse), 1);
      const img = imgs.current[i];
      if (img) img.opacity = fly * (1 - collapse);
      const band = bands.current[i];
      if (band) band.opacity = collapse;
      g.visible = fly > 0.001;
    });
  });

  return (
    <>
      {tiles.map((t, i) => (
        <group
          key={t.src}
          ref={(g) => {
            groups.current[i] = g;
          }}
        >
          <mesh>
            <planeGeometry args={[TILE, TILE]} />
            <meshBasicMaterial
              ref={(m) => {
                imgs.current[i] = m;
              }}
              map={textures[i]}
              transparent
              toneMapped={false}
              side={DoubleSide}
            />
          </mesh>
          <mesh position={[0, 0, 0.001]}>
            <planeGeometry args={[TILE, TILE]} />
            <meshBasicMaterial
              ref={(m) => {
                bands.current[i] = m;
              }}
              color={colours[t.detector - 1]}
              transparent
              opacity={0}
              toneMapped={false}
            />
          </mesh>
          <Html position={[0, -TILE / 2 - 0.12, 0]} center className="s3d-tile-label mono" zIndexRange={[5, 0]}>
            D{t.detector}
            {ranges.get(t.detector) &&
              ` · ${ranges.get(t.detector)![0].toFixed(2)}–${ranges.get(t.detector)![1].toFixed(2)} µm`}
          </Html>
        </group>
      ))}
    </>
  );
}

function Points({
  points,
  tiles,
  fmax,
  progress,
}: {
  points: SpecPoint[];
  tiles: DetectorTile[];
  fmax: number;
  progress: RefObject<number>;
}) {
  const mesh = useRef<InstancedMesh>(null);
  const dummy = useMemo(() => new Object3D(), []);
  const colours = useMemo(() => readDetectorColours(), []);
  const hasTile = useMemo(() => new Set(tiles.map((t) => t.detector)), [tiles]);
  const coloured = useRef(false);

  useFrame(() => {
    const m = mesh.current;
    if (!m) return;
    if (!coloured.current) {
      points.forEach((pt, j) => m.setColorAt(j, colours[pt.det - 1] ?? new Color()));
      if (m.instanceColor) m.instanceColor.needsUpdate = true;
      coloured.current = true;
    }
    const p = progress.current ?? 0;
    points.forEach((pt, j) => {
      const [gx, gy] = hasTile.has(pt.det) ? gridPos(pt.det) : [0, 0];
      const sx = gx + (hash(j) - 0.5) * TILE * 0.8;
      const sy = gy + (hash(j + 999) - 0.5) * TILE * 0.8;
      const tx = chartX(pt.um);
      const ty = CHART_Y0 + (pt.ujy / fmax) * CHART_H;
      // Short wavelengths leave first, so the spectrum draws from left to right.
      const a = 0.34 + ((pt.um - UM_MIN) / (UM_MAX - UM_MIN)) * 0.14;
      const t = win(p, a, a + 0.14);
      dummy.position.set(
        MathUtils.lerp(sx, tx, t),
        MathUtils.lerp(sy, ty, t),
        Math.sin(Math.PI * t) * 1.2 + 0.02,
      );
      const s = t <= 0 ? 0 : 1;
      dummy.scale.setScalar(s);
      dummy.updateMatrix();
      m.setMatrixAt(j, dummy.matrix);
    });
    m.instanceMatrix.needsUpdate = true;
  });

  return (
    <instancedMesh ref={mesh} args={[undefined, undefined, points.length]} frustumCulled={false}>
      <sphereGeometry args={[0.032, 10, 8]} />
      <meshBasicMaterial toneMapped={false} />
    </instancedMesh>
  );
}

function Axes({ fmax }: { fmax: number }) {
  const palette = useMemo(() => readPalette(), []);
  const ticks = [1, 2, 3, 4, 5];
  const fluxTicks = [0, 0.5, 1].map((f) => f * fmax);
  return (
    <group>
      <Line
        points={[new Vector3(-CHART_W / 2, CHART_Y0, 0), new Vector3(CHART_W / 2, CHART_Y0, 0)]}
        color={palette.ink}
        lineWidth={1}
      />
      <Line
        points={[new Vector3(-CHART_W / 2, CHART_Y0, 0), new Vector3(-CHART_W / 2, CHART_Y0 + CHART_H, 0)]}
        color={palette.ink}
        lineWidth={1}
      />
      {ticks.map((um) => (
        <Html key={um} position={[chartX(um), CHART_Y0 - 0.42, 0]} center className="s3d-axis mono" zIndexRange={[5, 0]}>
          {um} µm
        </Html>
      ))}
      {fluxTicks.map((f) => (
        <Html
          key={f}
          position={[-CHART_W / 2 - 0.2, CHART_Y0 + (f / fmax) * CHART_H, 0]}
          center
          className="s3d-axis s3d-axis-y mono"
          zIndexRange={[5, 0]}
        >
          {f >= 1000 ? `${Math.round(f / 1000)} mJy` : `${Math.round(f)} µJy`}
        </Html>
      ))}
    </group>
  );
}

function Rig({ progress, narrow }: { progress: RefObject<number>; narrow: boolean }) {
  const smooth = useRef(0);
  const look = useMemo(() => new Vector3(0, -0.1, 0), []);
  useFrame((state, dt) => {
    smooth.current = MathUtils.damp(smooth.current, progress.current ?? 0, 4, dt);
    const p = smooth.current;
    const z = MathUtils.lerp(8.6, 7.1, win(p, 0, 0.3));
    // A slow swing at the end on wide screens; phones keep the chart square-on so it fits.
    const swing = narrow ? 0 : win(p, 0.7, 1);
    state.camera.position.set(
      swing * 0.9 + state.pointer.x * 0.25,
      0.1 + swing * 0.35 + state.pointer.y * 0.15,
      z - swing * 0.4,
    );
    state.camera.lookAt(look);
  });
  return null;
}

function Fade({ progress, children }: { progress: RefObject<number>; children: React.ReactNode }) {
  const g = useRef<Group>(null);
  useFrame(() => {
    if (!g.current) return;
    const o = win(progress.current ?? 0, 0.58, 0.7);
    g.current.visible = o > 0.01;
    g.current.traverse((obj) => {
      const mat = (obj as Mesh).material as { opacity?: number; transparent?: boolean } | undefined;
      if (mat && "opacity" in mat) {
        mat.transparent = true;
        mat.opacity = o;
      }
    });
  });
  return <group ref={g}>{children}</group>;
}

export default function SpectrumScene({
  tiles,
  points,
  progress,
  narrow,
}: {
  tiles: DetectorTile[];
  points: SpecPoint[];
  progress: RefObject<number>;
  narrow: boolean;
}) {
  const palette = useMemo(() => readPalette(), []);
  // Wavelength range of each detector, from its measured points.
  const ranges = useMemo(() => {
    const r = new Map<number, [number, number]>();
    for (const p of points) {
      const cur = r.get(p.det);
      r.set(p.det, cur ? [Math.min(cur[0], p.um), Math.max(cur[1], p.um)] : [p.um, p.um]);
    }
    return r;
  }, [points]);
  const fmax = useMemo(() => Math.max(...points.map((p) => p.ujy)) * 1.08, [points]);

  return (
    <Canvas
      dpr={narrow ? [1, 1.5] : [1, 2]}
      camera={{ fov: narrow ? 60 : 38, near: 0.1, far: 60, position: [0, 0.1, 8.6] }}
      gl={{ antialias: true }}
    >
      <color attach="background" args={[palette.bg]} />
      <group scale={narrow ? 0.56 : 1} position={narrow ? [0.12, 0, 0] : [0, 0, 0]}>
        <Tiles tiles={tiles} ranges={ranges} progress={progress} />
        <Points points={points} tiles={tiles} fmax={fmax} progress={progress} />
        <Fade progress={progress}>
          <Axes fmax={fmax} />
        </Fade>
      </group>
      <Rig progress={progress} narrow={narrow} />
    </Canvas>
  );
}
