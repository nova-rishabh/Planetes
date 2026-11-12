import type { Metadata } from "next";
import Link from "next/link";
import { PlanetXCalculator } from "@/components/PlanetXCalculator";

export const metadata: Metadata = {
  title: "Planet X reality check · Planetes",
  description: "Could SPHEREx see a hypothetical distant planet? A what-if calculator with the physics shown.",
};

export default function PlanetX() {
  return (
    <main className="app about px-page">
      <header className="masthead">
        <div>
          <h1>Planet X reality check</h1>
          <p className="tagline">
            Pick a size and a distance for a hypothetical planet far beyond Neptune, and see whether SPHEREx could pick
            it up. These are what-if numbers, not observations.
          </p>
        </div>
        <Link href="/" className="btn">
          Back to the viewer
        </Link>
      </header>

      <PlanetXCalculator />

      <section>
        <h2>What this shows</h2>
        <ul>
          <li>
            <strong>Sunlight it reflects.</strong> Scaled from Neptune (V 7.8 at 29 AU): twice as far is 16 times
            fainter, because sunlight has to travel out and the reflection back.
          </li>
          <li>
            <strong>Its own heat.</strong> Some models give a cold planet extra glow at 3–5 µm, but the range is huge,
            so treat this slider as model-dependent.
          </li>
          <li>
            <strong>SPHEREx depth.</strong> One visit reaches about AB 18.5 at short wavelengths. Adding visits only
            helps if the object stays put, and a distant planet does not: it jumps by arcminutes between visits six
            months apart, as Earth swings around the Sun.
          </li>
          <li>
            <strong>Simplifications.</strong> The albedo is the same at every wavelength. Real giant planets are darker
            in parts of the infrared (methane absorbs there), so the infrared numbers are optimistic.
          </li>
        </ul>
        <p>
          <strong>Honest bottom line:</strong> published estimates put the proposed Planet Nine around V 21–25, below
          what one SPHEREx visit reaches. SPHEREx is not expected to detect it. It can test brighter or closer
          hypothetical planets in the fields it covers.
        </p>
        <p className="hint">
          Physics: docs/04 §6 and <span className="mono">pipeline/src/planetes/planet_x.py</span>.
        </p>
      </section>
    </main>
  );
}
