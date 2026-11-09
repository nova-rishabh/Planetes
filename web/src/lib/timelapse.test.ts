/* Loader tests. Responses carry no measurements: only error bodies, job states and an empty frame list. */
import { describe, expect, it } from "vitest";
import { loadBaked, parseTimelapse, resolveAsset, runLive, type LoadState } from "./timelapse";

const reply = (status: number, body: unknown) =>
  Promise.resolve(new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } }));

const EMPTY_RESULT = {
  schema_version: "1.0",
  request: { ra: 10, dec: 20 },
  grid: { projection: "TAN", crval_deg: [10, 20], crpix: [1, 1], cdelt_deg: 0.001, naxis: [1, 1], north_up: true },
  epochs: [],
  frames: [],
  stretch: null,
  flag_legend: [],
  provenance: { tap_query: null, generated_utc: "2026-11-09T00:00:00Z", code_version: "test" },
};

const noSleep = () => Promise.resolve();

describe("parseTimelapse", () => {
  it("accepts the contract shape and rejects others", () => {
    expect(parseTimelapse(EMPTY_RESULT)).not.toBeNull();
    expect(parseTimelapse({ ...EMPTY_RESULT, schema_version: "2.0" })).toBeNull();
    expect(parseTimelapse({ frames: [] })).toBeNull();
  });
});

describe("loadBaked", () => {
  it("reports a missing bake instead of inventing frames", async () => {
    const s = await loadBaked("barnard", "stacks", "https://x.test", () => reply(404, {}));
    expect(s.kind).toBe("missing");
  });

  it("resolves frame URLs against the JSON file", async () => {
    const s = await loadBaked("barnard", "stacks", "https://x.test", () => reply(200, EMPTY_RESULT));
    expect(s.kind).toBe("ready");
    if (s.kind !== "ready") return;
    expect(resolveAsset("./frames/f_0123456789ab.webp", s.baseUrl)).toBe(
      "https://x.test/data/targets/barnard/frames/f_0123456789ab.webp",
    );
  });
});

describe("runLive", () => {
  it("polls until done and resolves API frame URLs against the API", async () => {
    const answers = [
      reply(200, { schema_version: "1.0", job_id: "j_abc" }),
      reply(200, { schema_version: "1.0", job_id: "j_abc", kind: "timelapse", status: "running", progress: { done: 2, total: 9, stage: "fetching cutouts" }, result: null, error: null }),
      reply(200, { schema_version: "1.0", job_id: "j_abc", kind: "timelapse", status: "done", progress: { done: 9, total: 9, stage: "done" }, result: EMPTY_RESULT, error: null }),
    ];
    const seen: LoadState[] = [];
    const s = await runLive("https://api.test/", { ra: 10, dec: 20 }, (u) => seen.push(u), {
      fetchFn: () => answers.shift()!,
      sleep: noSleep,
    });
    expect(s.kind).toBe("ready");
    expect(seen.some((u) => u.kind === "loading" && u.stage === "fetching cutouts" && u.total === 9)).toBe(true);
    if (s.kind === "ready") expect(resolveAsset("/api/frames/f_0123456789ab.webp", s.baseUrl)).toBe("https://api.test/api/frames/f_0123456789ab.webp");
  });

  it("passes the contract error message and hint through", async () => {
    const answers = [
      reply(200, { schema_version: "1.0", job_id: "j_abc" }),
      reply(200, { schema_version: "1.0", job_id: "j_abc", kind: "timelapse", status: "error", progress: { done: 0, total: null, stage: "error" }, result: null, error: { code: "NO_COVERAGE", message: "No frames here", hint: "Try another spot" } }),
    ];
    const s = await runLive("https://api.test", { ra: 10, dec: 20 }, () => {}, { fetchFn: () => answers.shift()!, sleep: noSleep });
    expect(s).toEqual({ kind: "error", message: "No frames here", hint: "Try another spot" });
  });

  it("shows a 413 limit error from the POST", async () => {
    const s = await runLive("https://api.test", { ra: 10, dec: 20 }, () => {}, {
      fetchFn: () => reply(413, { schema_version: "1.0", error: { code: "TOO_LARGE", message: "max_frames is limited to 60", hint: null } }),
      sleep: noSleep,
    });
    expect(s).toEqual({ kind: "error", message: "max_frames is limited to 60", hint: null });
  });

  it("needs an API base", async () => {
    expect((await runLive(undefined, { ra: 1, dec: 1 }, () => {})).kind).toBe("error");
  });
});
