"use client";

import { Environment, Lightformer } from "@react-three/drei";
import { BackSide } from "three";
import type { Palette } from "./palette";

/** Paper-white studio: background, soft lights and local reflections (no HDR download). */
export function Studio({ palette }: { palette: Palette }) {
  return (
    <>
      <color attach="background" args={[palette.bg]} />
      <hemisphereLight args={[palette.surface, palette.border, 1.1]} />
      <directionalLight position={[4, 6, 3]} intensity={1.6} />
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
    </>
  );
}
