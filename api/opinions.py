"""Two Opinions for one object (docs/03 §5, docs/04 §2-§5).

Each opinion comes from a provider. Until the real measurements exist (D3.3 motion fit, D4.1/D4.3 spectrum
typer), the providers return None and the object gets an honest "can't tell" with the reason, never a guess.
To wire a measurement in, replace `measure_motion` or `measure_spectrum`; the verdict and the contract stay the same.
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
)
from planetes.verdict import cant_tell, decide

NO_DISTANCE = Distance(lo=None, hi=None, unit=None)
MOTION_PENDING = "Motion has not been measured for this object yet."
SPECTRUM_PENDING = "The spectrum has not been measured and typed for this object yet."


def measure_motion(req: OpinionsRequest) -> MotionOpinion | None:
    """Proper motion from SPHEREx positions (D3.3). Not built yet: None."""
    return None


def measure_spectrum(req: OpinionsRequest) -> tuple[SpectrumOpinion, bool] | None:
    """(spectrum opinion, saturated) from the measured spectrum (D4.1 + D4.3 / D4.2). Not built yet: None."""
    return None


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


def opinions_for(req: OpinionsRequest) -> Opinions:
    motion = measure_motion(req)
    measured = measure_spectrum(req)
    spectrum, saturated = measured if measured is not None else (None, False)

    if motion is not None and spectrum is not None:
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
