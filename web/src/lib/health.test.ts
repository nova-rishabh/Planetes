import { describe, expect, it } from "vitest";
import type { Health } from "@/types/contracts";
import { badgeFor, parseHealth } from "./health";

// Shape-only input for the pure mapping function; never shown in the app.
function health(irsa_tap: Health["irsa_tap"]): Health {
  return {
    schema_version: "1.0",
    status: "ok",
    code_version: "dev",
    irsa_tap,
    default_release: "QR3",
    cache_entries: 0,
  };
}

describe("badgeFor", () => {
  it("maps loading", () => {
    expect(badgeFor({ kind: "loading" })).toMatchObject({ label: "Checking API…", tone: "neutral" });
  });

  it("maps each irsa_tap value", () => {
    expect(badgeFor({ kind: "ok", health: health("ok") })).toMatchObject({ label: "NASA archive: ok", tone: "good" });
    expect(badgeFor({ kind: "ok", health: health("slow") })).toMatchObject({ label: "NASA archive: slow", tone: "warn" });
    expect(badgeFor({ kind: "ok", health: health("down") })).toMatchObject({ label: "NASA archive: down", tone: "bad" });
  });

  it("maps unreachable and keeps the reason", () => {
    expect(badgeFor({ kind: "unreachable", reason: "No response" })).toEqual({
      label: "API unreachable",
      tone: "bad",
      detail: "No response",
    });
  });
});

describe("parseHealth", () => {
  it("accepts a Health body and rejects anything else", () => {
    expect(parseHealth(health("ok"))).not.toBeNull();
    expect(parseHealth({ ...health("ok"), irsa_tap: "maybe" })).toBeNull();
    expect(parseHealth({ ...health("ok"), schema_version: "2.0" })).toBeNull();
    expect(parseHealth(null)).toBeNull();
    expect(parseHealth("ok")).toBeNull();
  });
});
