/**
 * Loads a TimelapseResult from a baked file or from a live API job. The player never knows which:
 * both end as { result, baseUrl }, and frame URLs are resolved against baseUrl (docs/03 §6).
 */

import type { ErrorBody, Job, TimelapseRequest, TimelapseResult } from "@/types/contracts";
import type { BenchmarkId } from "./benchmarks";
import type { Mode } from "./urlState";

export type LoadState =
  | { kind: "idle" }
  | { kind: "loading"; stage: string; done: number; total: number | null; slow: boolean }
  | { kind: "ready"; result: TimelapseResult; baseUrl: string }
  | { kind: "missing"; message: string }
  | { kind: "error"; message: string; hint: string | null };

type FetchFn = typeof fetch;
type Sleep = (ms: number, signal?: AbortSignal) => Promise<void>;

const defaultSleep: Sleep = (ms, signal) =>
  new Promise((resolve, reject) => {
    const t = setTimeout(resolve, ms);
    signal?.addEventListener("abort", () => {
      clearTimeout(t);
      reject(new DOMException("Aborted", "AbortError"));
    });
  });

/** After this long without an answer we tell the user the API may be starting up. */
export const SLOW_AFTER_MS = 4000;
const POLL_MS = [1000, 1500, 2000, 3000];
const MAX_POLLS = 600;

/** Accept a body only if it has the TimelapseResult fields the player relies on. */
export function parseTimelapse(body: unknown): TimelapseResult | null {
  if (typeof body !== "object" || body === null) return null;
  const b = body as Record<string, unknown>;
  if (b.schema_version !== "1.0" || !Array.isArray(b.frames) || !Array.isArray(b.epochs)) return null;
  if (typeof b.grid !== "object" || b.grid === null || !Array.isArray(b.flag_legend)) return null;
  return body as TimelapseResult;
}

function errorFrom(body: unknown, fallback: string): { message: string; hint: string | null } {
  const err = (body as { error?: ErrorBody } | null)?.error;
  if (err && typeof err.message === "string") return { message: err.message, hint: err.hint ?? null };
  return { message: fallback, hint: null };
}

async function json(res: Response): Promise<unknown> {
  try {
    return await res.json();
  } catch {
    return null;
  }
}

export function resolveAsset(url: string, baseUrl: string): string {
  return new URL(url, baseUrl).toString();
}

/** Baked benchmark: public/data/targets/{id}/timelapse_{mode}.json. */
export async function loadBaked(
  id: BenchmarkId,
  mode: Mode,
  origin: string,
  fetchFn: FetchFn = fetch,
  signal?: AbortSignal,
): Promise<LoadState> {
  const url = new URL(`/data/targets/${id}/timelapse_${mode}.json`, origin).toString();
  let res: Response;
  try {
    res = await fetchFn(url, { signal });
  } catch (e) {
    if (signal?.aborted) throw e;
    return { kind: "error", message: "Could not load the baked time-lapse", hint: "Check your connection." };
  }
  if (res.status === 404) {
    return { kind: "missing", message: `No baked ${mode} time-lapse for this target yet.` };
  }
  if (!res.ok) return { kind: "error", message: `Baked file returned HTTP ${res.status}`, hint: null };
  const result = parseTimelapse(await json(res));
  if (!result) return { kind: "error", message: "The baked file does not match the data contract", hint: null };
  return { kind: "ready", result, baseUrl: url };
}

/** Live: POST /api/timelapse, then poll /api/jobs/{id} until done or error. Calls onUpdate as it goes. */
export async function runLive(
  apiBase: string | undefined,
  request: TimelapseRequest,
  onUpdate: (s: LoadState) => void,
  opts: { fetchFn?: FetchFn; sleep?: Sleep; signal?: AbortSignal; now?: () => number } = {},
): Promise<LoadState> {
  const { fetchFn = fetch, sleep = defaultSleep, signal, now = Date.now } = opts;
  if (!apiBase) return { kind: "error", message: "The live API is not configured", hint: "NEXT_PUBLIC_API_BASE is not set." };
  const base = apiBase.replace(/\/+$/, "");
  const started = now();
  const loading = (stage: string, done = 0, total: number | null = null): LoadState => ({
    kind: "loading",
    stage,
    done,
    total,
    slow: now() - started > SLOW_AFTER_MS,
  });

  onUpdate(loading("Asking NASA's archive for images"));
  const slowTimer = setTimeout(() => onUpdate(loading("Waiting for the API to answer")), SLOW_AFTER_MS + 50);
  let created: Response;
  try {
    created = await fetchFn(`${base}/api/timelapse`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
      signal,
    });
  } catch (e) {
    if (signal?.aborted) throw e;
    return { kind: "error", message: "The API did not answer", hint: "It may be restarting; try again in a minute." };
  } finally {
    clearTimeout(slowTimer);
  }
  const createdBody = await json(created);
  if (!created.ok) return { kind: "error", ...errorFrom(createdBody, `The API returned HTTP ${created.status}`) };
  const jobId = (createdBody as { job_id?: unknown } | null)?.job_id;
  if (typeof jobId !== "string") return { kind: "error", message: "Unexpected answer from the API", hint: null };

  for (let i = 0; i < MAX_POLLS; i++) {
    await sleep(POLL_MS[Math.min(i, POLL_MS.length - 1)] ?? 3000, signal);
    let res: Response;
    try {
      res = await fetchFn(`${base}/api/jobs/${encodeURIComponent(jobId)}`, { signal, cache: "no-store" });
    } catch (e) {
      if (signal?.aborted) throw e;
      continue; // one dropped poll is not a failure
    }
    const body = await json(res);
    if (!res.ok) return { kind: "error", ...errorFrom(body, `The API returned HTTP ${res.status}`) };
    const job = body as Job;
    if (job.status === "error") return { kind: "error", ...errorFrom({ error: job.error }, "The job failed") };
    if (job.status === "done") {
      const result = parseTimelapse(job.result);
      if (!result) return { kind: "error", message: "The result does not match the data contract", hint: null };
      return { kind: "ready", result, baseUrl: `${base}/` };
    }
    onUpdate(loading(job.progress?.stage ?? job.status, job.progress?.done ?? 0, job.progress?.total ?? null));
  }
  return { kind: "error", message: "The job is taking too long", hint: "Try a smaller field of view or fewer frames." };
}
