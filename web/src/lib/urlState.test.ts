import { describe, expect, it } from "vitest";
import { DEFAULT_VIEW, parseView, serializeView } from "./urlState";

const parse = (q: string) => parseView(new URLSearchParams(q));

describe("URL view state", () => {
  it("round-trips a full view", () => {
    const v = parse("ra=133.7951&dec=-7.2451&fov=0.2&mode=difference&det=1,2,6&frame=7&a=0&b=2");
    expect(v).toMatchObject({ ra_deg: 133.7951, dec_deg: -7.2451, fov_deg: 0.2, mode: "difference", detectors: [1, 2, 6], frame: 7, a: 0, b: 2 });
    expect(parseView(serializeView(v))).toEqual(v);
  });

  it("prefers a benchmark target over raw coordinates when writing", () => {
    const v = parse("target=barnard&ra=1&dec=2");
    expect(v.target).toBe("barnard");
    expect(serializeView(v).toString()).toBe("target=barnard");
  });

  it("falls back to defaults on bad values", () => {
    const v = parse("target=planet9&ra=400&dec=10&fov=5&mode=x&det=0,9&frame=-1&a=1.5");
    expect(v).toEqual(DEFAULT_VIEW);
    expect(serializeView(DEFAULT_VIEW).toString()).toBe("");
  });
});
