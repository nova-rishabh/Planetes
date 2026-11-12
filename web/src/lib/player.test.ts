import { describe, expect, it } from "vitest";
import { initialPlayer, playerReducer, type PlayerAction, type PlayerState } from "./player";

const run = (s: PlayerState, ...actions: PlayerAction[]) => actions.reduce(playerReducer, s);
const loaded = (count: number) => playerReducer(initialPlayer(), { type: "load", count });

describe("playerReducer", () => {
  it("plays, loops and stops at the end without loop", () => {
    let s = run(loaded(3), { type: "togglePlay" }, { type: "tick" }, { type: "tick" });
    expect(s.index).toBe(2);
    expect(run(s, { type: "tick" }).index).toBe(0);
    s = run(s, { type: "toggleLoop" }, { type: "tick" });
    expect(s.playing).toBe(false);
    expect(s.index).toBe(2);
    expect(run(s, { type: "togglePlay" }).index).toBe(0);
  });

  it("steps and seeks inside the range and pauses on step", () => {
    const s = run(loaded(4), { type: "togglePlay" }, { type: "step", by: -1 });
    expect(s.index).toBe(0);
    expect(s.playing).toBe(false);
    expect(run(s, { type: "seek", index: 99 }).index).toBe(3);
  });

  it("blinks between A and B", () => {
    let s = run(loaded(5), { type: "setBlinkFrame", which: "a", index: 1 }, { type: "setBlinkFrame", which: "b", index: 3 });
    s = run(s, { type: "toggleBlink" });
    expect(s.index).toBe(1);
    expect(s.playing).toBe(true);
    s = run(s, { type: "tick" });
    expect(s.index).toBe(3);
    s = run(s, { type: "tick" });
    expect(s.index).toBe(1);
    expect(run(s, { type: "step", by: 1 }).blink.on).toBe(false);
  });

  it("does nothing useful with fewer than two frames", () => {
    expect(run(loaded(1), { type: "togglePlay" }).playing).toBe(false);
    expect(run(loaded(0), { type: "toggleBlink" }).blink.on).toBe(false);
  });

  it("only accepts listed speeds", () => {
    expect(run(loaded(3), { type: "setSpeed", fps: 4 }).speedFps).toBe(4);
    expect(run(loaded(3), { type: "setSpeed", fps: 3 }).speedFps).toBe(2);
  });
});
