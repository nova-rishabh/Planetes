"use client";

import { Canvas, useFrame } from "@react-three/fiber";
import { Line } from "@react-three/drei";
import { useLayoutEffect, useMemo, useRef, type RefObject } from "react";
import { MathUtils, Object3D, Vector3, type Group, type InstancedMesh, type Mesh } from "three";
import type { StarField } from "@/lib/landing";
import { readPalette } from "./palette";

/**
 * The footer: real Gaia DR3 stars around Barnard's Star printed as dark dots on a tilted paper plate, with
 * Barnard's Star itself (orange) walking along its measured path. Dot size follows magnitude.
 */
function Plate({ field, progress }: { field: StarField; progress: RefObject<number> }) {
  const palette = useMemo(() => readPalette(), []);
  const k = 2.6 / field.radiusArcmin; // arcmin → scene units
  const mesh = useRef<InstancedMesh>(null);
  const root = useRef<Group>(null);
  const dot = useRef<Mesh>(null);
  const path = useMemo(() => field.path.map(([x, y]) => new Vector3(-x * k, y * k, 0.004)), [field.path, k]);

  useLayoutEffect(() => {
    const m = mesh.current;
    if (!m) return;
    const o = new Object3D();
    field.stars.forEach((s, i) => {
      // East is left on a sky chart.
      o.position.set(-s.x * k, s.y * k, 0.002);
      o.scale.setScalar(MathUtils.clamp(0.055 - (s.mag - 9) * 0.0045, 0.012, 0.06));
      o.updateMatrix();
      m.setMatrixAt(i, o.matrix);
    });
    m.instanceMatrix.needsUpdate = true;
  }, [field.stars, k]);

  useFrame((state) => {
    const p = progress.current ?? 0;
    if (root.current) {
      root.current.rotation.x = -0.72 + state.pointer.y * 0.06;
      root.current.rotation.z = 0.2 + p * 0.5 + state.pointer.x * 0.08;
    }
    // Loop along the measured path every 6 s.
    if (dot.current && path.length > 1) {
      const t = ((state.clock.elapsedTime / 6) % 1) * (path.length - 1);
      const i = Math.floor(t);
      dot.current.position.lerpVectors(path[i]!, path[Math.min(i + 1, path.length - 1)]!, t - i);
    }
  });

  return (
    <group ref={root} scale={0.8}>
      <mesh>
        <circleGeometry args={[2.85, 96]} />
        <meshBasicMaterial color={palette.surface} />
      </mesh>
      <mesh position={[0, 0, 0.001]}>
        <ringGeometry args={[2.84, 2.87, 128]} />
        <meshBasicMaterial color={palette.border} />
      </mesh>
      <instancedMesh ref={mesh} args={[undefined, undefined, field.stars.length]}>
        <circleGeometry args={[1, 16]} />
        <meshBasicMaterial color={palette.ink} />
      </instancedMesh>
      {path.length > 1 && <Line points={path} color={palette.accent} lineWidth={2} />}
      <mesh ref={dot}>
        <circleGeometry args={[0.07, 24]} />
        <meshBasicMaterial color={palette.accent} toneMapped={false} />
      </mesh>
    </group>
  );
}

export default function StarFieldScene({
  field,
  progress,
  narrow,
}: {
  field: StarField;
  progress: RefObject<number>;
  narrow: boolean;
}) {
  const palette = useMemo(() => readPalette(), []);
  return (
    <Canvas dpr={narrow ? [1, 1.5] : [1, 2]} camera={{ fov: narrow ? 44 : 30, position: [0, -0.45, 8.2] }} aria-hidden="true">
      <color attach="background" args={[palette.bg]} />
      <hemisphereLight args={[palette.surface, palette.border, 1.2]} />
      <directionalLight position={[2, 4, 5]} intensity={0.8} />
      <Plate field={field} progress={progress} />
    </Canvas>
  );
}
