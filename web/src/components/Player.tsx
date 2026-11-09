"use client";

import { useCallback, useEffect, useMemo, useReducer, useRef } from "react";
import type { Frame, TimelapseResult } from "@/types/contracts";
import { initialPlayer, playerReducer, SPEEDS_FPS } from "@/lib/player";
import { resolveAsset } from "@/lib/timelapse";
import { FrameMeta } from "./FrameMeta";

interface Props {
  result: TimelapseResult;
  baseUrl: string;
  startIndex?: number;
  blinkA?: number | null;
  blinkB?: number | null;
  /** Reports the frame and blink choice when playback stops, for the shareable URL. */
  onSettle?: (s: { frame: number; a: number; b: number }) => void;
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
export function Player({ result, baseUrl, startIndex = 0, blinkA = null, blinkB = null, onSettle }: Props) {
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
    ctx.imageSmoothingEnabled = false;
    ctx.fillStyle = cssVar(canvas, "--plate");
    ctx.fillRect(0, 0, w, h);
    const entry = cache.current.get(frame.id);
    if (entry?.image) ctx.drawImage(entry.image, 0, 0, w, h);
    if (s.showFlags && entry?.flags) ctx.drawImage(entry.flags, 0, 0, w, h);
    if (frame.target_xy) {
      // target_xy: 0-based pixel (x right, y north/up, origin at the lower-left like numpy origin="lower").
      const x = frame.target_xy[0] + 0.5;
      const y = h - (frame.target_xy[1] + 0.5);
      const gap = Math.max(3, w / 40);
      const len = Math.max(4, w / 25);
      ctx.strokeStyle = cssVar(canvas, "--accent-fill");
      ctx.lineWidth = Math.max(1, w / 240);
      ctx.beginPath();
      ctx.moveTo(x - gap - len, y);
      ctx.lineTo(x - gap, y);
      ctx.moveTo(x, y - gap - len);
      ctx.lineTo(x, y - gap);
      ctx.stroke();
    }
  }, [frame, s.showFlags, w, h, loadedCount]);

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

  const options = useMemo(
    () => frames.map((f, i) => <option key={f.id} value={i}>{`${i + 1} · ${frameLabel(f)}`}</option>),
    [frames],
  );

  if (!frame) {
    return <p className="notice">SPHEREx has no frames for this request.</p>;
  }

  return (
    <section className="player" onKeyDown={onKey} tabIndex={0} aria-label="Time-lapse player">
      <figure className="plate player-figure">
        <canvas ref={canvasRef} width={w} height={h} className="player-canvas" role="img" aria-label={`Frame ${s.index + 1} of ${frames.length}: ${frameLabel(frame)}`} />
        <figcaption className="caption">
          Fig. 1 · {frameLabel(frame)}
          {frame.utc ? ` · ${frame.utc.replace("T", " ").replace(/:\d\d(\.\d+)?Z$/, " UTC")}` : ""}
          {s.blink.on ? ` · blinking ${s.blink.showingB ? "B" : "A"}` : ""}
        </figcaption>
      </figure>

      <div className="controls" role="group" aria-label="Playback">
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

      <div className="controls" role="group" aria-label="Options">
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
      </div>

      <div className="controls" role="group" aria-label="Blink two frames">
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
      <p className="hint">Keys: Space play/pause · ← → step · B blink · F flags · L loop</p>

      <FrameMeta frame={frame} legend={result.flag_legend} showLegend={s.showFlags} />
    </section>
  );
}
