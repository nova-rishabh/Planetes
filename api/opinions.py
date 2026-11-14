"""Two Opinions for one object (docs/03 §5, docs/04 §2-§5).

Each opinion comes from a provider. A provider with nothing measured returns None and the object gets an honest
"can't tell" with the reason, never a guess.
- Spectrum: the measured SPHEREx points (from a finished spectrum job, or a baked spectrum.json) -> brown-dwarf /
  star typer (D4.3) for objects with a proper motion, or the asteroid thermometer (D4.2) for moving solar-system
  objects. Saturated points are never used; if the spectrum is mostly saturated the verdict says so.
- Motion: D3.3 measured positions (wired when it lands; None until then).
"""

from __future__ import annotations

from planetes.contracts import (
    Distance,
    MotionOpinion,
    MotionTruth,
    OpinionObject,
    Opinions,
    OpinionsRequest,
    SpectrumOpinion,
    SpectrumPoint,
)
from planetes.thermal import thermal_opinion
from planetes.typing import spectrum_opinion
from planetes.verdict import cant_tell, decide

NO_DISTANCE = Distance(lo=None, hi=None, unit=None)
MOTION_PENDING = "Motion has not been measured for this object yet."
SPECTRUM_PENDING = "The spectrum has not been measured and typed for this object yet."


def measure_motion(req: OpinionsRequest) -> MotionOpinion | None:
    """Proper motion from SPHEREx positions (D3.3). Not built yet: None."""
    return None


SATURATED_SHARE = 0.5  # more than half the measured points saturated -> the spectrum can't be trusted for a verdict


def measure_spectrum(
    req: OpinionsRequest, points: list[SpectrumPoint] | None = None, moving_sso: bool = False
) -> tuple[SpectrumOpinion, bool] | None:
    """(spectrum opinion, saturated) from measured points; None when no spectrum was measured."""
    if not points:
        return None
    measured = [p for p in points if p.flux_ujy is not None or p.saturated]
    saturated = bool(measured) and sum(p.saturated for p in measured) / len(measured) > SATURATED_SHARE
    opinion, _ = thermal_opinion(points) if moving_sso else spectrum_opinion(points)
    return opinion, saturated


def _no_motion() -> MotionOpinion:
    return MotionOpinion(
        kind="unknown",
        value=None,
        unit=None,
        err=None,
        pa_deg=None,
        distance=NO_DISTANCE,
        truth=MotionTruth(value=None, source=None),
        quality="poor",
        method="not measured",
    )


def _no_spectrum() -> SpectrumOpinion:
    return SpectrumOpinion(
        kind="none",
        **{"class": None},
        temperature_k=None,
        distance=NO_DISTANCE,
        quality="poor",
        method="not measured",
    )


def opinions_for(
    req: OpinionsRequest,
    points: list[SpectrumPoint] | None = None,
    motion: MotionOpinion | None = None,
    moving_sso: bool = False,
) -> Opinions:
    """`points`: measured spectrum (job result or baked file); `motion`: a measured motion opinion, if any."""
    motion = motion or measure_motion(req)
    measured = measure_spectrum(req, points, moving_sso)
    spectrum, saturated = measured if measured is not None else (None, False)

    if saturated and spectrum is not None:
        # Saturation decides on its own (docs/04 §8): say so even when motion is still missing.
        verdict = decide(motion or _no_motion(), spectrum, saturated=True)
        if motion is None:
            verdict.reasons = [verdict.reasons[0], MOTION_PENDING]
    elif motion is not None and spectrum is not None:
        verdict = decide(motion, spectrum, saturated)
    else:
        missing = [r for r, m in ((MOTION_PENDING, motion), (SPECTRUM_PENDING, spectrum)) if m is None]
        verdict = cant_tell(*missing)

    return Opinions(
        schema_version="1.0",
        object=OpinionObject(ra=req.ra, dec=req.dec),
        motion=motion or _no_motion(),
        spectrum=spectrum or _no_spectrum(),
        verdict=verdict,
    )
