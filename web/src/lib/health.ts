import type { Health } from "@/types/contracts";

/** What the health check produced: still loading, a valid Health payload, or no usable answer. */
export type HealthState =
  | { kind: "loading" }
  | { kind: "ok"; health: Health }
  | { kind: "unreachable"; reason: string };

export type BadgeTone = "neutral" | "good" | "warn" | "bad";

export interface Badge {
  label: string;
  tone: BadgeTone;
  detail: string | null;
}

/** Map a health-check state to the badge shown on the page. */
export function badgeFor(state: HealthState): Badge {
  switch (state.kind) {
    case "loading":
      return { label: "Checking API…", tone: "neutral", detail: null };
    case "unreachable":
      return { label: "API unreachable", tone: "bad", detail: state.reason };
    case "ok": {
      const { irsa_tap, code_version } = state.health;
      const detail = `API ${code_version}`;
      if (irsa_tap === "ok") return { label: "NASA archive: ok", tone: "good", detail };
      if (irsa_tap === "slow") return { label: "NASA archive: slow", tone: "warn", detail };
      return { label: "NASA archive: down", tone: "bad", detail };
    }
  }
}

const IRSA_STATES = new Set(["ok", "slow", "down"]);

/** Accept a parsed JSON body only if it has the Health fields the badge relies on. */
export function parseHealth(body: unknown): Health | null {
  if (typeof body !== "object" || body === null) return null;
  const b = body as Record<string, unknown>;
  if (b.schema_version !== "1.0" || b.status !== "ok") return null;
  if (typeof b.irsa_tap !== "string" || !IRSA_STATES.has(b.irsa_tap)) return null;
  if (typeof b.code_version !== "string") return null;
  return body as Health;
}

/** Call `${apiBase}/api/health` and turn the outcome into a HealthState. */
export async function fetchHealth(apiBase: string | undefined, signal?: AbortSignal): Promise<HealthState> {
  if (!apiBase) return { kind: "unreachable", reason: "NEXT_PUBLIC_API_BASE is not set" };
  try {
    const res = await fetch(`${apiBase.replace(/\/+$/, "")}/api/health`, { signal, cache: "no-store" });
    if (!res.ok) return { kind: "unreachable", reason: `HTTP ${res.status}` };
    const health = parseHealth(await res.json());
    return health ? { kind: "ok", health } : { kind: "unreachable", reason: "Unexpected response" };
  } catch (err) {
    if (signal?.aborted) throw err;
    return { kind: "unreachable", reason: "No response" };
  }
}
