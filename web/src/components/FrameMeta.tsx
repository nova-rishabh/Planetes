import type { FlagLegendItem, Frame } from "@/types/contracts";

const dash = "—";

function fmt(v: number | null, digits: number, unit = ""): string {
  return v === null ? dash : `${v.toFixed(digits)}${unit}`;
}

/** Metadata of the frame on screen, and the flag legend read from the real FITS headers. */
export function FrameMeta({ frame, legend, showLegend }: { frame: Frame; legend: FlagLegendItem[]; showLegend: boolean }) {
  const rows: [string, string][] = [
    ["Date (UTC)", frame.utc ?? dash],
    ["MJD", fmt(frame.mjd, 5)],
    ["Detector", frame.detector === null ? dash : `D${frame.detector}`],
    [
      "Wavelength",
      frame.wavelength_um === null
        ? dash
        : `${frame.wavelength_um.toFixed(3)} µm${frame.bandwidth_um !== null ? ` ± ${(frame.bandwidth_um / 2).toFixed(3)}` : ""}`,
    ],
    ["Release", frame.release],
    ["Epoch", frame.epoch_index === null ? dash : String(frame.epoch_index)],
    ["Flagged pixels", frame.flagged_frac === null ? dash : `${(frame.flagged_frac * 100).toFixed(1)} %`],
    ["Saturated near centre", frame.saturated_near_center === null ? dash : frame.saturated_near_center ? "yes" : "no"],
  ];
  const sources = frame.obs_id ? [frame.obs_id] : frame.members;

  return (
    <aside className="panel meta" aria-label="Frame details">
      <h2>This frame</h2>
      <dl>
        {rows.map(([k, v]) => (
          <div key={k} className="meta-row">
            <dt>{k}</dt>
            <dd className="mono">{v}</dd>
          </div>
        ))}
      </dl>
      <h3>Source {sources.length > 1 ? `exposures (${sources.length})` : "exposure"}</h3>
      <ul className="mono obs-list">
        {sources.slice(0, 6).map((id) => (
          <li key={id}>{id}</li>
        ))}
        {sources.length > 6 ? <li>… and {sources.length - 6} more</li> : null}
      </ul>
      {frame.notes.length ? (
        <ul className="notes">
          {frame.notes.map((n) => (
            <li key={n}>{n}</li>
          ))}
        </ul>
      ) : null}
      {showLegend ? (
        <>
          <h3>Flag legend</h3>
          {legend.length ? (
            <ul className="legend">
              {legend.map((l) => (
                <li key={l.bit}>
                  <span className="mono">bit {l.bit} {l.name}</span>
                  {l.plain ? ` · ${l.plain}` : ""}
                </li>
              ))}
            </ul>
          ) : (
            <p className="hint">No flag meanings were read for this time-lapse.</p>
          )}
        </>
      ) : null}
    </aside>
  );
}
