"use client";

import { useEffect, useRef, useState } from "react";
import { cubeCutout, PIXEL_ARCSEC, type CubeCutout } from "@/lib/spherexCube";

/** Error codes that mean the archive (or our API in front of it) could not run the search: not a bad request. */
export const ARCHIVE_DOWN_CODES = new Set(["IRSA_ERROR", "IRSA_TIMEOUT", "API_UNREACHABLE"]);

/**
 * Shown only after the main path failed: IRSA's search did not answer for a typed position. Explains what failed and
 * shows real SPHEREx pixels from NASA's open-data copy of the DR1 all-sky cube instead (all visits combined).
 */
export function ArchiveFallback({ ra_deg, dec_deg, code, onRetry }: { ra_deg: number; dec_deg: number; code: string; onRetry: () => void }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [state, setState] = useState<{ kind: "loading" } | { kind: "ready"; cut: CubeCutout } | { kind: "error" }>({ kind: "loading" });

  useEffect(() => {
    const d = dialog.current;
    if (d && !d.open && typeof d.showModal === "function") d.showModal();
  }, []);

  useEffect(() => {
    const ctl = new AbortController();
    cubeCutout(ra_deg, dec_deg, 24, ctl.signal)
      .then((cut) => setState({ kind: "ready", cut }))
      .catch(() => !ctl.signal.aborted && setState({ kind: "error" }));
    return () => ctl.abort();
  }, [ra_deg, dec_deg]);

  const ours = code === "API_UNREACHABLE";
  return (
    <>
      <dialog ref={dialog} className="outage" aria-labelledby="outage-title">
        <h2 id="outage-title">{ours ? "Our server is not answering" : "NASA’s archive search is down right now"}</h2>
        {ours ? (
          <p>
            The Planetes API that asks NASA&apos;s archive for images did not reply. It may be restarting. Your position is fine.
          </p>
        ) : (
          <p>
            <b>What failed:</b> the search service of the NASA/IPAC Infrared Science Archive (IRSA), the only place that
            lists every SPHEREx image of a spot. It is returning errors from IRSA&apos;s own servers (&ldquo;502 Proxy
            Error&rdquo;), for every app that uses it. Nothing is wrong with your position or with Planetes.
          </p>
        )}
        <p>
          <b>What we show instead:</b> real SPHEREx pixels of this spot from NASA&apos;s open-data copy of the SPHEREx
          Data Release 1 all-sky map, hosted on Amazon Web Services. Same mission, same colours, with all visits combined
          into one deep image.
        </p>
        <p>
          <b>What you lose:</b> the visit-by-visit time-lapse, so movement and brightness changes cannot be seen until
          the archive is back. The five ready-made targets above still play their full time-lapse from saved real data.
        </p>
        <div className="outage-actions">
          <button type="button" className="btn btn-primary" onClick={() => dialog.current?.close()}>
            Show the backup map
          </button>
          <button type="button" className="btn" onClick={() => { dialog.current?.close(); onRetry(); }}>
            Try the archive again
          </button>
        </div>
      </dialog>

      <section className="panel fallback" aria-label="Backup view from the SPHEREx all-sky map">
        <h2>Backup view: SPHEREx all-sky map</h2>
        <p className="hint">
          {ours ? "Our API" : "IRSA’s search"} is not answering, so this is the SPHEREx DR1 all-sky map (all visits
          combined) from{" "}
          <a href="https://irsa.ipac.caltech.edu/cloud_access/" target="_blank" rel="noreferrer">NASA&apos;s open-data copy on AWS</a>.
          No time-lapse here: it switches back to the archive as soon as it answers.
        </p>
        {state.kind === "loading" ? <p className="hint">Reading the SPHEREx pixels around this position…</p> : null}
        {state.kind === "error" ? <p className="error-text">The backup map could not be read either. Please try again later.</p> : null}
        {state.kind === "ready" ? <FallbackView cut={state.cut} /> : null}
        <p className="hint">
          <button type="button" className="btn" onClick={() => dialog.current?.showModal()}>What happened?</button>
        </p>
      </section>
    </>
  );
}

function asinhStretch(data: Float32Array): (v: number) => number {
  const vals = Array.from(data).filter(Number.isFinite).sort((a, b) => a - b);
  const lo = vals[Math.floor(vals.length * 0.1)] ?? 0;
  const hi = vals[Math.floor(vals.length * 0.99)] ?? 1;
  const s = Math.max(hi - lo, 1e-6);
  const k = 30;
  const norm = Math.asinh(k);
  return (v) => (Number.isFinite(v) ? Math.max(0, Math.min(1, Math.asinh((k * (v - lo)) / s) / norm)) : 0);
}

function FallbackView({ cut }: { cut: CubeCutout }) {
  const canvas = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const c = canvas.current;
    if (!c) return;
    c.width = cut.width;
    c.height = cut.height;
    const ctx = c.getContext("2d");
    if (!ctx) return;
    const img = ctx.createImageData(cut.width, cut.height);
    const [b, g, r] = cut.planes;
    const st = cut.planes.map((p) => asinhStretch(p.data));
    for (let i = 0; i < cut.width * cut.height; i++) {
      img.data[i * 4] = 255 * st[2]!(r!.data[i]!);
      img.data[i * 4 + 1] = 255 * st[1]!(g!.data[i]!);
      img.data[i * 4 + 2] = 255 * st[0]!(b!.data[i]!);
      img.data[i * 4 + 3] = 255;
    }
    ctx.putImageData(img, 0, 0);
  }, [cut]);

  const pts = cut.spectrum.filter((p) => p.value != null) as { um: number; detector: number; value: number }[];
  const W = 560, H = 240, L = 48, R = 12, T = 12, B = 32;
  const ymax = Math.max(0.01, ...pts.map((p) => p.value)) * 1.1;
  const ymin = Math.min(0, ...pts.map((p) => p.value));
  const x = (um: number) => L + ((um - 0.7) / (5.05 - 0.7)) * (W - L - R);
  const y = (v: number) => T + (1 - (v - ymin) / (ymax - ymin)) * (H - T - B);
  const fov = ((cut.width * PIXEL_ARCSEC) / 60).toFixed(1);

  return (
    <div className="fallback-body">
      <figure>
        <div className="fallback-plate plate">
          <canvas ref={canvas} aria-label="SPHEREx colour image of this position" />
          <span className="fallback-mark" style={{ left: `${((cut.target.x + 0.5) / cut.width) * 100}%`, top: `${((cut.target.y + 0.5) / cut.height) * 100}%` }} />
        </div>
        <figcaption className="hint">
          Real SPHEREx pixels, {fov}′ across; blue {cut.planes[0]!.um.toFixed(2)} µm, green {cut.planes[1]!.um.toFixed(2)} µm,
          red {cut.planes[2]!.um.toFixed(2)} µm. Sky tiles are in HEALPix orientation, so north is not straight up.
        </figcaption>
      </figure>
      <figure>
        <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Spectrum of the brightest pixel at this position, 102 SPHEREx colours">
          <line x1={L} y1={y(0)} x2={W - R} y2={y(0)} className="fallback-axis" />
          {[1, 2, 3, 4, 5].map((w) => (
            <text key={w} x={x(w)} y={H - 10} className="fallback-tick" textAnchor="middle">{w} µm</text>
          ))}
          {pts.map((p) => (
            <circle key={p.um} cx={x(p.um)} cy={y(p.value)} r={3.2} style={{ fill: `var(--epoch-${p.detector})` }} />
          ))}
        </svg>
        <figcaption className="hint">
          Brightest pixel within 20″ of the position, minus the local sky, in all 102 SPHEREx colours (MJy/sr; colour =
          detector D1–D6). Combined over all visits, so a fast-moving star is smeared.
        </figcaption>
      </figure>
    </div>
  );
}
