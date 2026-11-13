"use client";

import dynamic from "next/dynamic";
import type { StarField } from "@/lib/landing";
import { LazyScene } from "./LazyScene";

const OpinionsScene = dynamic(() => import("./three/OpinionsScene"), { ssr: false });
const StarFieldScene = dynamic(() => import("./three/StarFieldScene"), { ssr: false });

/** Two glass blocks above the Two Opinions cards (symbols only; nothing shown when 3D can't run). */
export function OpinionsFigure() {
  return (
    <LazyScene className="op3d-figure" flat={null}>
      {({ narrow, progress }) => <OpinionsScene progress={progress} narrow={narrow} />}
    </LazyScene>
  );
}

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
