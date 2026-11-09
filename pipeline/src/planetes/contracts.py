# GENERATED, DO NOT EDIT. Source: contracts/*.schema.json. Regenerate with `make contracts`.

from __future__ import annotations

from typing import Any, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, RootModel, constr


class PlanetesContracts(RootModel[Any]):
    root: Any = Field(..., title="PlanetesContracts")


class Detector(RootModel[int]):
    root: int = Field(..., ge=1, le=6)
    """
    SPHEREx detector number (D1-D6).
    """


class Distance(BaseModel):
    """
    Distance range. null = not measured.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    lo: float | None
    hi: float | None
    unit: Literal["pc", "au"] | None


class Epoch(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    index: int = Field(..., ge=0)
    mjd_start: float
    mjd_end: float
    n_frames: int = Field(..., ge=0)


class ErrorBody(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    code: Literal[
        "BAD_INPUT",
        "NOT_FOUND",
        "NO_COVERAGE",
        "IRSA_TIMEOUT",
        "IRSA_ERROR",
        "TOO_LARGE",
        "INTERNAL",
    ]
    message: str
    hint: str | None


class FlagLegendItem(BaseModel):
    """
    One FLAGS bit, as read from the header MP_* keys.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    bit: int = Field(..., ge=0)
    name: str
    plain: str | None
    """
    Plain-language meaning.
    """


class TargetXy(RootModel[list[float]]):
    root: list[float] = Field(..., max_length=2, min_length=2)
    """
    Where the (propagated) target falls on the grid: 0-based pixel (x, y), x east-to-west as drawn, y increasing north (origin lower-left, numpy origin='lower'). Rendered images have north at the top.
    """


class Naxi(RootModel[int]):
    root: int = Field(..., ge=1)


class Grid(BaseModel):
    """
    Common north-up output grid every frame is reprojected onto.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    projection: Literal["TAN"]
    crval_deg: list[float] = Field(..., max_length=2, min_length=2)
    crpix: list[float] = Field(..., max_length=2, min_length=2)
    """
    Reference pixel, FITS 1-based convention.
    """
    cdelt_deg: float = Field(..., gt=0.0)
    naxis: list[Naxi] = Field(..., max_length=2, min_length=2)
    north_up: bool


class JobId(RootModel[str]):
    root: str = Field(..., pattern="^j_[A-Za-z0-9_-]+$")


class JobProgress(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    done: int = Field(..., ge=0)
    total: int | None = Field(..., ge=0)
    """
    null while the total is not yet known.
    """
    stage: str | None


class MotionTruth(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    value: float | None
    source: str | None


class AtMjd(RootModel[list[float]]):
    root: list[float] = Field(..., max_length=2, min_length=2)


class ProperMotion(BaseModel):
    """
    Proper motion and its reference epoch, as returned by /resolve.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    pm_ra_masyr: float
    """
    Proper motion in RA, mas/yr.
    """
    pm_dec_masyr: float
    """
    Proper motion in Dec, mas/yr.
    """
    ref_epoch_jyear: float
    """
    Reference epoch, Julian year (Gaia DR3 = 2016.0).
    """


class Provenance(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    tap_query: str | None
    generated_utc: AwareDatetime
    code_version: str = Field(..., min_length=1)


class SpectrumOpinion(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    kind: Literal["template", "thermal", "none"]
    class_: str | None = Field(..., alias="class")
    temperature_k: float | None
    distance: Distance
    quality: Literal["good", "fair", "poor"]
    method: str


class SpectrumPoint(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    obs_id: str
    mjd: float
    detector: int = Field(..., ge=1, le=6)
    """
    SPHEREx detector number (D1-D6).
    """
    wavelength_um: float | None
    bandwidth_um: float | None
    flux_ujy: float | None
    """
    null until measured.
    """
    flux_err_ujy: float | None
    snr: float | None
    flags: int = Field(..., ge=0)
    """
    Raw FLAGS bitmask at the source position.
    """
    saturated: bool
    used: bool
    reject_reason: str | None
    pair_id: str | None
    """
    Simultaneous detector pair (D1&D4, D2&D5, D3&D6).
    """
    method: Literal["psf", "aperture"] | None
    ra: float = Field(..., ge=0.0, lt=360.0)
    """
    Right ascension, ICRS, degrees.
    """
    dec: float = Field(..., ge=-90.0, le=90.0)
    """
    Declination, ICRS, degrees.
    """


class SpectrumProvenance(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    release: Literal["QR2", "QR3"]
    """
    SPHEREx Quick Release a measurement came from.
    """
    code_version: str = Field(..., min_length=1)


class SpectrumRequest(BaseModel):
    """
    Body of POST /api/spectrum (docs/03 §4).
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    schema_version: Literal["1.0"] | None = None
    """
    Contract version (docs/03 §1).
    """
    ra: float = Field(..., ge=0.0, lt=360.0)
    """
    Right ascension, ICRS, degrees.
    """
    dec: float = Field(..., ge=-90.0, le=90.0)
    """
    Declination, ICRS, degrees.
    """
    release: Literal["auto", "QR3", "QR2"] = "auto"
    """
    Release to query. auto = QR2 and QR3 together (they cover different weeks); QR3 wins for the same exposure.
    """
    method: Literal["auto", "psf", "aperture"] = "auto"
    """
    auto = PSF fit, fall back to aperture.
    """
    pm: ProperMotion | None = None


class SpectrumSummary(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    n_points: int = Field(..., ge=0)
    n_used: int = Field(..., ge=0)
    n_rejected: int = Field(..., ge=0)
    bands_covered: list[Detector]


class SpectrumTarget(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    ra: float = Field(..., ge=0.0, lt=360.0)
    """
    Right ascension, ICRS, degrees.
    """
    dec: float = Field(..., ge=-90.0, le=90.0)
    """
    Declination, ICRS, degrees.
    """
    pm: ProperMotion | None


class Stretch(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    method: Literal["linear", "asinh", "log"]
    lo: float
    hi: float
    unit: str
    """
    Unit of lo/hi, e.g. MJy/sr.
    """


class TimelapseRequest(BaseModel):
    """
    Body of POST /api/timelapse (docs/03 §4). Echoed in TimelapseResult.request.
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    schema_version: Literal["1.0"] | None = None
    """
    Contract version (docs/03 §1).
    """
    ra: float = Field(..., ge=0.0, lt=360.0)
    """
    Right ascension, ICRS, degrees.
    """
    dec: float = Field(..., ge=-90.0, le=90.0)
    """
    Declination, ICRS, degrees.
    """
    fov_deg: float = Field(0.1, ge=0.03, le=0.5)
    mode: Literal["exposures", "stacks", "difference", "sum", "color"] = "stacks"
    detectors: list[Detector] = Field(
        [1, 2, 3, 4, 5, 6], max_length=6, min_length=1, validate_default=True
    )
    release: Literal["auto", "QR3", "QR2"] = "auto"
    """
    Release to query. auto = QR2 and QR3 together (they cover different weeks); QR3 wins for the same exposure.
    """
    mjd_start: float | None = None
    mjd_end: float | None = None
    max_frames: int = Field(60, ge=1, le=120)
    pm: ProperMotion | None = None


class Verdict(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    label: Literal["agree", "disagree", "cant_tell"]
    class_: Literal["nearby_star", "brown_dwarf", "asteroid", "variable", "artifact", "unknown"] = (
        Field(..., alias="class")
    )
    confidence: float | None = Field(..., ge=0.0, le=1.0)
    reasons: list[str]


class Error(BaseModel):
    """
    Body of every HTTP 4xx/5xx response (docs/03 §3).
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    schema_version: Literal["1.0"]
    """
    Contract version (docs/03 §1).
    """
    error: ErrorBody


class Frame(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    id: str = Field(..., pattern="^f_[0-9a-f]{12}$")
    """
    f_ + first 12 hex of sha1(obs_id + cutout params).
    """
    kind: Literal["exposure", "stack", "difference", "sum", "color"]
    obs_id: str | None
    """
    IVOA publisher DID; null for combined frames (see members).
    """
    members: list[str]
    """
    obs_ids combined into this frame.
    """
    release: Literal["QR2", "QR3"]
    """
    SPHEREx Quick Release a measurement came from.
    """
    epoch_index: int | None = Field(..., ge=0)
    mjd: float | None
    utc: AwareDatetime | None
    detector: Detector | None
    wavelength_um: float | None
    bandwidth_um: float | None
    image_url: str
    flags_url: str | None
    flagged_frac: float | None = Field(..., ge=0.0, le=1.0)
    saturated_near_center: bool | None
    target_xy: TargetXy | None
    """
    Where the (propagated) target falls on the grid: 0-based pixel (x, y), x east-to-west as drawn, y increasing north (origin lower-left, numpy origin='lower'). Rendered images have north at the top.
    """
    notes: list[str]


class Health(BaseModel):
    """
    GET /api/health: liveness and upstream check (docs/03 §5).
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    schema_version: Literal["1.0"]
    """
    Contract version (docs/03 §1).
    """
    status: Literal["ok"]
    """
    The API process is up.
    """
    code_version: str = Field(..., min_length=1)
    """
    Git short hash of the running code, or "dev".
    """
    irsa_tap: Literal["ok", "slow", "down"]
    """
    Result of a live request to the IRSA TAP service.
    """
    default_release: Literal["QR2", "QR3"]
    """
    SPHEREx Quick Release a measurement came from.
    """
    cache_entries: int = Field(..., ge=0)


class JobCreated(BaseModel):
    """
    Response of POST /api/timelapse and POST /api/spectrum (docs/03 §3).
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    schema_version: Literal["1.0"]
    """
    Contract version (docs/03 §1).
    """
    job_id: str = Field(..., pattern="^j_[A-Za-z0-9_-]+$")


class MotionOpinion(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    kind: Literal["proper_motion", "sso_rate", "static", "unknown"]
    value: float | None
    unit: Literal["arcsec/yr", "arcsec/hr"] | None
    err: float | None
    """
    Uncertainty of value, same unit.
    """
    pa_deg: float | None
    distance: Distance
    truth: MotionTruth
    quality: Literal["good", "fair", "poor"]
    method: str


class OpinionObject(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    ra: float = Field(..., ge=0.0, lt=360.0)
    """
    Right ascension, ICRS, degrees.
    """
    dec: float = Field(..., ge=-90.0, le=90.0)
    """
    Declination, ICRS, degrees.
    """


class Opinions(BaseModel):
    """
    POST /api/opinions: Two Opinions (motion vs spectrum) for one object (docs/03 §5).
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    schema_version: Literal["1.0"]
    """
    Contract version (docs/03 §1).
    """
    object: OpinionObject
    motion: MotionOpinion
    spectrum: SpectrumOpinion
    verdict: Verdict


class OpinionsRequest(BaseModel):
    """
    Body of POST /api/opinions (docs/03 §4).
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    schema_version: Literal["1.0"] | None = None
    """
    Contract version (docs/03 §1).
    """
    ra: float = Field(..., ge=0.0, lt=360.0)
    """
    Right ascension, ICRS, degrees.
    """
    dec: float = Field(..., ge=-90.0, le=90.0)
    """
    Declination, ICRS, degrees.
    """
    spectrum_job_id: JobId | None = None
    pm: ProperMotion | None = None


class OverlaySource(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    id: str
    ra: float = Field(..., ge=0.0, lt=360.0)
    """
    Right ascension, ICRS, degrees.
    """
    dec: float = Field(..., ge=-90.0, le=90.0)
    """
    Declination, ICRS, degrees.
    """
    pm_ra_masyr: float | None
    pm_dec_masyr: float | None
    mag: float | None
    band: str | None
    at_mjd: dict[constr(pattern=r"^[0-9]+(\.[0-9]+)?$"), AtMjd]
    """
    Position [ra_deg, dec_deg] keyed by MJD (as a string).
    """


class Resolved(BaseModel):
    """
    GET /api/resolve: name to position and proper motion (docs/03 §5).
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    schema_version: Literal["1.0"]
    """
    Contract version (docs/03 §1).
    """
    query: str
    name: str | None
    ra: float = Field(..., ge=0.0, lt=360.0)
    """
    Right ascension, ICRS, degrees.
    """
    dec: float = Field(..., ge=-90.0, le=90.0)
    """
    Declination, ICRS, degrees.
    """
    ref_epoch_jyear: float | None
    """
    Epoch of ra/dec, Julian year.
    """
    pm_ra_masyr: float | None
    pm_dec_masyr: float | None
    parallax_mas: float | None
    source: str
    """
    Service that resolved the name.
    """


class SpectrumResult(BaseModel):
    """
    Result of a spectrum job, also baked as data/targets/{id}/spectrum.json (docs/03 §5-§6).
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    schema_version: Literal["1.0"]
    """
    Contract version (docs/03 §1).
    """
    target: SpectrumTarget
    points: list[SpectrumPoint]
    summary: SpectrumSummary
    provenance: SpectrumProvenance


class TimelapseResult(BaseModel):
    """
    Result of a time-lapse job, also baked as data/targets/{id}/timelapse_{mode}.json (docs/03 §5-§6).
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    schema_version: Literal["1.0"]
    """
    Contract version (docs/03 §1).
    """
    request: TimelapseRequest
    grid: Grid
    epochs: list[Epoch]
    frames: list[Frame]
    stretch: Stretch | None
    """
    Shared display stretch; null until computed.
    """
    flag_legend: list[FlagLegendItem]
    provenance: Provenance


class Job(BaseModel):
    """
    GET /api/jobs/{job_id}: status and (partial) result (docs/03 §5).
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    schema_version: Literal["1.0"]
    """
    Contract version (docs/03 §1).
    """
    job_id: str = Field(..., pattern="^j_[A-Za-z0-9_-]+$")
    kind: Literal["timelapse", "spectrum"]
    status: Literal["queued", "running", "done", "error"]
    progress: JobProgress
    result: TimelapseResult | SpectrumResult | None
    """
    TimelapseResult or SpectrumResult; partial while running, null before any output.
    """
    error: ErrorBody | None


class OverlayCatalog(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    name: str
    vizier: str | None
    """
    VizieR catalogue ID.
    """
    ref_epoch_jyear: float | None
    sources: list[OverlaySource]


class Overlays(BaseModel):
    """
    GET /api/overlays: catalog sources moved to each frame date (docs/03 §5).
    """

    model_config = ConfigDict(
        extra="forbid",
    )
    schema_version: Literal["1.0"]
    """
    Contract version (docs/03 §1).
    """
    catalogs: list[OverlayCatalog]
