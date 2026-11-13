"use client";

import { Canvas, useFrame } from "@react-three/fiber";
import { Html } from "@react-three/drei";
import { useMemo, useRef, type RefObject } from "react";
import { DoubleSide, MathUtils, type Group, type Mesh } from "three";
import { readPalette } from "./palette";

/** Radius on screen for a distance in AU: logarithmic, so Neptune (30 AU) and 1500 AU both fit. */
export function orbitR(au: number) {
  return 0.55 + 0.85 * Math.log10(au / 10);
}

function Ring({ r, width, color, opacity }: { r: number; width: number; color: string; opacity: number }) {
  return (
    <mesh rotation={[-Math.PI / 2, 0, 0]}>
      <ringGeometry args={[r - width / 2, r + width / 2, 160]} />
      <meshBasicMaterial color={color} side={DoubleSide} transparent opacity={opacity} toneMapped={false} />
    </mesh>
  );
}

function System({
  au,
  seen,
  progress,
}: {
  au: RefObject<number>;
  seen: RefObject<boolean>;
  progress: RefObject<number>;
}) {
  const palette = useMemo(() => readPalette(), []);
  const ink = `#${palette.ink.getHexString()}`;
  const muted = `#${palette.ui.getHexString()}`;
  const accent = `#${palette.accent.getHexString()}`;
  const root = useRef<Group>(null);
  const planet = useRef<Mesh>(null);
  const orbit = useRef<Mesh>(null);
  const angle = useRef(0.6);
  const neptune = useRef<Mesh>(null);

  useFrame((state, dt) => {
    state.camera.lookAt(0, -0.25, 0);
    const p = progress.current ?? 0;
    if (root.current) {
      root.current.rotation.y = 0.4 + p * 0.9 + state.pointer.x * 0.15;
      root.current.rotation.x = 0.1 + state.pointer.y * 0.06;
    }
    // Kepler: period grows as a^1.5, so the far planet crawls compared with Neptune (sped up for the eye).
    const a = au.current ?? 700;
    angle.current += dt * 0.25 * Math.pow(30 / a, 1.5) * 8;
    const r = orbitR(a);
    planet.current?.position.set(Math.cos(angle.current) * r, 0, Math.sin(angle.current) * r);
    if (orbit.current) orbit.current.scale.setScalar(r / orbitR(700));
    if (neptune.current) {
      const t = state.clock.elapsedTime * 0.25;
      neptune.current.position.set(Math.cos(t) * orbitR(30), 0, Math.sin(t) * orbitR(30));
    }
    if (planet.current) {
      const m = planet.current.material as unknown as { color: { set: (c: string) => void }; opacity: number };
      m.color.set(seen.current ? accent : muted);
      m.opacity = seen.current ? 1 : 0.55;
      planet.current.scale.setScalar(MathUtils.lerp(planet.current.scale.x, seen.current ? 1.25 : 0.9, 0.1));
    }
  });

  return (
    <group ref={root}>
      <mesh>
        <sphereGeometry args={[0.12, 32, 16]} />
        <meshBasicMaterial color={accent} toneMapped={false} />
      </mesh>
      <Html position={[0, 0.28, 0]} center className="o3d-label mono">
        Sun
      </Html>
      {/* Kuiper belt, 30–50 AU */}
      <mesh rotation={[-Math.PI / 2, 0, 0]}>
        <ringGeometry args={[orbitR(30), orbitR(50), 160]} />
        <meshBasicMaterial color={muted} side={DoubleSide} transparent opacity={0.16} />
      </mesh>
      <Ring r={orbitR(30)} width={0.012} color={ink} opacity={0.55} />
      <mesh ref={neptune}>
        <sphereGeometry args={[0.055, 24, 12]} />
        <meshBasicMaterial color={ink} />
        <Html position={[0, 0.2, 0]} center className="o3d-label mono">
          Neptune · 30 AU
        </Html>
      </mesh>
      {[100, 1000].map((d) => (
        <group key={d}>
          <Ring r={orbitR(d)} width={0.006} color={muted} opacity={0.35} />
          <Html position={[orbitR(d), 0, 0]} center className="o3d-label o3d-scale mono">
            {d} AU
          </Html>
        </group>
      ))}
      <mesh ref={orbit} rotation={[-Math.PI / 2, 0, 0]}>
        <ringGeometry args={[orbitR(700) - 0.008, orbitR(700) + 0.008, 200]} />
        <meshBasicMaterial color={accent} side={DoubleSide} transparent opacity={0.7} toneMapped={false} />
      </mesh>
      <mesh ref={planet}>
        <sphereGeometry args={[0.07, 24, 12]} />
        <meshBasicMaterial color={accent} transparent toneMapped={false} />
      </mesh>
    </group>
  );
}

export default function OrbitScene({
  au,
  seen,
  progress,
  narrow,
}: {
  au: RefObject<number>;
  seen: RefObject<boolean>;
  progress: RefObject<number>;
  narrow: boolean;
}) {
  const palette = useMemo(() => readPalette(), []);
  return (
    <Canvas dpr={narrow ? [1, 1.5] : [1, 2]} camera={{ fov: 34, position: [0, 4.2, 6.4] }} aria-hidden="true">
      <color attach="background" args={[palette.bg]} />
      <System au={au} seen={seen} progress={progress} />
    </Canvas>
  );
}
