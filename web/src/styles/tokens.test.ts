import { readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

const SRC = join(__dirname, "..");
const TOKENS = join(__dirname, "tokens.css");
const HEX = /#[0-9a-fA-F]{3,8}\b/;

function files(dir: string): string[] {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name);
    return statSync(path).isDirectory() ? files(path) : [path];
  });
}

describe("design tokens (docs/09)", () => {
  it("defines every palette C token", () => {
    const css = readFileSync(TOKENS, "utf8");
    for (const token of ["bg", "surface", "border", "ink", "ink-muted", "ui", "accent-fill", "accent-text", "plate"]) {
      expect(css).toMatch(new RegExp(`--${token}:\\s*#`));
    }
  });

  it("keeps raw hex colours out of every file except tokens.css", () => {
    const offenders = files(SRC)
      .filter((f) => /\.(css|tsx?)$/.test(f) && f !== TOKENS && !f.endsWith(".test.ts"))
      .filter((f) => !f.endsWith(join("types", "contracts.ts")))
      .filter((f) => HEX.test(readFileSync(f, "utf8")));
    expect(offenders).toEqual([]);
  });
});
