"use client";

import { useCallback, useEffect, useMemo, useReducer, useRef, useState } from "react";
import type { Frame, Overlays, TimelapseResult } from "@/types/contracts";
import { markersFor } from "@/lib/overlays";
import { initialPlayer, playerReducer, SPEEDS_FPS } from "@/lib/player";
import { resolveAsset } from "@/lib/timelapse";
import { gainFor, pitchHz, tick, tone } from "@/lib/sound";
import { TOUR_EVENT, type TourCue } from "@/lib/tour";
import { FrameMeta } from "./FrameMeta";

interface Props {
  result: TimelapseResult;
  baseUrl: string;
  startIndex?: number;
  blinkA?: number | null;
  blinkB?: number | null;
  /** Reports the frame and blink choice when playback stops, for the shareable URL. */
  onSettle?: (s: { frame: number; a: number; b: number }) => void;
  /** Gaia DR3 / AllWISE stars moved to each frame date (overlays.json); null when not available. */
  overlays?: Overlays | null;
}

type Loaded = { image?: HTMLImageElement; flags?: HTMLImageElement };

function loadImage(src: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error(src));
    img.src = src;
  });
}

/** Canvas pixels per SPHEREx grid pixel, so markers can be thinner than one 6-arcsec pixel. */
const UPSCALE = 8;

function cssVar(el: Element, name: string): string {
  return getComputedStyle(el).getPropertyValue(name).trim();
}

function frameLabel(f: Frame): string {
  return `D${f.detector ?? "?"} ${f.kind}${f.epoch_index !== null ? `, epoch ${f.epoch_index}` : ""}`;
}

/**
 * Time-lapse player (D1.3): frames on a dark plate, play/step/scrub/speed/loop, A/B blink and the flag
 * overlay. Frames are already stretched images on the common grid (docs/03 §5), drawn pixel for pixel.
 */
export function Player({ result, baseUrl, startIndex = 0, blinkA = null, blinkB = null, onSettle, overlays = null }: Props) {
  const [showStars, setShowStars] = useState(true);
  const [sound, setSound] = useState(false);
  const frames = result.frames;
  const [s, dispatch] = useReducer(playerReducer, undefined, () =>
    playerReducer(initialPlayer(), {
      type: "load",
      count: frames.length,
      index: startIndex,
      a: blinkA ?? undefined,
      b: blinkB ?? undefined,
    }),
  );
  const [loadedCount, bumpLoaded] = useReducer((n: number) => n + 1, 0);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const cache = useRef(new Map<string, Loaded>());
  const [w, h] = result.grid.naxis;

  // Preload every frame (and its flag overlay) once.
  useEffect(() => {
    for (const f of frames) {
      if (cache.current.has(f.id)) continue;
      const entry: Loaded = {};
      cache.current.set(f.id, entry);
      loadImage(resolveAsset(f.image_url, baseUrl))
        .then((img) => {
          entry.image = img;
          bumpLoaded();
        })
        .catch(() => {});
      if (f.flags_url) {
        loadImage(resolveAsset(f.flags_url, baseUrl))
          .then((img) => {
            entry.flags = img;
            bumpLoaded();
          })
          .catch(() => {});
      }
    }
  }, [frames, baseUrl]);

  // Draw the current frame.
  const frame = frames[s.index];
  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext("2d");
    if (!canvas || !ctx || !frame) return;
    ctx.setTransform(UPSCALE, 0, 0, UPSCALE, 0, 0);
    ctx.imageSmoothingEnabled = false;
    ctx.fillStyle = cssVar(canvas, "--plate");
    ctx.fillRect(0, 0, w, h);
    const entry = cache.current.get(frame.id);
    if (entry?.image) ctx.drawImage(entry.image, 0, 0, w, h);
    if (s.showFlags && entry?.flags) ctx.drawImage(entry.flags, 0, 0, w, h);
    if (showStars && overlays && typeof frame.mjd === "number") {
      const r = 1.6;
      ctx.lineWidth = 1.5 / UPSCALE;
      for (const m of markersFor(overlays, result.grid, frame.mjd)) {
        const x = m.x + 0.5;
        const y = h - (m.y + 0.5);
        ctx.strokeStyle = cssVar(canvas, m.catalog === "AllWISE" ? "--epoch-3" : "--epoch-6");
        ctx.beginPath();
        if (m.catalog === "AllWISE") ctx.rect(x - r, y - r, 2 * r, 2 * r);
        else ctx.arc(x, y, r, 0, 2 * Math.PI);
        ctx.stroke();
      }
    }
    if (frame.target_xy) {
      // target_xy: 0-based pixel (x right, y north/up, origin at the lower-left like numpy origin="lower").
      const x = frame.target_xy[0] + 0.5;
      const y = h - (frame.target_xy[1] + 0.5);
      const gap = Math.max(3, w / 40);
      const len = Math.max(4, w / 25);
      ctx.strokeStyle = cssVar(canvas, "--accent-fill");
      ctx.lineWidth = 2 / UPSCALE;
      ctx.beginPath();
      ctx.moveTo(x - gap - len, y);
      ctx.lineTo(x - gap, y);
      ctx.moveTo(x, y - gap - len);
      ctx.lineTo(x, y - gap);
      ctx.stroke();
    }
  }, [frame, s.showFlags, w, h, loadedCount, showStars, overlays, result.grid]);

  // Playback clock.
  useEffect(() => {
    if (!s.playing) return;
    const t = setInterval(() => dispatch({ type: "tick" }), 1000 / s.speedFps);
    return () => clearInterval(t);
  }, [s.playing, s.speedFps]);

  useEffect(() => {
    if (!s.playing) onSettle?.({ frame: s.index, a: s.blink.a, b: s.blink.b });
  }, [s.playing, s.index, s.blink.a, s.blink.b, onSettle]);

  const onKey = useCallback((e: React.KeyboardEvent) => {
    const map: Record<string, () => void> = {
      " ": () => dispatch({ type: "togglePlay" }),
      ArrowLeft: () => dispatch({ type: "step", by: -1 }),
      ArrowRight: () => dispatch({ type: "step", by: 1 }),
      b: () => dispatch({ type: "toggleBlink" }),
      f: () => dispatch({ type: "toggleFlags" }),
      l: () => dispatch({ type: "toggleLoop" }),
    };
    const fn = map[e.key];
    if (fn && !(e.target instanceof HTMLInputElement || e.target instanceof HTMLSelectElement)) {
      e.preventDefault();
      fn();
    }
  }, []);

  // Guided tour cues: play, blink first vs last visit, show catalogue stars, or stop.
  const live = useRef(s);
  useEffect(() => {
    live.current = s;
  }, [s]);
  useEffect(() => {
    const onCue = (e: Event) => {
      const cue = (e as CustomEvent<TourCue>).detail;
      const now = live.current;
      if (now.blink.on && cue !== "blink") dispatch({ type: "toggleBlink" });
      if (cue === "play") {
        if (!now.loop) dispatch({ type: "toggleLoop" });
        if (!now.playing) dispatch({ type: "togglePlay" });
        return;
      }
      if (now.playing) dispatch({ type: "pause" });
      if (cue === "blink" && frames.length > 1) {
        // First and last visit on the same detector, so only the sky changes between them.
        const det = frames[0]!.detector;
        let last = frames.length - 1;
        while (last > 0 && frames[last]!.detector !== det) last--;
        dispatch({ type: "setBlinkFrame", which: "a", index: 0 });
        dispatch({ type: "setBlinkFrame", which: "b", index: last > 0 ? last : frames.length - 1 });
        if (!now.blink.on) dispatch({ type: "toggleBlink" });
      }
      if (cue === "stars") setShowStars(true);
    };
    window.addEventListener(TOUR_EVENT, onCue);
    return () => window.removeEventListener(TOUR_EVENT, onCue);
  }, [frames]);

  // Sonified time-lapse (D1.7): one note per frame while playing or stepping; a tick on each blink flip.
  const lastSound = useRef<string | null>(null);
  useEffect(() => {
    if (!sound || !frame) return;
    const key = `${frame.id}:${s.blink.on ? (s.blink.showingB ? "B" : "A") : ""}`;
    if (lastSound.current === key) return;
    lastSound.current = key;
    if (s.blink.on) {
      tick();
      return;
    }
    let grey: number | null = null;
    const canvas = canvasRef.current;
    if (canvas && frame.target_xy) {
      try {
        const px = Math.round((frame.target_xy[0] + 0.5) * UPSCALE);
        const py = Math.round((h - (frame.target_xy[1] + 0.5)) * UPSCALE);
        grey = canvas.getContext("2d")?.getImageData(px, py, 1, 1).data[0] ?? null;
      } catch {
        grey = null; // cross-origin frames can't be read; use the default loudness
      }
    }
    tone(pitchHz(frame.wavelength_um), gainFor(grey));
  }, [sound, frame, s.blink.on, s.blink.showingB, h]);

  const options = useMemo(
    () => frames.map((f, i) => <option key={f.id} value={i}>{`${i + 1} · ${frameLabel(f)}`}</option>),
    [frames],
  );

  if (!frame) {
    return <p className="notice">SPHEREx has no frames for this request.</p>;
  }

  return (
    <section className="player" onKeyDown={onKey} tabIndex={0} aria-label="Time-lapse player">
      <figure className="plate player-figure" data-tour="plate">
        <canvas ref={canvasRef} width={w * UPSCALE} height={h * UPSCALE} className="player-canvas" role="img" aria-label={`Frame ${s.index + 1} of ${frames.length}: ${frameLabel(frame)}`} />
        <figcaption className="caption">
          Fig. 1 · {frameLabel(frame)}
          {frame.utc ? ` · ${frame.utc.replace("T", " ").replace(/:\d\d(\.\d+)?Z$/, " UTC")}` : ""}
          {s.blink.on ? ` · blinking ${s.blink.showingB ? "B" : "A"}` : ""}
          {overlays && showStars ? " · ○ Gaia DR3 □ AllWISE, moved to this date" : ""}
        </figcaption>
      </figure>

      <div className="controls" role="group" aria-label="Playback" data-tour="playback">
        <button type="button" className="btn" onClick={() => dispatch({ type: "step", by: -1 })} aria-label="Previous frame">◀</button>
        <button type="button" className="btn btn-primary" onClick={() => dispatch({ type: "togglePlay" })} aria-pressed={s.playing}>
          {s.playing ? "Pause" : "Play"}
        </button>
        <button type="button" className="btn" onClick={() => dispatch({ type: "step", by: 1 })} aria-label="Next frame">▶</button>
        <label className="scrub">
          <span className="sr-only">Frame</span>
          <input
            type="range"
            min={0}
            max={frames.length - 1}
            value={s.index}
            onChange={(e) => dispatch({ type: "seek", index: Number(e.target.value) })}
          />
        </label>
        <span className="mono counter">
          {s.index + 1}/{frames.length}
        </span>
      </div>

      <div className="controls" role="group" aria-label="Options" data-tour="options">
        <label className="field">
          Speed
          <select value={s.speedFps} onChange={(e) => dispatch({ type: "setSpeed", fps: Number(e.target.value) })}>
            {SPEEDS_FPS.map((v) => (
              <option key={v} value={v}>{`${v} fps`}</option>
            ))}
          </select>
        </label>
        <button type="button" className="toggle" aria-pressed={s.loop} onClick={() => dispatch({ type: "toggleLoop" })}>Loop</button>
        <button type="button" className="toggle" aria-pressed={s.showFlags} onClick={() => dispatch({ type: "toggleFlags" })}>Flags</button>
        <button
          type="button"
          className="toggle"
          aria-pressed={sound}
          onClick={() => setSound((v) => !v)}
          title="Hear each frame: pitch follows wavelength, loudness follows the target's brightness"
        >
          Sound
        </button>
        {overlays ? (
          <button type="button" className="toggle" aria-pressed={showStars} onClick={() => setShowStars((v) => !v)}>Catalogue stars</button>
        ) : null}
      </div>

      <div className="controls" role="group" aria-label="Blink two frames" data-tour="blink">
        <label className="field">
          A
          <select value={s.blink.a} onChange={(e) => dispatch({ type: "setBlinkFrame", which: "a", index: Number(e.target.value) })}>{options}</select>
        </label>
        <label className="field">
          B
          <select value={s.blink.b} onChange={(e) => dispatch({ type: "setBlinkFrame", which: "b", index: Number(e.target.value) })}>{options}</select>
        </label>
        <button type="button" className="toggle" aria-pressed={s.blink.on} onClick={() => dispatch({ type: "toggleBlink" })}>Blink A/B</button>
      </div>
      <p className="hint">Keys: Space play/pause · ← → step · B blink · F flags · L loop · Sound: high note = short infrared, low = long; louder = brighter target</p>

      <FrameMeta frame={frame} legend={result.flag_legend} showLegend={s.showFlags} />
    </section>
  );
}
