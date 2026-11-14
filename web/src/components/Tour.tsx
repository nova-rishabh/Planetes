"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { sendCue, type TourCue } from "@/lib/tour";

/** Guided tour (D1.6): five stops over the real viewer, each pointing at the control it explains. */
const STEPS: { at: string; title: string; text: string; cue: TourCue }[] = [
  {
    at: "plate",
    title: "1 · The plate",
    text: "Every frame here is a real SPHEREx exposure of this patch of sky. The orange ring is where the target should be on that date, moved for its known motion.",
    cue: "rest",
  },
  {
    at: "playback",
    title: "2 · Play it",
    text: "Play steps through the visits in time order. Anything that moves against the fixed stars jumps from frame to frame. Watch the ring.",
    cue: "play",
  },
  {
    at: "blink",
    title: "3 · Blink two frames",
    text: "Now it blinks the first and last visit, the way Pluto was found. A moving object flips position; the stars around it stay put.",
    cue: "blink",
  },
  {
    at: "options",
    title: "4 · Check the data",
    text: "Flags shows pixels SPHEREx marked as unreliable (saturated, cosmic rays). Catalogue stars puts Gaia and AllWISE stars on top. Sound plays each frame as a note.",
    cue: "stars",
  },
  {
    at: "panels",
    title: "5 · Two Opinions",
    text: "Below: the measured spectrum and the verdict. Motion and colour each give an opinion; Planetes says whether they agree, and why.",
    cue: "rest",
  },
];

export function Tour({ autoStart = false }: { autoStart?: boolean }) {
  const [step, setStep] = useState<number | null>(null);
  const started = useRef(false);

  useEffect(() => {
    if (!autoStart || started.current) return;
    started.current = true;
    const t = window.setTimeout(() => setStep(0), 400);
    return () => window.clearTimeout(t);
  }, [autoStart]);
  const cardRef = useRef<HTMLDivElement>(null);

  const close = useCallback(() => {
    sendCue("rest");
    setStep(null);
  }, []);

  useEffect(() => {
    if (step === null) return;
    const s = STEPS[step];
    const el = s ? document.querySelector<HTMLElement>(`[data-tour="${s.at}"]`) : null;
    el?.classList.add("tour-focus");
    if (s) sendCue(s.cue);
    const reduced = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
    el?.scrollIntoView({ behavior: reduced ? "auto" : "smooth", block: "center" });
    cardRef.current?.focus();
    return () => el?.classList.remove("tour-focus");
  }, [step]);

  useEffect(() => {
    if (step === null) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") close();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [step, close]);

  if (step === null) {
    return (
      <button type="button" className="btn tour-start" onClick={() => setStep(0)}>
        Take the 1-minute tour
      </button>
    );
  }
  const s = STEPS[step]!;
  const last = step === STEPS.length - 1;
  return (
    <div className="tour-card panel" role="dialog" aria-label="Guided tour" tabIndex={-1} ref={cardRef}>
      <p className="tour-title">{s.title}</p>
      <p className="tour-text">{s.text}</p>
      <div className="tour-nav">
        <button type="button" className="btn" onClick={close}>
          Close
        </button>
        <span className="mono tour-count">
          {step + 1}/{STEPS.length}
        </span>
        <button type="button" className="btn" disabled={step === 0} onClick={() => setStep(step - 1)}>
          Back
        </button>
        <button type="button" className="btn btn-primary" onClick={() => (last ? close() : setStep(step + 1))}>
          {last ? "Done" : "Next"}
        </button>
      </div>
    </div>
  );
}
