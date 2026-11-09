import type { Opinions } from "@/types/contracts";
import { motionLines, spectrumLines, verdictView } from "@/lib/opinions";

/** Two Opinions (D1.5): what the motion says, what the spectrum says, and whether they agree. */
export function OpinionsPanel({ opinions }: { opinions: Opinions }) {
  const motion = motionLines(opinions.motion);
  const spectrum = spectrumLines(opinions.spectrum);
  const verdict = verdictView(opinions.verdict);

  return (
    <section className="panel opinions" aria-label="Two Opinions">
      <h2>Two Opinions</h2>
      <div className="opinion-grid">
        <div className="opinion">
          <h3>1 · Motion</h3>
          <p className="opinion-head">{motion.headline}</p>
          <ul>{motion.details.map((d) => <li key={d}>{d}</li>)}</ul>
        </div>
        <div className="opinion">
          <h3>2 · Spectrum</h3>
          <p className="opinion-head">{spectrum.headline}</p>
          <ul>{spectrum.details.map((d) => <li key={d}>{d}</li>)}</ul>
        </div>
      </div>
      <div className="verdict" data-tone={verdict.tone} role="status">
        <span className="verdict-symbol" aria-hidden="true">{verdict.symbol}</span>
        <div>
          <p className="opinion-head">{verdict.headline}</p>
          {verdict.reasons.length ? <ul>{verdict.reasons.map((r) => <li key={r}>{r}</li>)}</ul> : null}
        </div>
      </div>
    </section>
  );
}
