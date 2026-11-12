import { readFileSync } from "node:fs";
import { join } from "node:path";
import type { Metadata } from "next";
import Link from "next/link";
import { parseValidation, plain, stateOf, type ValidationState } from "@/lib/validation";

export const metadata: Metadata = {
  title: "Validation · Planetes",
  description: "How Planetes checks its own measurements against known values, including what has not passed yet.",
};

// Read at build time. A missing file must fail the build, never show an empty or invented table.
const rows = parseValidation(readFileSync(join(process.cwd(), "..", "docs", "VALIDATION.md"), "utf8"));

const LABEL: Record<ValidationState, string> = {
  pass: "Pass",
  fail: "Fail",
  cut: "Cut",
  pending: "Not run yet",
};

export default function Validation() {
  const counts = rows.reduce<Record<ValidationState, number>>(
    (acc, r) => ({ ...acc, [stateOf(r)]: acc[stateOf(r)] + 1 }),
    { pass: 0, fail: 0, cut: 0, pending: 0 },
  );
  return (
    <main className="app about">
      <header className="masthead">
        <div>
          <h1>Validation</h1>
          <p className="tagline">
            Every check we run against a known answer, with the result as it stands. Failures and gaps stay on this
            page.
          </p>
        </div>
        <Link href="/" className="btn">
          Back to the viewer
        </Link>
      </header>

      <p className="mono val-counts">
        {counts.pass} pass · {counts.fail} fail · {counts.pending} not run yet · {counts.cut} cut
      </p>

      <section>
        <ul className="val-list">
          {rows.map((r) => {
            const state = stateOf(r);
            return (
              <li key={r.id} className="panel val-row" data-state={state}>
                <div className="val-head">
                  <span className="mono val-id">{r.id}</span>
                  <h2>{r.test}</h2>
                  <span className="val-badge">{LABEL[state]}</span>
                </div>
                {r.result && !/^(not run yet|cut)$/i.test(r.result) && <p className="val-result">{plain(r.result)}</p>}
                {r.pass && state === "pass" && /\(/.test(r.pass) && <p className="hint">{plain(r.pass)}</p>}
                {r.evidence && <p className="hint">{plain(r.evidence)}</p>}
              </li>
            );
          })}
        </ul>
      </section>

      <section>
        <h2>What SPHEREx can and can&apos;t show here</h2>
        <ul>
          <li>
            Bright stars saturate SPHEREx (roughly brighter than AB magnitude 11.7 at short wavelengths and 9.7 at long
            ones). Barnard&apos;s Star, R Draconis and RW Aurigae are affected: their saturated points are shown but
            never used in a verdict.
          </li>
          <li>
            One SPHEREx pixel is about 6″. Yearly parallax wobbles of these stars are under a tenth of a pixel, so we do
            not claim to measure parallax.
          </li>
          <li>WISE 0855 is almost invisible below 3.5 µm; it is a test of the faint limit, not of the spectrum.</li>
          <li>
            The SPHEREx data so far span about one year, so motions measured from SPHEREx alone have large errors; the
            tests above say when an older catalogue position (Gaia, 2016) was included.
          </li>
        </ul>
        <p className="hint">
          Test definitions: docs/04 §7. Results file:{" "}
          <a href="https://github.com/nova-rishabh/Planetes/blob/main/docs/VALIDATION.md">docs/VALIDATION.md</a>.
        </p>
      </section>
    </main>
  );
}
