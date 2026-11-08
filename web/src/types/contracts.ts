/* GENERATED, DO NOT EDIT. Source: contracts/*.schema.json. Regenerate with `make contracts`. */

/**
 * Declination, ICRS, degrees.
 *
 * This interface was referenced by `PlanetesContracts`'s JSON-Schema
 * via the `definition` "DecDeg".
 */
export type DecDeg = number;
/**
 * SPHEREx detector number (D1-D6).
 *
 * This interface was referenced by `PlanetesContracts`'s JSON-Schema
 * via the `definition` "Detector".
 */
export type Detector = number;
/**
 * Contract version (docs/03 §1).
 *
 * This interface was referenced by `PlanetesContracts`'s JSON-Schema
 * via the `definition` "SchemaVersion".
 */
export type SchemaVersion = "1.0";
/**
 * SPHEREx Quick Release a measurement came from.
 *
 * This interface was referenced by `PlanetesContracts`'s JSON-Schema
 * via the `definition` "Release".
 */
export type Release = "QR2" | "QR3";
/**
 * This interface was referenced by `PlanetesContracts`'s JSON-Schema
 * via the `definition` "JobId".
 */
export type JobId = string;
/**
 * Right ascension, ICRS, degrees.
 *
 * This interface was referenced by `PlanetesContracts`'s JSON-Schema
 * via the `definition` "RaDeg".
 */
export type RaDeg = number;
/**
 * This interface was referenced by `PlanetesContracts`'s JSON-Schema
 * via the `definition` "Quality".
 */
export type Quality = "good" | "fair" | "poor";
/**
 * Release to query. auto = QR3, then fall back to QR2.
 *
 * This interface was referenced by `PlanetesContracts`'s JSON-Schema
 * via the `definition` "RequestedRelease".
 */
export type RequestedRelease = "auto" | "QR3" | "QR2";

export interface PlanetesContracts {
  [k: string]: unknown;
}
/**
 * Distance range. null = not measured.
 *
 * This interface was referenced by `PlanetesContracts`'s JSON-Schema
 * via the `definition` "Distance".
 */
export interface Distance {
  lo: number | null;
  hi: number | null;
  unit: "pc" | "au" | null;
}
/**
 * This interface was referenced by `PlanetesContracts`'s JSON-Schema
 * via the `definition` "Epoch".
 */
export interface Epoch {
  index: number;
  mjd_start: number;
  mjd_end: number;
  n_frames: number;
}
/**
 * Body of every HTTP 4xx/5xx response (docs/03 §3).
 *
 * This interface was referenced by `PlanetesContracts`'s JSON-Schema
 * via the `definition` "Error".
 */
export interface Error {
  schema_version: SchemaVersion;
  error: ErrorBody;
}
/**
 * This interface was referenced by `PlanetesContracts`'s JSON-Schema
 * via the `definition` "ErrorBody".
 */
export interface ErrorBody {
  code: "BAD_INPUT" | "NOT_FOUND" | "NO_COVERAGE" | "IRSA_TIMEOUT" | "IRSA_ERROR" | "TOO_LARGE" | "INTERNAL";
  message: string;
  hint: string | null;
}
/**
 * One FLAGS bit, as read from the header MP_* keys.
 *
 * This interface was referenced by `PlanetesContracts`'s JSON-Schema
 * via the `definition` "FlagLegendItem".
 */
export interface FlagLegendItem {
  bit: number;
  name: string;
  /**
   * Plain-language meaning.
   */
  plain: string | null;
}
/**
 * This interface was referenced by `PlanetesContracts`'s JSON-Schema
 * via the `definition` "Frame".
 */
export interface Frame {
  /**
   * f_ + first 12 hex of sha1(obs_id + cutout params).
   */
  id: string;
  kind: "exposure" | "stack" | "difference" | "sum" | "color";
  /**
   * IVOA publisher DID; null for combined frames (see members).
   */
  obs_id: string | null;
  /**
   * obs_ids combined into this frame.
   */
  members: string[];
  release: Release;
  epoch_index: number | null;
  mjd: number | null;
  utc: string | null;
  detector: Detector | null;
  wavelength_um: number | null;
  bandwidth_um: number | null;
  image_url: string;
  flags_url: string | null;
  flagged_frac: number | null;
  saturated_near_center: boolean | null;
  /**
   * Where the (propagated) target falls on the grid, pixels.
   */
  target_xy: [number, number] | null;
  notes: string[];
}
/**
 * Common north-up output grid every frame is reprojected onto.
 *
 * This interface was referenced by `PlanetesContracts`'s JSON-Schema
 * via the `definition` "Grid".
 */
export interface Grid {
  projection: "TAN";
  /**
   * @minItems 2
   * @maxItems 2
   */
  crval_deg: [number, number];
  /**
   * Reference pixel, FITS 1-based convention.
   *
   * @minItems 2
   * @maxItems 2
   */
  crpix: [number, number];
  cdelt_deg: number;
  /**
   * @minItems 2
   * @maxItems 2
   */
  naxis: [number, number];
  north_up: boolean;
}
/**
 * GET /api/health: liveness and upstream check (docs/03 §5).
 *
 * This interface was referenced by `PlanetesContracts`'s JSON-Schema
 * via the `definition` "Health".
 */
export interface Health {
  schema_version: SchemaVersion;
  /**
   * The API process is up.
   */
  status: "ok";
  /**
   * Git short hash of the running code, or "dev".
   */
  code_version: string;
  /**
   * Result of a live request to the IRSA TAP service.
   */
  irsa_tap: "ok" | "slow" | "down";
  default_release: Release;
  cache_entries: number;
}
/**
 * GET /api/jobs/{job_id}: status and (partial) result (docs/03 §5).
 *
 * This interface was referenced by `PlanetesContracts`'s JSON-Schema
 * via the `definition` "Job".
 */
export interface Job {
  schema_version: SchemaVersion;
  job_id: JobId;
  kind: "timelapse" | "spectrum";
  status: "queued" | "running" | "done" | "error";
  progress: JobProgress;
  /**
   * TimelapseResult or SpectrumResult; partial while running, null before any output.
   */
  result: TimelapseResult | SpectrumResult | null;
  error: ErrorBody | null;
}
/**
 * This interface was referenced by `PlanetesContracts`'s JSON-Schema
 * via the `definition` "JobProgress".
 */
export interface JobProgress {
  done: number;
  /**
   * null while the total is not yet known.
   */
  total: number | null;
  stage: string | null;
}
/**
 * Result of a time-lapse job, also baked as data/targets/{id}/timelapse_{mode}.json (docs/03 §5-§6).
 *
 * This interface was referenced by `PlanetesContracts`'s JSON-Schema
 * via the `definition` "TimelapseResult".
 */
export interface TimelapseResult {
  schema_version: SchemaVersion;
  request: TimelapseRequest;
  grid: Grid;
  epochs: Epoch[];
  frames: Frame[];
  /**
   * Shared display stretch; null until computed.
   */
  stretch: Stretch | null;
  flag_legend: FlagLegendItem[];
  provenance: Provenance;
}
/**
 * Body of POST /api/timelapse (docs/03 §4). Echoed in TimelapseResult.request.
 *
 * This interface was referenced by `PlanetesContracts`'s JSON-Schema
 * via the `definition` "TimelapseRequest".
 */
export interface TimelapseRequest {
  schema_version?: SchemaVersion;
  ra: RaDeg;
  dec: DecDeg;
  fov_deg?: number;
  mode?: "exposures" | "stacks" | "difference" | "sum" | "color";
  /**
   * @minItems 1
   * @maxItems 6
   */
  detectors?:
    | [Detector]
    | [Detector, Detector]
    | [Detector, Detector, Detector]
    | [Detector, Detector, Detector, Detector]
    | [Detector, Detector, Detector, Detector, Detector]
    | [Detector, Detector, Detector, Detector, Detector, Detector];
  /**
   * Release to query. auto = QR3, then fall back to QR2.
   */
  release?: "auto" | "QR3" | "QR2";
  mjd_start?: number | null;
  mjd_end?: number | null;
  max_frames?: number;
  pm?: ProperMotion | null;
}
/**
 * Proper motion and its reference epoch, as returned by /resolve.
 *
 * This interface was referenced by `PlanetesContracts`'s JSON-Schema
 * via the `definition` "ProperMotion".
 */
export interface ProperMotion {
  /**
   * Proper motion in RA, mas/yr.
   */
  pm_ra_masyr: number;
  /**
   * Proper motion in Dec, mas/yr.
   */
  pm_dec_masyr: number;
  /**
   * Reference epoch, Julian year (Gaia DR3 = 2016.0).
   */
  ref_epoch_jyear: number;
}
/**
 * This interface was referenced by `PlanetesContracts`'s JSON-Schema
 * via the `definition` "Stretch".
 */
export interface Stretch {
  method: "linear" | "asinh" | "log";
  lo: number;
  hi: number;
  /**
   * Unit of lo/hi, e.g. MJy/sr.
   */
  unit: string;
}
/**
 * This interface was referenced by `PlanetesContracts`'s JSON-Schema
 * via the `definition` "Provenance".
 */
export interface Provenance {
  tap_query: string | null;
  generated_utc: string;
  code_version: string;
}
/**
 * Result of a spectrum job, also baked as data/targets/{id}/spectrum.json (docs/03 §5-§6).
 *
 * This interface was referenced by `PlanetesContracts`'s JSON-Schema
 * via the `definition` "SpectrumResult".
 */
export interface SpectrumResult {
  schema_version: SchemaVersion;
  target: SpectrumTarget;
  points: SpectrumPoint[];
  summary: SpectrumSummary;
  provenance: SpectrumProvenance;
}
/**
 * This interface was referenced by `PlanetesContracts`'s JSON-Schema
 * via the `definition` "SpectrumTarget".
 */
export interface SpectrumTarget {
  ra: RaDeg;
  dec: DecDeg;
  pm: ProperMotion | null;
}
/**
 * This interface was referenced by `PlanetesContracts`'s JSON-Schema
 * via the `definition` "SpectrumPoint".
 */
export interface SpectrumPoint {
  obs_id: string;
  mjd: number;
  detector: Detector;
  wavelength_um: number | null;
  bandwidth_um: number | null;
  /**
   * null until measured.
   */
  flux_ujy: number | null;
  flux_err_ujy: number | null;
  snr: number | null;
  /**
   * Raw FLAGS bitmask at the source position.
   */
  flags: number;
  saturated: boolean;
  used: boolean;
  reject_reason: string | null;
  /**
   * Simultaneous detector pair (D1&D4, D2&D5, D3&D6).
   */
  pair_id: string | null;
  method: "psf" | "aperture" | null;
  ra: RaDeg;
  dec: DecDeg;
}
/**
 * This interface was referenced by `PlanetesContracts`'s JSON-Schema
 * via the `definition` "SpectrumSummary".
 */
export interface SpectrumSummary {
  n_points: number;
  n_used: number;
  n_rejected: number;
  bands_covered: Detector[];
}
/**
 * This interface was referenced by `PlanetesContracts`'s JSON-Schema
 * via the `definition` "SpectrumProvenance".
 */
export interface SpectrumProvenance {
  release: Release;
  code_version: string;
}
/**
 * Response of POST /api/timelapse and POST /api/spectrum (docs/03 §3).
 *
 * This interface was referenced by `PlanetesContracts`'s JSON-Schema
 * via the `definition` "JobCreated".
 */
export interface JobCreated {
  schema_version: SchemaVersion;
  job_id: JobId;
}
/**
 * This interface was referenced by `PlanetesContracts`'s JSON-Schema
 * via the `definition` "MotionOpinion".
 */
export interface MotionOpinion {
  kind: "proper_motion" | "sso_rate" | "static" | "unknown";
  value: number | null;
  unit: "arcsec/yr" | "arcsec/hr" | null;
  /**
   * Uncertainty of value, same unit.
   */
  err: number | null;
  pa_deg: number | null;
  distance: Distance;
  truth: MotionTruth;
  quality: Quality;
  method: string;
}
/**
 * This interface was referenced by `PlanetesContracts`'s JSON-Schema
 * via the `definition` "MotionTruth".
 */
export interface MotionTruth {
  value: number | null;
  source: string | null;
}
/**
 * This interface was referenced by `PlanetesContracts`'s JSON-Schema
 * via the `definition` "OpinionObject".
 */
export interface OpinionObject {
  ra: RaDeg;
  dec: DecDeg;
}
/**
 * POST /api/opinions: Two Opinions (motion vs spectrum) for one object (docs/03 §5).
 *
 * This interface was referenced by `PlanetesContracts`'s JSON-Schema
 * via the `definition` "Opinions".
 */
export interface Opinions {
  schema_version: SchemaVersion;
  object: OpinionObject;
  motion: MotionOpinion;
  spectrum: SpectrumOpinion;
  verdict: Verdict;
}
/**
 * This interface was referenced by `PlanetesContracts`'s JSON-Schema
 * via the `definition` "SpectrumOpinion".
 */
export interface SpectrumOpinion {
  kind: "template" | "thermal" | "none";
  class: string | null;
  temperature_k: number | null;
  distance: Distance;
  quality: Quality;
  method: string;
}
/**
 * This interface was referenced by `PlanetesContracts`'s JSON-Schema
 * via the `definition` "Verdict".
 */
export interface Verdict {
  label: "agree" | "disagree" | "cant_tell";
  class: "nearby_star" | "brown_dwarf" | "asteroid" | "variable" | "artifact" | "unknown";
  confidence: number | null;
  reasons: string[];
}
/**
 * Body of POST /api/opinions (docs/03 §4).
 *
 * This interface was referenced by `PlanetesContracts`'s JSON-Schema
 * via the `definition` "OpinionsRequest".
 */
export interface OpinionsRequest {
  schema_version?: SchemaVersion;
  ra: RaDeg;
  dec: DecDeg;
  spectrum_job_id?: JobId | null;
  pm?: ProperMotion | null;
}
/**
 * This interface was referenced by `PlanetesContracts`'s JSON-Schema
 * via the `definition` "OverlayCatalog".
 */
export interface OverlayCatalog {
  name: string;
  /**
   * VizieR catalogue ID.
   */
  vizier: string | null;
  ref_epoch_jyear: number | null;
  sources: OverlaySource[];
}
/**
 * This interface was referenced by `PlanetesContracts`'s JSON-Schema
 * via the `definition` "OverlaySource".
 */
export interface OverlaySource {
  id: string;
  ra: RaDeg;
  dec: DecDeg;
  pm_ra_masyr: number | null;
  pm_dec_masyr: number | null;
  mag: number | null;
  band: string | null;
  /**
   * Position [ra_deg, dec_deg] keyed by MJD (as a string).
   */
  at_mjd: {
    /**
     * @minItems 2
     * @maxItems 2
     */
    [k: string]: [number, number];
  };
}
/**
 * GET /api/overlays: catalog sources moved to each frame date (docs/03 §5).
 *
 * This interface was referenced by `PlanetesContracts`'s JSON-Schema
 * via the `definition` "Overlays".
 */
export interface Overlays {
  schema_version: SchemaVersion;
  catalogs: OverlayCatalog[];
}
/**
 * GET /api/resolve: name to position and proper motion (docs/03 §5).
 *
 * This interface was referenced by `PlanetesContracts`'s JSON-Schema
 * via the `definition` "Resolved".
 */
export interface Resolved {
  schema_version: SchemaVersion;
  query: string;
  name: string | null;
  ra: RaDeg;
  dec: DecDeg;
  /**
   * Epoch of ra/dec, Julian year.
   */
  ref_epoch_jyear: number | null;
  pm_ra_masyr: number | null;
  pm_dec_masyr: number | null;
  parallax_mas: number | null;
  /**
   * Service that resolved the name.
   */
  source: string;
}
/**
 * Body of POST /api/spectrum (docs/03 §4).
 *
 * This interface was referenced by `PlanetesContracts`'s JSON-Schema
 * via the `definition` "SpectrumRequest".
 */
export interface SpectrumRequest {
  schema_version?: SchemaVersion;
  ra: RaDeg;
  dec: DecDeg;
  /**
   * Release to query. auto = QR3, then fall back to QR2.
   */
  release?: "auto" | "QR3" | "QR2";
  /**
   * auto = PSF fit, fall back to aperture.
   */
  method?: "auto" | "psf" | "aperture";
  pm?: ProperMotion | null;
}
