"use client";

import { useEffect, useState } from "react";
import type { Opinions, SpectrumResult } from "@/types/contracts";
import type { BenchmarkId } from "@/lib/benchmarks";
import { parseOpinions } from "@/lib/opinions";
import { loadBakedJson, parseSpectrum } from "@/lib/timelapse";
import { OpinionsPanel } from "./OpinionsPanel";
import { SpectrumChart } from "./SpectrumChart";

type Slot<T> = { kind: "loading" } | { kind: "ready"; value: T } | { kind: "missing" } | { kind: "error"; message: string };

function Placeholder({ title, text }: { title: string; text: string }) {
  return (
    <section className="panel">
      <h2>{title}</h2>
      <p className="hint">{text}</p>
    </section>
  );
}

/** Spectrum and Two Opinions for the target. Benchmarks read baked files; typed positions come later (D2.4). */
export function ObjectPanels({ target }: { target: BenchmarkId | null }) {
  const [spectrum, setSpectrum] = useState<Slot<SpectrumResult>>({ kind: "loading" });
  const [opinions, setOpinions] = useState<Slot<Opinions>>({ kind: "loading" });

  useEffect(() => {
    if (!target) return;
    const ctrl = new AbortController();
    const origin = window.location.origin;
    loadBakedJson(target, "spectrum.json", origin, parseSpectrum, ctrl.signal).then(setSpectrum, () => {});
    loadBakedJson(target, "opinions.json", origin, parseOpinions, ctrl.signal).then(setOpinions, () => {});
    return () => ctrl.abort();
  }, [target]);

  if (!target) {
    return (
      <div className="object-panels">
        <Placeholder title="Spectrum" text="Spectra for typed positions arrive with the brightness-measuring step of the pipeline." />
        <Placeholder title="Two Opinions" text="Needs a spectrum and a motion measurement for one object." />
      </div>
    );
  }

  const say = (s: Slot<unknown>, what: string) =>
    s.kind === "loading" ? "Loading…" : s.kind === "missing" ? `No baked ${what} for this target yet.` : s.kind === "error" ? `The ${what} ${s.message}.` : "";

  return (
    <div className="object-panels">
      {spectrum.kind === "ready" ? <SpectrumChart result={spectrum.value} /> : <Placeholder title="Spectrum" text={say(spectrum, "spectrum")} />}
      {opinions.kind === "ready" ? <OpinionsPanel opinions={opinions.value} /> : <Placeholder title="Two Opinions" text={say(opinions, "verdict")} />}
    </div>
  );
}
