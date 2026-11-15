import { describe, expect, it } from "vitest";
import { formatPosition, parsePosition } from "./coords";

function pos(text: string) {
  const r = parsePosition(text);
  if (!r.ok) throw new Error(r.reason);
  return r.pos;
}

describe("parsePosition", () => {
  it("reads decimal degrees with space or comma", () => {
    expect(pos("269.4521 4.6934")).toEqual({ ra_deg: 269.4521, dec_deg: 4.6934 });
    expect(pos("133.7951, -7.2451")).toEqual({ ra_deg: 133.7951, dec_deg: -7.2451 });
  });

  it("reads sexagesimal with RA in hours", () => {
    const p = pos("17 57 48.5 +04 41 36");
    expect(p.ra_deg).toBeCloseTo((17 + 57 / 60 + 48.5 / 3600) * 15, 9);
    expect(p.dec_deg).toBeCloseTo(4 + 41 / 60 + 36 / 3600, 9);
    expect(pos("17:57:48.5, -04:41:36").dec_deg).toBeCloseTo(-(4 + 41 / 60 + 36 / 3600), 9);
    expect(pos("17h57m48.5s +4d41m36s").ra_deg).toBeCloseTo(p.ra_deg, 9);
  });

  it("keeps the sign of a -00 declination", () => {
    expect(pos("10 00 00 -00 30 00").dec_deg).toBeCloseTo(-0.5, 9);
  });

  it("rejects bad input", () => {
    for (const bad of ["", "abc", "400 10", "10 95", "-1 5", "1 2 3"]) {
      expect(parsePosition(bad).ok).toBe(false);
    }
  });
});

describe("formatPosition", () => {
  it("uses degree signs and an explicit sign on Dec", () => {
    expect(formatPosition({ ra_deg: 269.4521, dec_deg: 4.6934 })).toBe("RA 269.4521°  Dec +4.6934°");
    expect(formatPosition({ ra_deg: 1, dec_deg: -7.2451 })).toBe("RA 1.0000°  Dec −7.2451°");
  });
});
