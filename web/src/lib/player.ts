/** Time-lapse player state as a pure reducer, so the controls are testable without a browser. */

export const SPEEDS_FPS = [0.5, 1, 2, 4, 8] as const;

export interface PlayerState {
  count: number;
  index: number;
  playing: boolean;
  speedFps: number;
  loop: boolean;
  /** A/B blink: alternate between two chosen frames. */
  blink: { on: boolean; a: number; b: number; showingB: boolean };
  showFlags: boolean;
}

export type PlayerAction =
  | { type: "load"; count: number; index?: number; a?: number; b?: number }
  | { type: "togglePlay" }
  | { type: "pause" }
  | { type: "step"; by: number }
  | { type: "seek"; index: number }
  | { type: "tick" }
  | { type: "setSpeed"; fps: number }
  | { type: "toggleLoop" }
  | { type: "toggleBlink" }
  | { type: "setBlinkFrame"; which: "a" | "b"; index: number }
  | { type: "toggleFlags" };

const clamp = (i: number, count: number) => (count <= 0 ? 0 : Math.min(Math.max(Math.round(i), 0), count - 1));

export function initialPlayer(count = 0): PlayerState {
  return {
    count,
    index: 0,
    playing: false,
    speedFps: 2,
    loop: true,
    blink: { on: false, a: 0, b: Math.max(count - 1, 0), showingB: false },
    showFlags: false,
  };
}

export function playerReducer(s: PlayerState, action: PlayerAction): PlayerState {
  switch (action.type) {
    case "load": {
      const base = initialPlayer(action.count);
      return {
        ...base,
        index: clamp(action.index ?? 0, action.count),
        blink: {
          ...base.blink,
          a: clamp(action.a ?? 0, action.count),
          b: clamp(action.b ?? action.count - 1, action.count),
        },
      };
    }
    case "togglePlay":
      if (s.count < 2) return s;
      // Pressing play on the last frame without loop starts again from the first.
      if (!s.playing && !s.loop && !s.blink.on && s.index === s.count - 1) return { ...s, playing: true, index: 0 };
      return { ...s, playing: !s.playing };
    case "pause":
      return { ...s, playing: false };
    case "step":
      return { ...s, playing: false, blink: { ...s.blink, on: false }, index: clamp(s.index + action.by, s.count) };
    case "seek":
      return { ...s, blink: { ...s.blink, on: false }, index: clamp(action.index, s.count) };
    case "tick": {
      if (!s.playing || s.count < 2) return s;
      if (s.blink.on) {
        const showingB = !s.blink.showingB;
        return { ...s, index: showingB ? s.blink.b : s.blink.a, blink: { ...s.blink, showingB } };
      }
      const next = s.index + 1;
      if (next < s.count) return { ...s, index: next };
      return s.loop ? { ...s, index: 0 } : { ...s, playing: false };
    }
    case "setSpeed":
      return SPEEDS_FPS.includes(action.fps as (typeof SPEEDS_FPS)[number]) ? { ...s, speedFps: action.fps } : s;
    case "toggleLoop":
      return { ...s, loop: !s.loop };
    case "toggleBlink": {
      if (s.count < 2) return s;
      const on = !s.blink.on;
      return { ...s, playing: on, index: s.blink.a, blink: { ...s.blink, on, showingB: false } };
    }
    case "setBlinkFrame":
      return { ...s, blink: { ...s.blink, [action.which]: clamp(action.index, s.count) } };
    case "toggleFlags":
      return { ...s, showFlags: !s.showFlags };
  }
}
