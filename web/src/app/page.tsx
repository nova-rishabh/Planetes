import Link from "next/link";
import { SiteNav } from "@/components/SiteNav";
import { Colour3D } from "@/components/landing/Colour3D";
import { StarFieldFigure } from "@/components/landing/Figures3D";
import { LegacyLinkRedirect } from "@/components/landing/LegacyLinkRedirect";
import { PlanetX3D } from "@/components/landing/PlanetX3D";
import { PlateFan, PlateStack } from "@/components/landing/PlateStack";
import { Reveal } from "@/components/landing/Reveal";
import { ScrambleText } from "@/components/landing/ScrambleText";
import { SpectrumSketch } from "@/components/landing/SpectrumSketch";
import { BENCHMARKS } from "@/lib/benchmarks";
import {
  acrossDetectors,
  blinkPair,
  fmtDate,
  loadOpinions,
  loadSpectrum,
  loadStarField,
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
const blinkDays = blink ? Math.round((Date.parse(blink.b.utc) - Date.parse(blink.a.utc)) / 86400000) : null;
const eps = loadTarget("epsindib");
const epsColours = eps ? acrossDetectors(eps) : [];
const epsSpectrum = loadSpectrum("epsindib");
const epsOpinions = loadOpinions("epsindib");
const barnardField = loadStarField("barnard");
const thumbs = BENCHMARKS.map((b) => ({ ...b, t: loadTarget(b.id) }));
const p9 = evaluate(2.6 * EARTH_RADIUS_KM, 0.5, 700, 40, 1);
const p9Best = p9.bands.reduce((a, b) => (b.ab < a.ab ? b : a));
const firstDate = barnardRun[0] ? fmtDate(barnardRun[0].utc) : null;
const lastDate = barnardRun.length ? fmtDate(barnardRun[barnardRun.length - 1]!.utc) : null;

function Head({ n, title, children }: { n: string; title: React.ReactNode; children?: React.ReactNode }) {
  return (
    <header className="ed-head">
      <p className="ed-num mono">{n}</p>
      <h2 className="ed-h2">{title}</h2>
      {children}
    </header>
  );
}

export default function Home() {
  return (
    <main className="landing ed">
      <LegacyLinkRedirect />
      <div className="ed-wrap">
        <SiteNav current="/" />
        <p className="ed-meta mono">
          <span>NASA SPACE APPS 2026 · PLANET X AND SPHEREX</span>
          <span>
            <ScrambleText text="SPHEREX · 0.75–5 µm · EVERY VISIT SINCE AUG 2025" />
          </span>
        </p>
      </div>

      {/* 1 · Hero */}
      <section className="ed-hero ed-wrap">
        <div className="ed-hero-text">
          <h1 className="ed-h1">
            <span>Watch the</span>
            <span>infrared</span>
            <span className="ed-hot">sky move.</span>
          </h1>
          <div className="ed-strip" aria-hidden="true" />
          <p className="ed-lede">
            Planetes pulls every SPHEREx picture of one patch of sky and plays them as a time-lapse. Things that move
            jump between frames. Then it reads their colour, and asks whether the two stories agree.
          </p>
          <form className="ed-go" action="/viewer" method="get">
            <label className="field">
              <span className="mono">RA (°)</span>
              <input name="ra" inputMode="decimal" className="mono" placeholder="269.4485" required pattern="[0-9.]+" />
            </label>
            <label className="field">
              <span className="mono">Dec (°)</span>
              <input name="dec" inputMode="decimal" className="mono" placeholder="4.7394" required pattern="-?[0-9.]+" />
            </label>
            <button type="submit" className="ed-btn ed-btn-ink mono">
              Open time-lapse →
            </button>
          </form>
          <p className="ed-or mono">
            Or a benchmark: <Link href="/viewer?target=barnard">Barnard&apos;s Star</Link> ·{" "}
            <Link href="/viewer?target=epsindib">ε Indi B</Link> · <Link href="/viewer?target=wise0855">WISE 0855</Link>
          </p>
        </div>
        {barnard && barnardRun.length > 1 && (
          <div className="ed-hero-fig">
            <PlateStack frames={barnardRun} naxis={barnard.naxis} label="Barnard's Star" />
            <div className="ed-callout">
              {blink?.movedArcsec != null && blinkDays !== null && (
                <p className="ed-callout-big">
                  {blink.movedArcsec.toFixed(1)}″ in {blinkDays} days
                </p>
              )}
              <p className="mono">
                Fig. 1 — Barnard&apos;s Star, SPHEREx D{barnardRun[0]!.detector}
                {barnardRun[0]!.wavelength_um ? ` · ${barnardRun[0]!.wavelength_um.toFixed(2)} µm` : ""}.{" "}
                {barnardRun.length} real visits, {firstDate} to {lastDate}. Orange ring: measured position.
              </p>
            </div>
          </div>
        )}
      </section>

      {/* 2 · Blink: a flip-book through every visit */}
      {barnard && barnardRun.length > 1 && (
        <section className="ed-blink">
          <div className="ed-wrap ed-blink-grid">
            <div className="ed-blink-text">
              <Head n="01 — Blink" title="The oldest trick for finding things that move." />
              <p>
                In 1930 Clyde Tombaugh found Pluto by flipping between two photographs of the same stars, days apart.
                Everything fixed stays still. Anything that moved jumps.
              </p>
              <p>
                Scroll to flip through all {barnardRun.length} SPHEREx visits of Barnard&apos;s Star. The cross marks
                where it sat on the first plate; the orange ring is where it is now.
                {blink?.movedArcsec != null && (
                  <>
                    {" "}
                    Over {blinkDays} days it moves <strong className="ed-hot">{blink.movedArcsec.toFixed(1)}″</strong>,
                    about {(blink.movedArcsec / barnard.cdeltArcsec).toFixed(1)} pixels.
                  </>
                )}
              </p>
            </div>
          </div>
          <PlateFan frames={barnardRun} naxis={barnard.naxis} />
        </section>
      )}

      {/* 3 · Colour: detectors to spectrum */}
      {eps && epsColours.length > 0 && (
        <Colour3D
          tiles={epsColours.map((f) => ({ src: f.src, detector: f.detector, wavelength_um: f.wavelength_um }))}
          points={epsSpectrum?.points.map((p) => ({ um: p.um, ujy: p.ujy, det: p.det })) ?? []}
          nUsed={epsSpectrum?.nUsed ?? 0}
          nTotal={epsSpectrum?.nTotal ?? 0}
          spectrumLine={epsOpinions?.spectrum ?? null}
          flat={
            <section className="ed-sec ed-wrap">
              <Head n="02 — Colour" title="Six detectors, one spectrum." />
              <ol className="ed-dets">
                {epsColours.map((f) => (
                  <li key={f.src}>
                    {/* eslint-disable-next-line @next/next/no-img-element -- real baked WebP */}
                    <img src={f.src} alt={`ε Indi B on detector D${f.detector}`} width={eps.naxis[0]} height={eps.naxis[1]} />
                    <span className="mono">
                      D{f.detector} · {f.wavelength_um?.toFixed(2)} µm
                    </span>
                  </li>
                ))}
              </ol>
              {epsSpectrum && epsSpectrum.points.length > 0 && <SpectrumSketch spectrum={epsSpectrum} label="ε Indi B" />}
            </section>
          }
        />
      )}

      {/* 4 · Two Opinions */}
      <section className="ed-sec ed-wrap">
        <Head n="03 — Two Opinions" title="Motion says one thing. Colour says another.">
          <p className="ed-sub">
            A nearby object moves fast across the sky. Its colour says what it is, and how far away that kind of object
            must be. If the two fit, they agree. If not, Planetes says so.
          </p>
        </Head>
        <div className="ed-ops">
          <Reveal className="ed-op">
            <p className="ed-op-k mono">Opinion 1 · Motion</p>
            <p className="ed-op-v">{epsOpinions?.motion ?? "Not measured yet"}</p>
            <p className="ed-op-h">How far ε Indi B moves across the sky per year, from where it sits in each frame.</p>
          </Reveal>
          <Reveal className="ed-op">
            <p className="ed-op-k mono">Opinion 2 · Spectrum</p>
            <p className="ed-op-v">{epsOpinions?.spectrum ?? "Not measured yet"}</p>
            <p className="ed-op-h">Type from a fit to standard spectra; distance from how bright that type is.</p>
          </Reveal>
          <Reveal className="ed-op ed-op-verdict">
            <p className="ed-op-k mono">Verdict · ε Indi B</p>
            <p className="ed-stamp" data-label={epsOpinions?.label ?? "pending"}>
              {epsOpinions
                ? { agree: "Agree", disagree: "Disagree", cant_tell: "Can't tell yet" }[epsOpinions.label]
                : "Pending"}
            </p>
            <p className="ed-op-h">
              {epsOpinions?.reasons[0] ?? "The verdict appears once both opinions are measured for this object."}
            </p>
          </Reveal>
        </div>
      </section>

      {/* 5 · Planet X */}
      <PlanetX3D
        flatFigure={
          <p className="ed-op-h">
            A Planet-Nine-like world at 700 AU peaks at AB {p9Best.ab.toFixed(1)}; one SPHEREx visit reaches AB{" "}
            {SPHEREX_SINGLE_VISIT_AB}.
          </p>
        }
      />

      {/* 6 · Benchmarks */}
      <section className="ed-sec ed-wrap">
        <Head n="05 — Benchmarks" title="Five objects with known answers.">
          <p className="ed-sub">
            Before trusting Planetes on anything new, we test it on objects whose motion and type are already known.
          </p>
        </Head>
        <ul className="ed-bench">
          {thumbs.map(({ id, name, t }, k) => (
            <li key={id}>
              <Link href={`/viewer?target=${id}`} className="ed-card">
                <span className="ed-card-n mono">{String(k + 1).padStart(2, "0")}</span>
                <span className="ed-card-img">
                  {t?.frames[0] && (
                    // eslint-disable-next-line @next/next/no-img-element -- real baked WebP
                    <img src={t.frames[0].src} alt="" width={t.naxis[0]} height={t.naxis[1]} />
                  )}
                </span>
                <strong>{name}</strong>
                <span className="ed-card-why">{WHY[id]}</span>
                <span className="ed-card-go mono">Open →</span>
              </Link>
            </li>
          ))}
        </ul>
      </section>

      {/* 7 · Honesty */}
      <section className="ed-sec ed-wrap">
        <Head n="06 — Limits" title="What SPHEREx can't tell you here." />
        <ol className="ed-limits">
          <li>
            <strong>Bright stars saturate.</strong> Saturated points are shown, and never used in a verdict.
          </li>
          <li>
            <strong>One pixel is about 6″.</strong> So we don&apos;t claim to measure parallax.
          </li>
          <li>
            <strong>About a year of data.</strong> Motions from SPHEREx alone have large errors.
          </li>
        </ol>
        <Link href="/validation" className="ed-btn mono">
          See every validation test →
        </Link>
      </section>

      {/* 8 · Footer */}
      <footer className="ed-foot">
        {barnardField && (
          <div className="ed-wrap ed-foot-fig">
            <StarFieldFigure field={barnardField} />
            <p className="mono">
              Fig. 3 — The {barnardField.stars.length} Gaia DR3 stars within {barnardField.radiusArcmin.toFixed(0)}′ of
              Barnard&apos;s Star. The orange mark is Barnard&apos;s Star itself, walking its measured path.
            </p>
          </div>
        )}
        <p className="ed-word" aria-hidden="true">
          Planetes
        </p>
        <div className="ed-wrap ed-foot-meta mono">
          <span>
            Data: NASA SPHEREx via NASA/IPAC IRSA · ESA Gaia DR3 · NASA AllWISE · JPL Solar System Dynamics.
          </span>
          <span>
            NASA Space Apps 2026 project by Team Planetes; not a NASA product.{" "}
            <a href="https://github.com/nova-rishabh/Planetes">Source on GitHub</a>
          </span>
        </div>
      </footer>
    </main>
  );
}
