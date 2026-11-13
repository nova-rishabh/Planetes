import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { parseValidation, plain, stateOf } from "./validation";

describe("validation table (docs/VALIDATION.md)", () => {
  const rows = parseValidation(readFileSync(join(__dirname, "..", "..", "..", "docs", "VALIDATION.md"), "utf8"));

  it("has all ten tests V1-V10 in order", () => {
    expect(rows.map((r) => r.id)).toEqual(Array.from({ length: 10 }, (_, i) => `V${i + 1}`));
  });

  it("reads pass, cut and not-run states", () => {
    const state = (id: string) => stateOf(rows.find((r) => r.id === id)!);
    expect(state("V5")).toBe("pass");
    expect(state("V6")).toBe("pending");
    expect(state("V10")).toBe("pass");
    // No test is cut at the moment; check the parser on a copy of a row marked cut.
    expect(stateOf({ ...rows[0]!, result: "cut" })).toBe("cut");
  });

  it("strips markdown for display", () => {
    expect(plain("`motion.py` **bold** ✅ PASS")).toBe("motion.py bold PASS");
  });
});
