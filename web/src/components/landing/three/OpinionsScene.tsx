"use client";

import { Canvas, useFrame } from "@react-three/fiber";
import { Line, RoundedBox } from "@react-three/drei";
import { useMemo, useRef, type RefObject } from "react";
import { MathUtils, Vector3, type Group } from "three";
import { readDetectorColours, readPalette, type Palette } from "./palette";
import { Studio } from "./Studio";

/**
 * Two Opinions as two glass blocks: one holds an arrow and its trail (motion), the other a prism splitting a ray
 * into the six detector colours (spectrum). Symbols only; the numbers stay in the text cards.
 */
function Glass({ palette, glass }: { palette: Palette; glass: boolean }) {
  return (
    <RoundedBox args={[1.7, 1.7, 1.7]} radius={0.16} smoothness={4}>
      {glass ? (
        <meshPhysicalMaterial
          color={palette.surface}
          transmission={1}
          thickness={0.45}
          roughness={0.04}
          ior={1.25}
          clearcoat={1}
          transparent
        />
      ) : (
        <meshStandardMaterial color={palette.surface} transparent opacity={0.25} />
      )}
    </RoundedBox>
  );
}

function MotionInside({ palette }: { palette: Palette }) {
  const trail = [-0.55, -0.35, -0.15];
  return (
    <group rotation={[0, 0, 0.35]}>
      {trail.map((x, k) => (
        <mesh key={x} position={[x, 0, 0]}>
          <sphereGeometry args={[0.05 + k * 0.012, 16, 12]} />
          <meshBasicMaterial color={palette.accent} transparent opacity={0.3 + k * 0.2} toneMapped={false} />
        </mesh>
      ))}
      <mesh position={[0.18, 0, 0]} rotation={[0, 0, -Math.PI / 2]}>
        <cylinderGeometry args={[0.045, 0.045, 0.42, 16]} />
        <meshStandardMaterial color={palette.accent} />
      </mesh>
      <mesh position={[0.48, 0, 0]} rotation={[0, 0, -Math.PI / 2]}>
        <coneGeometry args={[0.13, 0.26, 24]} />
        <meshStandardMaterial color={palette.accent} />
      </mesh>
    </group>
  );
}

function SpectrumInside({ palette }: { palette: Palette }) {
  const colours = useMemo(() => readDetectorColours(), []);
  return (
    <group>
      <Line points={[new Vector3(-0.75, 0.12, 0), new Vector3(-0.12, 0.02, 0)]} color={palette.ink} lineWidth={2} />
      <mesh rotation={[Math.PI / 2, 0, 0]}>
        <cylinderGeometry args={[0.24, 0.24, 0.42, 3]} />
        <meshStandardMaterial color={palette.border} metalness={0.2} roughness={0.15} />
      </mesh>
      {colours.map((c, k) => (
        <Line
          key={k}
          points={[new Vector3(0.12, 0, 0), new Vector3(0.72, -0.3 + k * 0.12, 0)]}
          color={c}
          lineWidth={2.5}
        />
      ))}
    </group>
  );
}

function Blocks({ progress, narrow }: { progress: RefObject<number>; narrow: boolean }) {
  const palette = useMemo(() => readPalette(), []);
  const a = useRef<Group>(null);
  const b = useRef<Group>(null);
  useFrame((state) => {
    const p = progress.current ?? 0;
    const t = state.clock.elapsedTime;
    // The blocks turn towards each other as the section scrolls through, and bob a little.
    const turn = (p - 0.5) * 1.4;
    if (a.current) {
      a.current.rotation.set(0.25 + state.pointer.y * 0.15, 0.5 - turn + state.pointer.x * 0.2, 0);
      a.current.position.y = Math.sin(t * 0.8) * 0.06;
    }
    if (b.current) {
      b.current.rotation.set(0.25 + state.pointer.y * 0.15, -0.5 + turn + state.pointer.x * 0.2, 0);
      b.current.position.y = Math.sin(t * 0.8 + 1.4) * 0.06;
    }
    const spread = MathUtils.lerp(narrow ? 1.4 : 2.3, narrow ? 1.0 : 1.2, MathUtils.smoothstep(p, 0.1, 0.5));
    if (a.current) a.current.position.x = -spread;
    if (b.current) b.current.position.x = spread;
  });
  return (
    <group scale={narrow ? 1.15 : 1.25}>
      <group ref={a}>
        <MotionInside palette={palette} />
        <Glass palette={palette} glass={!narrow} />
      </group>
      <group ref={b}>
        <SpectrumInside palette={palette} />
        <Glass palette={palette} glass={!narrow} />
      </group>
    </group>
  );
}

export default function OpinionsScene({ progress, narrow }: { progress: RefObject<number>; narrow: boolean }) {
  const palette = useMemo(() => readPalette(), []);
  return (
    <Canvas dpr={narrow ? [1, 1.5] : [1, 2]} camera={{ fov: 30, position: [0, 0.4, 7.2] }} aria-hidden="true">
      <Studio palette={palette} />
      <Blocks progress={progress} narrow={narrow} />
    </Canvas>
  );
}
