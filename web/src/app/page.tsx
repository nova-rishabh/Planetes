import Link from "next/link";
import { SiteNav } from "@/components/SiteNav";
import { BlinkPlate } from "@/components/landing/BlinkPlate";
import { LegacyLinkRedirect } from "@/components/landing/LegacyLinkRedirect";
import { Colour3D } from "@/components/landing/Colour3D";
import { Hero3D } from "@/components/landing/Hero3D";
import { PlateLoop } from "@/components/landing/PlateLoop";
import { Reveal } from "@/components/landing/Reveal";
import { SpectrumSketch } from "@/components/landing/SpectrumSketch";
import { BENCHMARKS } from "@/lib/benchmarks";
import {
  acrossDetectors,
  blinkPair,
  fmtDate,
  loadOpinions,
  loadSpectrum,
  loadTarget,
  oneDetectorRun,
} from "@/lib/landing";
import { SPHEREX_SINGLE_VISIT_AB, evaluate, EARTH_RADIUS_KM } from "@/lib/planetx";

/** Why each benchmark is in the set (plain words, checked against docs/04 §1). */
const WHY: Record<string, string> = {
  barnard: "The fastest-moving star in our sky. Too bright for SPHEREx's pixels, so it tests motion, not colour.",
  wise0855: "The coldest brown dwarf known, almost invisible below 3.5 µm. It tests how faint we can go.",
  epsindib: "A pair of brown dwarfs 3.6 parsecs away, faint enough to measure. It tests the spectrum.",
  rwaur: "A young star whose brightness changes. It tests that variability is not mistaken for motion.",
  rdra: "A pulsating red giant near the north ecliptic pole, seen on many visits. Bright and saturated.",
};

// Read at build time from the baked benchmark files (real SPHEREx frames only).
const barnard = loadTarget("barnard");
const barnardRun = barnard ? oneDetectorRun(barnard) : [];
const blink = barnard ? blinkPair(barnard) : null;
const stackFrames = barnardRun.map((f) => ({
  src: f.src,
  xy: f.xy,
  utc: f.utc,
  detector: f.detector,
  wavelength_um: f.wavelength_um,
}));
const eps = loadTarget("epsindib");
const epsColours = eps ? acrossDetectors(eps) : [];
const epsSpectrum = loadSpectrum("epsindib");
const epsOpinions = loadOpinions("epsindib");
const thumbs = BENCHMARKS.map((b) => ({ ...b, t: loadTarget(b.id) }));
const p9 = evaluate(2.6 * EARTH_RADIUS_KM, 0.5, 700, 40, 1);
const p9Best = p9.bands.reduce((a, b) => (b.ab < a.ab ? b : a));

export default function Home() {
  const heroText = (
    <>
      <p className="lp-kicker mono">NASA SPHEREx · 0.75–5 µm · every visit since Aug 2025</p>
      <h1 className="lp-title">Watch the infrared sky move.</h1>
      <p className="lp-lede">
        Planetes pulls every SPHEREx image of one patch of sky and plays them as a time-lapse. Things that move jump
        between frames. Then it measures their colour, and asks whether the motion and the colour tell the same story.
      </p>
      <form className="lp-go" action="/viewer" method="get">
        <label className="field">
          <span>RA (°)</span>
          <input name="ra" inputMode="decimal" className="mono" placeholder="269.4485" required pattern="[0-9.]+" />
        </label>
        <label className="field">
          <span>Dec (°)</span>
          <input name="dec" inputMode="decimal" className="mono" placeholder="4.7394" required pattern="-?[0-9.]+" />
        </label>
        <button type="submit" className="btn btn-primary">
          Open time-lapse
        </button>
      </form>
      <p className="lp-or">
        or start with a benchmark: <Link href="/viewer?target=barnard">Barnard&apos;s Star</Link> ·{" "}
        <Link href="/viewer?target=epsindib">ε Indi B</Link> · <Link href="/viewer?target=wise0855">WISE 0855</Link>
      </p>
    </>
  );

  return (
    <main className="landing">
      <LegacyLinkRedirect />
      <div className="app lp-top">
        <SiteNav current="/" />
      </div>

      {/* 1 · Hero: the first thing on screen is a real SPHEREx time-lapse */}
      <Hero3D
        heroText={heroText}
        frames={stackFrames}
        naxis={barnard?.naxis ?? [1, 1]}
        movedArcsec={blink?.movedArcsec ?? null}
        days={blink ? Math.round((Date.parse(blink.b.utc) - Date.parse(blink.a.utc)) / 86400000) : null}
        flat={
          <section className="lp-hero app">
            <div className="lp-hero-text">{heroText}</div>
            {barnard && barnardRun.length > 1 && (
              <div className="lp-hero-plate">
                <PlateLoop frames={barnardRun} naxis={barnard.naxis} label="Barnard's Star" />
                <p className="lp-figcap">
                  <span className="mono">Fig. 1</span> Barnard&apos;s Star in {barnardRun.length} real SPHEREx
                  exposures, one detector, {fmtDate(barnardRun[0]!.utc)} to{" "}
                  {fmtDate(barnardRun[barnardRun.length - 1]!.utc)}. The orange ring follows the star; the line is its
                  path.
                </p>
              </div>
            )}
          </section>
        }
      />

      {/* 2 · The blink comparator */}
      {barnard && blink && (
        <section className="lp-scene lp-scene-split app">
          <Reveal className="lp-scene-text">
            <p className="lp-step mono">01 · Blink</p>
            <h2>The oldest trick for finding things that move.</h2>
            <p>
              In 1930 Clyde Tombaugh found Pluto by flipping between two photographs of the same stars, taken days
              apart. Everything fixed stays still. Anything that moved jumps.
            </p>
            <p>
              Planetes does the same with SPHEREx. These two frames of Barnard&apos;s Star are{" "}
              {Math.round((Date.parse(blink.b.utc) - Date.parse(blink.a.utc)) / 86400000)} days apart
              {blink.movedArcsec !== null && (
                <>
                  , and the star moved <strong className="lp-accent">{blink.movedArcsec.toFixed(1)}″</strong>
                </>
              )}
              . That&apos;s about{" "}
              {(blink.movedArcsec ?? 0) > 0 ? (blink.movedArcsec! / barnard.cdeltArcsec).toFixed(1) : "–"} SPHEREx
              pixels.
            </p>
          </Reveal>
          <Reveal>
            <BlinkPlate a={blink.a} b={blink.b} naxis={barnard.naxis} label="Barnard's Star" />
          </Reveal>
        </section>
      )}

      {/* 3 · 102 colours */}
      {eps && epsColours.length > 0 && (
        <Colour3D
          tiles={epsColours.map((f) => ({ src: f.src, detector: f.detector, wavelength_um: f.wavelength_um }))}
          points={epsSpectrum?.points.map((p) => ({ um: p.um, ujy: p.ujy, det: p.det })) ?? []}
          nUsed={epsSpectrum?.nUsed ?? 0}
          nTotal={epsSpectrum?.nTotal ?? 0}
          spectrumLine={epsOpinions?.spectrum ?? null}
          flat={
            <section className="lp-scene app">
              <Reveal className="lp-scene-text lp-narrow">
                <p className="lp-step mono">02 · Colour</p>
                <h2>One patch of sky, 102 colours of infrared.</h2>
                <p>
                  SPHEREx has six detectors, each seeing a slice of infrared from 0.75 to 5 µm. Here is ε Indi B, a pair of
                  brown dwarfs, in each of them. Put every visit together and you get its spectrum, measured, not looked up.
                </p>
              </Reveal>
              <Reveal>
                <ol className="lp-colours">
                  {epsColours.map((f, k) => (
                    <li key={f.src} style={{ transitionDelay: `${k * 90}ms` }}>
                      <div className="plate lp-mini">
                        {/* eslint-disable-next-line @next/next/no-img-element -- real baked WebP */}
                        <img
                          src={f.src}
                          alt={`ε Indi B on detector D${f.detector}`}
                          width={eps.naxis[0]}
                          height={eps.naxis[1]}
                        />
                      </div>
                      <span className="mono">
                        D{f.detector} · {f.wavelength_um?.toFixed(2)} µm
                      </span>
                    </li>
                  ))}
                </ol>
              </Reveal>
              {epsSpectrum && epsSpectrum.points.length > 0 && (
                <Reveal className="lp-spec-wrap">
                  <SpectrumSketch spectrum={epsSpectrum} label="ε Indi B" />
                  <p className="lp-figcap">
                    <span className="mono">Fig. 2</span> {epsSpectrum.nUsed} of {epsSpectrum.nTotal} real SPHEREx points for
                    ε Indi B. The rest were rejected for a stated reason (flags, saturation, a neighbour star), and the
                    viewer shows each one.
                  </p>
                </Reveal>
              )}
            </section>
          }
        />
      )}

      {/* 4 · Two Opinions */}
      <section className="lp-scene app">
        <Reveal className="lp-scene-text lp-narrow">
          <p className="lp-step mono">03 · Two Opinions</p>
          <h2>Motion says one thing. Colour says another. Do they agree?</h2>
          <p>
            A nearby object moves fast across the sky. Its colour says what it is, and how far away something of that
            type must be. If the two numbers fit together, the motion and the spectrum agree. If not, something is off,
            and Planetes says so.
          </p>
        </Reveal>
        <div className="lp-opinions">
          <Reveal className="lp-op panel">
            <p className="lp-op-k mono">Opinion 1 · motion</p>
            <p className="lp-op-v">{epsOpinions?.motion ?? "Measured from where it sits in each SPHEREx frame"}</p>
            <p className="hint">How far it moves across the sky per year.</p>
          </Reveal>
          <Reveal className="lp-op panel">
            <p className="lp-op-k mono">Opinion 2 · spectrum</p>
            <p className="lp-op-v">{epsOpinions?.spectrum ?? "Type and distance from its measured spectrum"}</p>
            <p className="hint">Type from a fit to standard spectra, distance from how bright that type is.</p>
          </Reveal>
          <Reveal className="lp-op lp-op-verdict panel">
            <p className="lp-op-k mono">Verdict · ε Indi B</p>
            <p className="lp-op-v" data-label={epsOpinions?.label ?? "pending"}>
              {epsOpinions
                ? {
                    agree: "✓ Agree",
                    disagree: "✕ Disagree",
                    cant_tell: "? Can't tell",
                  }[epsOpinions.label]
                : "Coming with the measured motion"}
            </p>
            <p className="hint">
              {epsOpinions?.reasons[0] ?? "The verdict appears here once both opinions are measured for this object."}
            </p>
          </Reveal>
        </div>
      </section>

      {/* 5 · Planet X */}
      <section className="lp-scene lp-scene-split app">
        <Reveal className="lp-scene-text">
          <p className="lp-step mono">04 · Planet X</p>
          <h2>Could SPHEREx see a hidden planet?</h2>
          <p>
            A Planet-Nine-like world, 2.6 times Earth&apos;s size at 700 AU, would shine at about{" "}
            <strong className="mono">AB {p9Best.ab.toFixed(1)}</strong> at its brightest SPHEREx band. One SPHEREx visit
            reaches about <strong className="mono">AB {SPHEREX_SINGLE_VISIT_AB}</strong>. Lower is brighter, so this one
            stays hidden. A bigger or closer planet would not.
          </p>
          <p>
            Between two visits six months apart it would also jump {(p9.shiftArcsec / 60).toFixed(0)}′ across the sky,
            far outside one time-lapse. Try your own planet.
          </p>
          <Link href="/planet-x" className="btn">
            Open the Planet X check
          </Link>
        </Reveal>
        <Reveal className="lp-px-figure">
          <svg viewBox="0 0 320 200" role="img" aria-label="Brightness of a hypothetical planet against SPHEREx depth">
            <line x1="20" y1="60" x2="300" y2="60" className="lp-depth" />
            <text x="300" y="52" textAnchor="end" className="lp-axis">
              SPHEREx one visit · AB {SPHEREX_SINGLE_VISIT_AB}
            </text>
            <circle cx="70" cy="40" r="7" className="lp-planet-near" />
            <text x="70" y="22" textAnchor="middle" className="lp-axis">
              closer: seen
            </text>
            <circle cx="240" cy={60 + (p9Best.ab - SPHEREX_SINGLE_VISIT_AB) * 24} r="5" className="lp-planet-far" />
            <text
              x="240"
              y={60 + (p9Best.ab - SPHEREX_SINGLE_VISIT_AB) * 24 + 22}
              textAnchor="middle"
              className="lp-axis"
            >
              700 AU · AB {p9Best.ab.toFixed(1)}
            </text>
          </svg>
        </Reveal>
      </section>

      {/* 6 · Benchmarks */}
      <section className="lp-scene app">
        <Reveal className="lp-scene-text lp-narrow">
          <p className="lp-step mono">05 · Benchmarks</p>
          <h2>Five objects with known answers.</h2>
          <p>
            Before trusting Planetes on anything new, we test it on objects whose motion and type are already known.
          </p>
        </Reveal>
        <ul className="lp-bench">
          {thumbs.map(({ id, name, t }, k) => (
            <Reveal as="li" key={id} className="lp-bench-card">
              <Link href={`/viewer?target=${id}`} style={{ transitionDelay: `${k * 60}ms` }}>
                <div className="plate lp-mini">
                  {t?.frames[0] && (
                    // eslint-disable-next-line @next/next/no-img-element -- real baked WebP
                    <img src={t.frames[0].src} alt="" width={t.naxis[0]} height={t.naxis[1]} />
                  )}
                </div>
                <strong>{name}</strong>
                <span>{WHY[id]}</span>
              </Link>
            </Reveal>
          ))}
        </ul>
      </section>

      {/* 7 · Honesty */}
      <section className="lp-scene app">
        <Reveal className="lp-honest panel">
          <h2>What SPHEREx can&apos;t tell you here</h2>
          <ul>
            <li>Bright stars saturate its pixels. Saturated points are shown and never used in a verdict.</li>
            <li>One pixel is about 6″, so we don&apos;t claim to measure parallax.</li>
            <li>The data span about a year, so motions from SPHEREx alone have large errors.</li>
          </ul>
          <Link href="/validation" className="btn">
            See every validation test
          </Link>
        </Reveal>
      </section>

      <footer className="lp-foot app">
        <p>
          Data: NASA SPHEREx via NASA/IPAC IRSA · ESA Gaia DR3 · NASA AllWISE · JPL Solar System Dynamics. Planetes is a
          NASA Space Apps 2026 project by Team Planetes; it is not a NASA product.{" "}
          <a href="https://github.com/nova-rishabh/Planetes">Source on GitHub</a>.
        </p>
      </footer>
    </main>
  );
}
