"use client";

import { useEffect, useRef, useState } from "react";

/**
 * Sky context map with Aladin Lite v3 (CDS). Loaded at runtime from jsDelivr, pinned to the npm
 * release we checked (3.8.2), so the library is not part of our bundle. API names used here were read
 * from that release: default export A, A.init (promise), A.aladin(el, options), aladin.setBaseImageLayer(id),
 * aladin.gotoRaDec(ra, dec), aladin.setFoV(deg). Surveys are passed as full HiPS URLs.
 */
const ALADIN_URL = "https://cdn.jsdelivr.net/npm/aladin-lite@3.8.2/dist/aladin.js";
const LOAD_TIMEOUT_MS = 20000;

/**
 * The same three CDS surveys (ivo://CDS/P/allWISE/color, ivo://CDS/P/2MASS/color, ivo://CDS/P/DSS2/color) from
 * several hosts, tried in order; the first that answers is used. Mirror URLs come from the CDS MocServer
 * records (hips_service_url, _1, _2), and every host sends Access-Control-Allow-Origin: * (checked). ESASky
 * and CDS have each been down for hours at a time, so one host is never enough.
 */
const ESASKY = "https://skies.esac.esa.int";
const IRSA_HIPS = "https://irsa.ipac.caltech.edu/data/hips/CDS";
const CDS = "https://alasky.cds.unistra.fr";
export const SURVEYS = [
  { key: "allwise", label: "AllWISE", note: "infrared, 3.4–22 µm", mirrors: [`${ESASKY}/AllWISEColor`, `${IRSA_HIPS}/AllWISE/RGB-W4-W2-W1`, `${CDS}/AllWISE/RGB-W4-W2-W1`] },
  { key: "2mass", label: "2MASS", note: "near-infrared, 1.2–2.2 µm", mirrors: [`${ESASKY}/2MASSColor`, `${IRSA_HIPS}/2MASS/Color`, `${CDS}/2MASS/Color`] },
  { key: "dss2", label: "DSS2", note: "visible light", mirrors: [`${ESASKY}/DSSColor`, "https://casda.csiro.au/hips/DSS2/color", `${CDS}/DSS/DSSColor`] },
] as const;
type SurveyKey = (typeof SURVEYS)[number]["key"];
const HOST_NAMES: Record<string, string> = {
  "skies.esac.esa.int": "ESA ESASky",
  "irsa.ipac.caltech.edu": "NASA/IPAC IRSA",
  "casda.csiro.au": "CSIRO CASDA",
  "alasky.cds.unistra.fr": "CDS",
};
const hostName = (url: string | null) => (url ? (HOST_NAMES[new URL(url).host] ?? new URL(url).host) : "");

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

/** All mirrors are probed at once; the first in the listed order that answers wins. */
async function firstReachable(mirrors: readonly string[]): Promise<string | null> {
  const ok = await Promise.all(mirrors.map(hostReachable));
  return mirrors[ok.indexOf(true)] ?? null;
}

function withTimeout<T>(p: Promise<T>, ms: number): Promise<T> {
  return Promise.race([p, new Promise<T>((_, reject) => setTimeout(() => reject(new Error("timeout")), ms))]);
}

export function SkyContext({ ra_deg, dec_deg, fov_deg }: { ra_deg: number; dec_deg: number; fov_deg: number }) {
  const el = useRef<HTMLDivElement>(null);
  const view = useRef<AladinView | null>(null);
  const [status, setStatus] = useState<"loading" | "ready" | "failed">("loading");
  const [survey, setSurvey] = useState<SurveyKey>(SURVEYS[0].key);
  const [urls, setUrls] = useState<Partial<Record<SurveyKey, string | null>>>({});
  // Show a wider patch than the time-lapse so the neighbourhood is visible.
  const contextFov = Math.min(Math.max(fov_deg * 4, 0.2), 3);

  useEffect(() => {
    let alive = true;
    const found = Promise.all(SURVEYS.map((s) => firstReachable(s.mirrors))).then((list) => {
      const map = Object.fromEntries(SURVEYS.map((s, i) => [s.key, list[i] ?? null])) as Record<SurveyKey, string | null>;
      if (alive) setUrls(map);
      return map;
    });
    Promise.all([found, withTimeout(loadAladin().then((A) => A.init.then(() => A)), LOAD_TIMEOUT_MS)])
      .then(([map, A]) => {
        if (!alive || !el.current) return;
        const first = SURVEYS.find((s) => map[s.key]);
        if (!first) {
          setStatus("failed");
          return;
        }
        if (!view.current) {
          setSurvey(first.key);
          view.current = A.aladin(el.current, {
            survey: map[first.key],
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

  const choose = (key: SurveyKey) => {
    const url = urls[key];
    if (!url) return;
    setSurvey(key);
    view.current?.setBaseImageLayer(url);
  };

  return (
    <section className="panel sky" aria-label="Sky around this position">
      <h2>Around this spot</h2>
      <div className="controls" role="group" aria-label="Survey">
        {SURVEYS.map((s) => (
          <button key={s.key} type="button" className="toggle" aria-pressed={survey === s.key} onClick={() => choose(s.key)} disabled={status !== "ready" || !urls[s.key]} title={urls[s.key] ? s.note : `${s.label}: no image server is answering right now`}>
            {s.label}
          </button>
        ))}
      </div>
      <div ref={el} className="sky-map plate" aria-hidden={status !== "ready"}>
        {status === "loading" ? <p className="sky-msg">Loading the sky map…</p> : null}
        {status === "failed" ? <p className="sky-msg">None of the sky survey image servers (ESA ESASky, NASA/IPAC IRSA, CDS) is answering right now. Try again later.</p> : null}
      </div>
      {urls[survey] && !urls[survey]!.startsWith(ESASKY) ? (
        <p className="sky-note" role="status">
          ESA&apos;s ESASky image server is not answering right now, so this map shows the same{" "}
          {SURVEYS.find((s) => s.key === survey)?.label} survey from {hostName(urls[survey] ?? null)}&apos;s copy. Nothing
          on our side is broken; the map switches back by itself when ESASky answers.
        </p>
      ) : null}
      <p className="hint">
        {SURVEYS.find((s) => s.key === survey)?.label} survey, {contextFov.toFixed(2)}° wide, centred on the time-lapse. Map:{" "}
        <a href="https://aladin.cds.unistra.fr/" target="_blank" rel="noreferrer">Aladin Lite</a> (CDS, Strasbourg)
        {urls[survey] ? `; images via ${hostName(urls[survey] ?? null)}` : ""}.
      </p>
    </section>
  );
}
