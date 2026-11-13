"use client";

import dynamic from "next/dynamic";
import type { StarField } from "@/lib/landing";
import { LazyScene } from "./LazyScene";

const StarFieldScene = dynamic(() => import("./three/StarFieldScene"), { ssr: false });

/** Footer plate of real Gaia stars around Barnard's Star. */
export function StarFieldFigure({ field }: { field: StarField }) {
  return (
    <LazyScene
      className="sf3d-figure"
      label={`${field.stars.length} Gaia DR3 stars around Barnard's Star, with its path over a year in orange`}
      flat={null}
    >
      {({ narrow, progress }) => <StarFieldScene field={field} progress={progress} narrow={narrow} />}
    </LazyScene>
  );
}
