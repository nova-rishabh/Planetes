import { readFileSync } from "node:fs";
import { join } from "node:path";
import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { SiteNav } from "@/components/SiteNav";

export const metadata: Metadata = {
  title: "About · Planetes",
  description: "What SPHEREx is, how to read a Planetes time-lapse, and how the Two Opinions check works.",
};

type BakedFrame = {
  id: string;
  obs_id: string;
  release: string;
  utc: string;
  detector: number;
  wavelength_um: number;
  saturated_near_center: boolean;
};

/** Earliest and latest baked Barnard's Star frames on the same detector (read at build time, real data only). */
function barnardPair(): [BakedFrame, BakedFrame] | null {
  try {
    const path = join(process.cwd(), "public", "data", "targets", "barnard", "timelapse_exposures.json");
    const frames = (JSON.parse(readFileSync(path, "utf8")) as { frames: BakedFrame[] }).frames;
    const sorted = [...frames].sort((a, b) => a.utc.localeCompare(b.utc));
    const first = sorted[0];
    const last = [...sorted].reverse().find((f) => f.detector === first?.detector && f.id !== first.id);
    return first && last ? [first, last] : null;
  } catch {
    return null;
  }
}

function FrameFigure({ frame }: { frame: BakedFrame }) {
  return (
    <figure className="about-fig">
      <div className="plate about-plate">
        <Image
          src={`/data/targets/barnard/frames/${frame.id}.webp`}
          alt={`SPHEREx detector ${frame.detector} cutout around Barnard's Star, ${frame.utc.slice(0, 10)}`}
          width={236}
          height={236}
          className="about-img"
        />
      </div>
      <figcaption className="mono">
        {frame.utc.slice(0, 10)} · D{frame.detector} · {frame.wavelength_um.toFixed(2)} µm · {frame.release}
        <br />
        <span className="about-obs">{frame.obs_id}</span>
      </figcaption>
    </figure>
  );
}

export default function About() {
  const pair = barnardPair();
  return (
    <main className="app about">
      <SiteNav current="/about" />
      <header className="masthead">
        <div>
          <h1>About Planetes</h1>
          <p className="tagline">
            What you are looking at, where it comes from, and what Planetes will and will not claim.
          </p>
        </div>
        <Link href="/viewer" className="btn">
          Back to the viewer
        </Link>
      </header>

      <section>
        <h2>The telescope</h2>
        <p>
          SPHEREx is a NASA space telescope launched in March 2025. Every six months it maps the whole sky in 102
          infrared colours, from 0.75 to 5.0 µm. It has six detectors (D1–D6). Each one covers a slice of that range,
          and the colour changes across each detector, so the same star is seen in a slightly different colour every
          time it is photographed.
        </p>
        <p>
          Because SPHEREx keeps coming back to the same sky, its images form a record of what changed. Planetes plays
          that record back for any position you type in.
        </p>
      </section>

      {pair && (
        <section>
          <h2>Something that moves</h2>
          <div className="about-figs">
            <FrameFigure frame={pair[0]} />
            <FrameFigure frame={pair[1]} />
          </div>
          <p className="hint">
            Fig. 1 · Two real SPHEREx cutouts of Barnard&apos;s Star (6.1′ across, north up), taken{" "}
            {Math.round((Date.parse(pair[1].utc) - Date.parse(pair[0].utc)) / (30.44 * 86400000))} months apart on
            the same detector. Barnard&apos;s Star crosses the sky by about 10″ a year, more than any other star.
            {pair[0].saturated_near_center &&
              " It is so bright that it saturates SPHEREx, so we use it to show motion, not to measure its spectrum."}{" "}
            <Link href="/?target=barnard">Play all frames</Link>.
          </p>
        </section>
      )}

      <section>
        <h2>How to read a time-lapse</h2>
        <ul>
          <li>Each frame is one SPHEREx exposure, cut out around your position and drawn with north up.</li>
          <li>
            All frames share one brightness stretch, so a source that gets brighter or fainter really did change.
          </li>
          <li>
            The label on each frame gives its date, detector and wavelength. Frames on different detectors show
            different colours of light, so compare like with like.
          </li>
          <li>
            <strong>Blink</strong> flips between two frames. Something that shifts while everything else stays put is
            moving across the sky.
          </li>
          <li>
            <strong>Flags</strong> marks pixels SPHEREx itself warns about: cosmic-ray hits, saturation, bad pixels.
            A change that sits on flagged pixels is not trusted.
          </li>
        </ul>
      </section>

      <section>
        <h2>Two Opinions</h2>
        <p>
          A change on its own is not enough: glitches, bright-star ghosts and stars that vary in brightness all look
          like changes. So for an object, Planetes forms two opinions that do not depend on each other.
        </p>
        <dl className="about-dl">
          <dt>Motion</dt>
          <dd>How fast and in which direction the object moves across the frames.</dd>
          <dt>Spectrum</dt>
          <dd>
            What its light across the SPHEREx colours says it is. A star&apos;s type tells us how bright it really is,
            which gives a distance. For an asteroid, the ratio of heat glow (4–5 µm) to reflected sunlight (1.6–2.4 µm)
            gives a temperature, which gives its distance from the Sun.
          </dd>
        </dl>
        <p>
          Then Planetes checks whether the two fit together. A star that moves 1″ a year at 10 parsecs is travelling
          about 47 km/s, a normal speed for a star near the Sun. If the numbers only work for an impossible speed,
          the opinions disagree, and Planetes says so.
        </p>
        <p>
          Opinions appear for a target once both measurements are ready. The verdict always shows the measurements, their
          uncertainty and where any comparison value comes from.
        </p>
      </section>

      <section>
        <h2>The five test targets</h2>
        <dl className="about-dl">
          <dt>Barnard&apos;s Star</dt>
          <dd>A red dwarf 1.8 parsecs away and the fastest-moving star in our sky. The motion example.</dd>
          <dt>ε Indi B</dt>
          <dd>A pair of brown dwarfs, too close together for SPHEREx to split. Moves and has a clear spectrum.</dd>
          <dt>WISE 0855−0714</dt>
          <dd>The coldest known brown dwarf, about 250 K. Nearly invisible below 3.5 µm; look at D5 and D6.</dd>
          <dt>RW Aurigae</dt>
          <dd>A young star with a dusty disk. It does not move, but its brightness changes.</dd>
          <dt>R Draconis</dt>
          <dd>A pulsating red giant whose brightness rises and falls over about 245 days. Often saturated.</dd>
        </dl>
      </section>

      <section>
        <h2>What we will and will not claim</h2>
        <ul>
          <li>Every image and number comes from public NASA data. Nothing is simulated or filled in.</li>
          <li>
            We say an object is &ldquo;consistent with&rdquo; something, never that we discovered or confirmed it.
            Anything unexplained is a candidate that needs follow-up by astronomers.
          </li>
          <li>Saturated data is labelled and never used in a verdict.</li>
          <li>
            Nearby stars also wobble yearly as the Earth orbits the Sun (parallax), but for these targets the wobble is
            under a tenth of a SPHEREx pixel, so we do not claim to measure it.
          </li>
        </ul>
      </section>

      <section>
        <h2>Data and credits</h2>
        <p>
          SPHEREx images: NASA/JPL-Caltech, served by IRSA (NASA/IPAC Infrared Science Archive), Quick Release 2 and 3.
          Star positions and motions: ESA Gaia DR3 (via IRSA) and SIMBAD (CDS, Strasbourg). Sky map: Aladin Lite (CDS)
          with images from ESA ESASky. Pipeline built on Astropy and astroquery. Full list in{" "}
          <a href="https://github.com/nova-rishabh/Planetes/blob/main/docs/REFERENCES.md">docs/REFERENCES.md</a>.
        </p>
        <p className="hint">
          Planetes is a NASA Space Apps 2026 project by Team Planetes for the &ldquo;Planet X and SPHEREx&rdquo;
          challenge. It is not an official NASA product.
        </p>
      </section>
    </main>
  );
}
