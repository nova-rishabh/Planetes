"use client";

import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { Environment, Lightformer, Line, useTexture } from "@react-three/drei";
import { useMemo, useRef, type RefObject } from "react";
import { BackSide, DoubleSide, MathUtils, NearestFilter, SRGBColorSpace, Vector3, type Group, type MeshBasicMaterial, type Texture } from "three";
import { SpherexModel } from "./SpherexModel";
import { readPalette, type Palette } from "./palette";

export type StackFrame = { src: string; xy: [number, number] | null };

/** Plates of the time stack: one real SPHEREx exposure each, stacked above the telescope by date. */
export const STACK_Y0 = 4.4;
/** Distance from the camera to the plate it is showing. */
const VIEW_D = 2.4;
export const STACK_GAP = 0.9;
const PLATE = 1.6;

type Key = {
  at: number;
  pos: [number, number, number];
  look: [number, number, number];
};

function cameraKeys(n: number, narrow: boolean): Key[] {
  const top = STACK_Y0 + (n - 1) * STACK_GAP;
  const far = narrow ? 1.0 : 1;
  return [
    // Hero: the observatory sits right of the headline (left on narrow screens it sits below).
    { at: 0.0, pos: [4.4 * far, 1.9, 5.6 * far], look: narrow ? [0, 3.1, 0] : [-1.0, 0.8, 0.75] },
    { at: 0.16, pos: [2.6, 2.6, 3.1], look: [0.1, 1.1, 0] },
    { at: 0.3, pos: [0.85, 2.8, 0.85], look: [0, 1.3, 0] },
    // Turn to look up: the first plate fills the view, then the camera climbs one plate at a time.
    { at: 0.4, pos: [0, STACK_Y0 - VIEW_D, 0.3], look: [0, STACK_Y0 + 6, -0.45] },
    { at: 1.0, pos: [0, top - VIEW_D, 0.3], look: [0, top + 6, -0.45] },
  ];
}

const ease = (t: number) => t * t * (3 - 2 * t);

function sample(keys: Key[], p: number, pos: Vector3, look: Vector3) {
  let i = 0;
  while (i < keys.length - 2 && p > keys[i + 1]!.at) i++;
  const a = keys[i]!;
  const b = keys[i + 1]!;
  const t = ease(MathUtils.clamp((p - a.at) / (b.at - a.at), 0, 1));
  pos.set(
    MathUtils.lerp(a.pos[0], b.pos[0], t),
    MathUtils.lerp(a.pos[1], b.pos[1], t),
    MathUtils.lerp(a.pos[2], b.pos[2], t),
  );
  look.set(
    MathUtils.lerp(a.look[0], b.look[0], t),
    MathUtils.lerp(a.look[1], b.look[1], t),
    MathUtils.lerp(a.look[2], b.look[2], t),
  );
}

function Rig({ progress, n, narrow }: { progress: RefObject<number>; n: number; narrow: boolean }) {
  const keys = useMemo(() => cameraKeys(n, narrow), [n, narrow]);
  const smooth = useRef(0);
  const posRef = useRef(new Vector3());
  const lookRef = useRef(new Vector3());
  const curLook = useRef<Vector3 | null>(null);
  const pointer = useThree((s) => s.pointer);
  useFrame((state, dt) => {
    const pos = posRef.current;
    const look = lookRef.current;
    smooth.current = MathUtils.damp(smooth.current, progress.current ?? 0, 4, dt);
    sample(keys, smooth.current, pos, look);
    // A little parallax from the pointer, fading out once we're inside the stack.
    const par = 0.18 * (1 - MathUtils.clamp(smooth.current / 0.35, 0, 1));
    pos.x += pointer.x * par;
    pos.y += pointer.y * par * 0.6;
    state.camera.position.copy(pos);
    if (!curLook.current) curLook.current = look.clone();
    curLook.current.lerp(look, 1 - Math.exp(-8 * dt));
    state.camera.lookAt(curLook.current);
  });
  return null;
}

function Observatory({ palette, progress }: { palette: Palette; progress: RefObject<number> }) {
  const g = useRef<Group>(null);
  useFrame((_, dt) => {
    if (!g.current) return;
    // Slow idle turn at the start; it settles as the camera dives in.
    const idle = 1 - MathUtils.clamp((progress.current ?? 0) / 0.3, 0, 1);
    g.current.rotation.y += dt * 0.12 * idle;
  });
  return (
    <group ref={g} rotation={[0, -0.6, 0]}>
      <SpherexModel palette={palette} />
    </group>
  );
}

function Stack({
  frames,
  naxis,
  palette,
  glass,
  progress,
}: {
  frames: StackFrame[];
  naxis: [number, number];
  palette: Palette;
  glass: boolean;
  progress: RefObject<number>;
}) {
  const root = useRef<Group>(null);
  const textures = useTexture(
    frames.map((f) => f.src),
    (loaded) => {
      for (const t of [loaded].flat() as Texture[]) {
        t.magFilter = NearestFilter; // real pixels, shown as pixels
        t.minFilter = NearestFilter;
        t.colorSpace = SRGBColorSpace;
        t.generateMipmaps = false;
        t.needsUpdate = true;
      }
    },
  ) as Texture[];

  const mats = useRef<(MeshBasicMaterial | null)[]>([]);
  const groups = useRef<(Group | null)[]>([]);
  useFrame(({ camera }) => {
    // The stack only appears once the camera has turned towards the telescope.
    if (root.current) root.current.visible = (progress.current ?? 0) > 0.26;
    // The plate the camera has climbed past fades out, so each exposure is seen whole in turn.
    mats.current.forEach((m, k) => {
      if (!m) return;
      const d = STACK_Y0 + k * STACK_GAP - camera.position.y;
      m.opacity = MathUtils.clamp((d - (VIEW_D - STACK_GAP)) / (STACK_GAP * 0.7), 0, 1);
      const g = groups.current[k];
      if (g) g.visible = m.opacity > 0.01;
    });
  });

  const [w, h] = naxis;
  // Target position on each plate (plate-local, north up), then in world space for the path line.
  const local = frames.map((f) =>
    f.xy ? ([((f.xy[0] + 0.5) / w - 0.5) * PLATE, ((f.xy[1] + 0.5) / h - 0.5) * PLATE] as const) : null,
  );
  const path = local.flatMap((uv, k) => (uv ? [new Vector3(-uv[0], STACK_Y0 + k * STACK_GAP - 0.004, -uv[1])] : []));

  return (
    <group ref={root}>
      {frames.map((f, k) => {
        const uv = local[k];
        return (
          // Faces down to the telescope; x mirrored so east/west read correctly from below.
          <group
            key={f.src}
            ref={(g) => {
              groups.current[k] = g;
            }}
            position={[0, STACK_Y0 + k * STACK_GAP, 0]}
            rotation={[-Math.PI / 2, 0, 0]}
            scale={[-1, 1, 1]}
          >
            <mesh>
              <planeGeometry args={[PLATE, PLATE]} />
              <meshBasicMaterial
                ref={(m) => {
                  mats.current[k] = m;
                }}
                map={textures[k]}
                side={DoubleSide}
                toneMapped={false}
                transparent
              />
            </mesh>
            <mesh position={[0, 0, 0.012]}>
              <boxGeometry args={[PLATE + 0.12, PLATE + 0.12, 0.02]} />
              {glass ? (
                <meshPhysicalMaterial
                  color={palette.surface}
                  transmission={1}
                  roughness={0.12}
                  thickness={0.04}
                  ior={1.45}
                  transparent
                  opacity={0.9}
                />
              ) : (
                <meshStandardMaterial color={palette.surface} transparent opacity={0.18} />
              )}
            </mesh>
            {uv && (
              <mesh position={[uv[0], uv[1], -0.006]}>
                <ringGeometry args={[0.07, 0.085, 48]} />
                <meshBasicMaterial color={palette.accent} side={DoubleSide} toneMapped={false} />
              </mesh>
            )}
          </group>
        );
      })}
      {path.length > 1 && <Line points={path} color={palette.accent} lineWidth={2} />}
    </group>
  );
}

export default function Scene({
  frames,
  naxis,
  progress,
  narrow,
}: {
  frames: StackFrame[];
  naxis: [number, number];
  progress: RefObject<number>;
  narrow: boolean;
}) {
  const palette = useMemo(() => readPalette(), []);
  return (
    <Canvas
      dpr={narrow ? [1, 1.5] : [1, 2]}
      camera={{ fov: narrow ? 64 : 38, near: 0.03, far: 60, position: [3.6, 1.5, 4.6] }}
      gl={{ antialias: true, powerPreference: "high-performance" }}
      aria-hidden="true"
    >
      <color attach="background" args={[palette.bg]} />
      <fog attach="fog" args={[palette.bg, 5, 16]} />
      <hemisphereLight args={[palette.surface, palette.border, 1.1]} />
      <directionalLight position={[4, 6, 3]} intensity={1.6} />
      {/* Studio reflections built locally (no HDR download). */}
      <Environment resolution={128}>
        <mesh scale={40}>
          <sphereGeometry args={[1, 32, 16]} />
          <meshBasicMaterial color={palette.bg} side={BackSide} />
        </mesh>
        <Lightformer intensity={2.2} position={[0, 5, -2]} scale={[10, 2, 1]} color={palette.surface} />
        <Lightformer intensity={1.2} position={[-5, 1, 2]} scale={[2, 6, 1]} color={palette.surface} />
        <Lightformer intensity={1} position={[0, -3, 4]} scale={[8, 1.5, 1]} color={palette.ink} />
        <Lightformer intensity={0.35} position={[5, 1, 2]} scale={[1, 4, 1]} color={palette.accent} />
      </Environment>
      <Observatory palette={palette} progress={progress} />
      <Stack frames={frames} naxis={naxis} palette={palette} glass={!narrow} progress={progress} />
      <Rig progress={progress} n={frames.length} narrow={narrow} />
    </Canvas>
  );
}
