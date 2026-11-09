"use client";

import { useEffect, useRef, useState } from "react";

/**
 * Sky context map (D1.4) with Aladin Lite v3 (CDS). Loaded at runtime from jsDelivr, pinned to the npm
 * release we checked (3.8.2), so the library is not part of our bundle. API names used here were read
 * from that release: default export A, A.init (promise), A.aladin(el, options), aladin.setBaseImageLayer(id),
 * aladin.gotoRaDec(ra, dec), aladin.setFoV(deg). Surveys are passed as full HiPS URLs.
 */
const ALADIN_URL = "https://cdn.jsdelivr.net/npm/aladin-lite@3.8.2/dist/aladin.js";
const LOAD_TIMEOUT_MS = 20000;

/**
 * ESA ESASky copies of the CDS surveys (their properties give creator_did ivo://CDS/P/allWISE/color,
 * ivo://CDS/P/2MASS/color, ivo://CDS/P/DSS2/color; they send Access-Control-Allow-Origin: *, checked Nov 9).
 * Full URLs because CDS itself was down worldwide on Nov 9 and IRSA's copies block browsers (no CORS).
 */
const ESASKY = "https://skies.esac.esa.int";
export const SURVEYS = [
  { id: `${ESASKY}/AllWISEColor`, label: "AllWISE", note: "infrared, 3.4–22 µm" },
  { id: `${ESASKY}/2MASSColor`, label: "2MASS", note: "near-infrared, 1.2–2.2 µm" },
  { id: `${ESASKY}/DSSColor`, label: "DSS2", note: "visible light" },
] as const;

interface AladinView {
  setBaseImageLayer(id: string): void;
  gotoRaDec(ra: number, dec: number): void;
  setFoV(deg: number): void;
}
interface AladinLib {
  init: Promise<void>;
  aladin(el: HTMLElement, options: Record<string, unknown>): AladinView;
}

let libPromise: Promise<AladinLib> | null = null;
function loadAladin(): Promise<AladinLib> {
  libPromise ??= import(/* webpackIgnore: true */ /* turbopackIgnore: true */ ALADIN_URL).then(
    (m: { default: AladinLib }) => m.default,
  );
  return libPromise;
}

/** Before showing the map we check the survey host answers, so an outage gives a message, not a grey box. */
const PROBE_TIMEOUT_MS = 8000;

async function hostReachable(surveyUrl: string): Promise<boolean> {
  try {
    const res = await fetch(`${surveyUrl}/properties`, { signal: AbortSignal.timeout(PROBE_TIMEOUT_MS), cache: "no-store" });
    return res.ok;
  } catch {
    return false;
  }
}

function withTimeout<T>(p: Promise<T>, ms: number): Promise<T> {
  return Promise.race([p, new Promise<T>((_, reject) => setTimeout(() => reject(new Error("timeout")), ms))]);
}

export function SkyContext({ ra_deg, dec_deg, fov_deg }: { ra_deg: number; dec_deg: number; fov_deg: number }) {
  const el = useRef<HTMLDivElement>(null);
  const view = useRef<AladinView | null>(null);
  const [status, setStatus] = useState<"loading" | "ready" | "failed">("loading");
  const [survey, setSurvey] = useState<string>(SURVEYS[0].id);
  // Show a wider patch than the time-lapse so the neighbourhood is visible.
  const contextFov = Math.min(Math.max(fov_deg * 4, 0.2), 3);

  useEffect(() => {
    let alive = true;
    hostReachable(SURVEYS[0].id).then((ok) => {
      if (!ok && alive) setStatus("failed");
    });
    withTimeout(
      loadAladin().then((A) => A.init.then(() => A)),
      LOAD_TIMEOUT_MS,
    )
      .then((A) => {
        if (!alive || !el.current) return;
        if (!view.current) {
          view.current = A.aladin(el.current, {
            survey: SURVEYS[0].id,
            target: `${ra_deg} ${dec_deg}`,
            fov: contextFov,
            cooFrame: "ICRS",
            showReticle: true,
            reticleColor: getComputedStyle(el.current).getPropertyValue("--accent-fill").trim(),
            showCooGrid: false,
            showFrame: false,
            showFullscreenControl: false,
            showLayersControl: false,
            showProjectionControl: false,
            showSettingsControl: false,
            showShareControl: false,
            showSimbadPointerControl: false,
            showContextMenu: false,
            showStatusBar: false,
            showZoomControl: true,
          });
        } else {
          view.current.gotoRaDec(ra_deg, dec_deg);
          view.current.setFoV(contextFov);
        }
        setStatus((s) => (s === "failed" ? s : "ready"));
      })
      .catch(() => alive && setStatus("failed"));
    return () => {
      alive = false;
    };
  }, [ra_deg, dec_deg, contextFov]);

  const choose = (id: string) => {
    setSurvey(id);
    view.current?.setBaseImageLayer(id);
  };

  return (
    <section className="panel sky" aria-label="Sky around this position">
      <h2>Around this spot</h2>
      <div className="controls" role="group" aria-label="Survey">
        {SURVEYS.map((s) => (
          <button key={s.id} type="button" className="toggle" aria-pressed={survey === s.id} onClick={() => choose(s.id)} disabled={status !== "ready"} title={s.note}>
            {s.label}
          </button>
        ))}
      </div>
      <div ref={el} className="sky-map plate" aria-hidden={status !== "ready"}>
        {status === "loading" ? <p className="sky-msg">Loading the sky map…</p> : null}
        {status === "failed" ? <p className="sky-msg">The sky survey images (from ESA&apos;s ESASky) are not loading right now. Try again later.</p> : null}
      </div>
      <p className="hint">
        {SURVEYS.find((s) => s.id === survey)?.label} survey, {contextFov.toFixed(2)}° wide, centred on the time-lapse. Map:{" "}
        <a href="https://aladin.cds.unistra.fr/" target="_blank" rel="noreferrer">Aladin Lite</a> (CDS, Strasbourg); images via ESA ESASky.
      </p>
    </section>
  );
}
