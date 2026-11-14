"use client";

import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { BENCHMARKS, benchmarkName } from "@/lib/benchmarks";
import { formatPosition, parsePosition } from "@/lib/coords";
import { loadBaked, loadBakedJson, runLive, type LoadState } from "@/lib/timelapse";
import { parseOverlays } from "@/lib/overlays";
import type { Overlays } from "@/types/contracts";
import { FOV_MAX_DEG, FOV_MIN_DEG, MODES, parseView, serializeView, type Mode, type ViewState } from "@/lib/urlState";
import { ObjectPanels } from "./ObjectPanels";
import { Player } from "./Player";
import { SkyContext } from "./SkyContext";
import { Tour } from "./Tour";
import { wantsTour } from "@/lib/tour";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE;
const FOV_CHOICES = [0.03, 0.05, 0.1, 0.2, 0.3, 0.5].filter((f) => f >= FOV_MIN_DEG && f <= FOV_MAX_DEG);
const MODE_LABEL: Record<Mode, string> = {
  exposures: "Single exposures",
  stacks: "Detector stacks",
  difference: "Differences",
  sum: "Sum",
  color: "Colour",
};

/** Writes the view into the address bar without a navigation, so the link always reproduces the view. */
function writeUrl(v: ViewState) {
  const q = serializeView(v).toString();
  window.history.replaceState(null, "", q ? `?${q}` : window.location.pathname);
}

function LoadView({ state, onRetry }: { state: LoadState; onRetry: () => void }) {
  switch (state.kind) {
    case "idle":
      return (
        <div className="plate empty">
          <p>Pick a benchmark or type a position to see every SPHEREx image of that patch of sky.</p>
        </div>
      );
    case "loading": {
      const pct = state.total ? Math.round((100 * state.done) / state.total) : null;
      return (
        <div className="plate empty" role="status" aria-live="polite">
          <p>{state.stage}{state.total ? ` · ${state.done}/${state.total}` : "…"}</p>
          <progress max={100} value={pct ?? undefined} />
          {state.slow ? <p className="hint-on-plate">This can take a minute: images come straight from NASA&apos;s archive.</p> : null}
        </div>
      );
    }
    case "missing":
      return (
        <div className="plate empty">
          <p>{state.message}</p>
          <p className="hint-on-plate">The benchmarks are baked from real SPHEREx frames once the image pipeline is ready.</p>
        </div>
      );
    case "error":
      return (
        <div className="plate empty" role="alert">
          <p>{state.message}</p>
          {state.hint ? <p className="hint-on-plate">{state.hint}</p> : null}
          <button type="button" className="btn" onClick={onRetry}>Try again</button>
        </div>
      );
    case "ready":
      return null;
  }
}

/** Coordinate input, benchmark buttons, mode/FOV and the player. `embed` hides everything but the player. */
export function Viewer({ embed = false }: { embed?: boolean }) {
  const params = useSearchParams();
  const [view, setView] = useState<ViewState>(() => parseView(new URLSearchParams(params.toString())));
  const [state, setState] = useState<LoadState>({ kind: "idle" });
  const [text, setText] = useState(() =>
    view.ra_deg !== null && view.dec_deg !== null ? `${view.ra_deg} ${view.dec_deg}` : "",
  );
  const [inputError, setInputError] = useState<string | null>(null);
  const [attempt, setAttempt] = useState(0);
  const [tourLink] = useState(() => wantsTour(new URLSearchParams(params.toString())));

  const { target, ra_deg, dec_deg, fov_deg, mode, detectors } = view;
  const detKey = detectors.join(",");
  const [baked, setBaked] = useState<{ target: string; value: Overlays } | null>(null);
  const overlays = target && baked?.target === target ? baked.value : null;

  // Catalogue stars for baked targets (overlays.json). Missing or invalid -> no markers, never invented ones.
  useEffect(() => {
    if (!target) return;
    const ctrl = new AbortController();
    loadBakedJson(target, "overlays.json", window.location.origin, parseOverlays, ctrl.signal).then(
      (r) => r.kind === "ready" && setBaked({ target, value: r.value }),
      () => {},
    );
    return () => ctrl.abort();
  }, [target]);

  useEffect(() => {
    if (!target && (ra_deg === null || dec_deg === null)) return;
    const ctrl = new AbortController();
    const go = async () => {
      setState({ kind: "loading", stage: "Loading", done: 0, total: null, slow: false });
      const final = target
        ? await loadBaked(target, mode, window.location.origin, fetch, ctrl.signal)
        : await runLive(
            API_BASE,
            { ra: ra_deg!, dec: dec_deg!, fov_deg, mode, detectors: detKey.split(",").map(Number) as [number] },
            (s) => !ctrl.signal.aborted && setState(s),
            { signal: ctrl.signal },
          );
      if (!ctrl.signal.aborted) setState(final);
    };
    go().catch(() => {
      /* aborted */
    });
    return () => ctrl.abort();
  }, [target, ra_deg, dec_deg, fov_deg, mode, detKey, attempt]);

  const update = (patch: Partial<ViewState>) => {
    const next = { ...view, frame: 0, a: null, b: null, ...patch };
    setView(next);
    writeUrl(next);
  };

  const onSettle = useCallback(
    ({ frame, a, b }: { frame: number; a: number; b: number }) => {
      setView((v) => {
        const next = { ...v, frame, a, b };
        writeUrl(next);
        return next;
      });
    },
    [],
  );

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    const r = parsePosition(text);
    if (!r.ok) {
      setInputError(r.reason);
      return;
    }
    setInputError(null);
    update({ target: null, ra_deg: r.pos.ra_deg, dec_deg: r.pos.dec_deg });
  };

  // Benchmarks have no typed position: the map uses the position recorded in the loaded time-lapse.
  const skyPos =
    ra_deg !== null && dec_deg !== null
      ? { ra_deg, dec_deg }
      : state.kind === "ready"
        ? { ra_deg: state.result.request.ra, dec_deg: state.result.request.dec }
        : null;

  const heading = target
    ? benchmarkName(target)
    : ra_deg !== null && dec_deg !== null
      ? formatPosition({ ra_deg, dec_deg })
      : null;

  return (
    <div className={embed ? "viewer viewer-embed" : "viewer"}>
      {embed ? null : (
        <section className="panel search" aria-label="Choose a patch of sky">
          <form onSubmit={submit} className="search-form">
            <label className="field grow">
              Position (RA Dec)
              <input
                className="mono"
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="269.4521 4.6934  or  17 57 48.5 +04 41 36"
                aria-invalid={inputError !== null}
                aria-describedby="pos-help"
              />
            </label>
            <label className="field">
              Field of view
              <select value={fov_deg} onChange={(e) => update({ fov_deg: Number(e.target.value) })}>
                {FOV_CHOICES.map((f) => (
                  <option key={f} value={f}>{`${f}°`}</option>
                ))}
              </select>
            </label>
            <label className="field">
              Show
              <select value={mode} onChange={(e) => update({ mode: e.target.value as Mode })}>
                {MODES.map((m) => (
                  <option key={m} value={m}>{MODE_LABEL[m]}</option>
                ))}
              </select>
            </label>
            <button type="submit" className="btn btn-primary">Show time-lapse</button>
          </form>
          <p id="pos-help" className={inputError ? "error-text" : "hint"}>
            {inputError ?? "Degrees, or hours-minutes-seconds for RA. ICRS."}
          </p>
          <div className="benchmarks" role="group" aria-label="Benchmark targets">
            {BENCHMARKS.map((b) => (
              <button key={b.id} type="button" className="toggle" aria-pressed={target === b.id} onClick={() => update({ target: b.id, ra_deg: null, dec_deg: null })}>
                {b.name}
              </button>
            ))}
          </div>
        </section>
      )}

      {heading ? (
        <div className="view-heading-row">
          <h2 className="view-heading">{heading}</h2>
          {!embed ? <Tour autoStart={tourLink && state.kind === "ready"} /> : null}
        </div>
      ) : null}
      {state.kind === "ready" ? (
        <Player
          key={`${target ?? `${ra_deg},${dec_deg}`}-${mode}-${fov_deg}-${detKey}`}
          result={state.result}
          baseUrl={state.baseUrl}
          startIndex={view.frame}
          blinkA={view.a}
          blinkB={view.b}
          onSettle={onSettle}
          overlays={overlays}
        />
      ) : (
        <LoadView state={state} onRetry={() => setAttempt((n) => n + 1)} />
      )}
      {!embed && heading ? (
        <div data-tour="panels">
          <ObjectPanels key={target ?? "position"} target={target} />
        </div>
      ) : null}
      {!embed && skyPos ? <SkyContext ra_deg={skyPos.ra_deg} dec_deg={skyPos.dec_deg} fov_deg={fov_deg} /> : null}
    </div>
  );
}
