import type { SpectrumResult } from "@/types/contracts";
import { chartModel, EPOCH_COLOURS } from "@/lib/spectrum";

const BOX = { width: 560, height: 300, left: 56, right: 12, top: 12, bottom: 52 };

const epochColour = (i: number) => `var(--epoch-${(i % EPOCH_COLOURS) + 1})`;

/**
 * Spectrum of one object (D1.4): flux vs wavelength, one colour per SPHEREx visit, error bars,
 * hollow muted circles for points not used (hover gives the reason). Values come only from the result.
 */
export function SpectrumChart({ result }: { result: SpectrumResult }) {
  const m = chartModel(result.points, BOX);
  const { summary } = result;
  const plotBottom = BOX.height - BOX.bottom;

  return (
    <figure className="panel chart">
      <h2>Spectrum</h2>
      {m.points.length === 0 ? (
        <p className="hint">No measured points yet{m.notMeasured ? ` (${m.notMeasured} not measured)` : ""}.</p>
      ) : (
        <svg viewBox={`0 0 ${BOX.width} ${BOX.height}`} className="chart-svg" role="img" aria-label={`Spectrum with ${m.points.length} points from ${m.epochs} visits`}>
          {m.bands.map((b, i) => (
            <g key={b.label}>
              {i % 2 === 0 ? <rect x={b.x0} y={BOX.top} width={b.x1 - b.x0} height={plotBottom - BOX.top} className="band" /> : null}
              <text x={(b.x0 + b.x1) / 2} y={BOX.height - 6} className="axis-label" textAnchor="middle">{b.label}</text>
            </g>
          ))}
          {m.yTicks.map((t) => (
            <g key={t.value}>
              <line x1={BOX.left} x2={BOX.width - BOX.right} y1={t.y} y2={t.y} className="grid" />
              <text x={BOX.left - 6} y={t.y + 4} className="tick" textAnchor="end">{t.value}</text>
            </g>
          ))}
          {m.zeroY !== null ? <line x1={BOX.left} x2={BOX.width - BOX.right} y1={m.zeroY} y2={m.zeroY} className="zero" /> : null}
          {m.xTicks.map((x, i) => (
            <text key={x} x={x} y={plotBottom + 16} className="tick" textAnchor="middle">{i + 1}</text>
          ))}
          <text x={BOX.width - BOX.right} y={plotBottom + 30} className="axis-label" textAnchor="end">wavelength (µm)</text>
          <text transform={`translate(14 ${(BOX.top + plotBottom) / 2}) rotate(-90)`} className="axis-label" textAnchor="middle">flux (µJy)</text>
          {m.points.map((p) => (
            <g key={p.key} className={p.used ? "pt" : "pt pt-rejected"} style={p.used ? { color: epochColour(p.epoch) } : undefined}>
              <title>{p.label}</title>
              {p.yLo !== null && p.yHi !== null ? <line x1={p.x} x2={p.x} y1={p.yLo} y2={p.yHi} className="err" /> : null}
              {p.halfWidth > 0.5 ? <line x1={p.x - p.halfWidth} x2={p.x + p.halfWidth} y1={p.y} y2={p.y} className="err" /> : null}
              {p.offScale ? (
                <path d={p.y <= BOX.top + 1 ? `M${p.x - 4} ${p.y + 6} L${p.x} ${p.y} L${p.x + 4} ${p.y + 6} Z` : `M${p.x - 4} ${p.y - 6} L${p.x} ${p.y} L${p.x + 4} ${p.y - 6} Z`} />
              ) : (
                <circle cx={p.x} cy={p.y} r={3.5} />
              )}
            </g>
          ))}
        </svg>
      )}
      <figcaption className="hint">
        {summary.n_used} of {summary.n_points} points used · {summary.n_rejected} rejected
        {m.notMeasured ? ` · ${m.notMeasured} not measured` : ""}
        {m.offScale ? ` · ${m.offScale} off scale (▲▼ at the edge)` : ""}
        {m.epochs > 1 ? ` · colours = ${m.epochs} SPHEREx visits` : ""} · {result.provenance.release}, code {result.provenance.code_version}
      </figcaption>
    </figure>
  );
}
