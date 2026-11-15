"""One test per verdict rule branch (docs/04 §2–§3). Inputs are rule-boundary test values, not results."""

from __future__ import annotations

from planetes.contracts import Distance, MotionOpinion, MotionTruth, SpectrumOpinion
from planetes.verdict import decide


def motion(kind="proper_motion", value=1.0, unit="arcsec/yr", lo=None, hi=None, dunit=None, q="good"):
    return MotionOpinion(
        kind=kind, value=value, unit=unit, err=None, pa_deg=None,
        distance=Distance(lo=lo, hi=hi, unit=dunit), truth=MotionTruth(value=None, source=None),
        quality=q, method="test",
    )  # fmt: skip


def spectrum(kind="template", klass="T8", lo=3.0, hi=4.0, unit="pc", q="good"):
    return SpectrumOpinion.model_validate(
        {"kind": kind, "class": klass, "temperature_k": None,
         "distance": {"lo": lo, "hi": hi, "unit": unit}, "quality": q, "method": "test"}
    )  # fmt: skip


def label_class(v):
    return v.label, v.class_


def test_normal_speed_agrees():
    # 4.74 × 4"/yr × 3.5 pc ≈ 66 km/s
    v = decide(motion(value=4.0), spectrum(klass="T1", lo=3.0, hi=4.0))
    assert label_class(v) == ("agree", "brown_dwarf") and v.confidence == 0.9
    assert all("discover" not in r.lower() and "confirm" not in r.lower() for r in v.reasons)


def test_halo_speed_agrees_with_note():
    v = decide(motion(value=10.0), spectrum(klass="M4", lo=4.0, hi=5.0))  # ≈ 213 km/s
    assert label_class(v) == ("agree", "nearby_star") and "halo" in v.reasons[1]


def test_too_fast_disagrees():
    v = decide(motion(value=10.0), spectrum(lo=20.0, hi=30.0))  # ≈ 1185 km/s
    assert label_class(v) == ("disagree", "unknown") and "follow-up" in v.reasons[-1]


def test_static_nearby_dwarf_disagrees_and_static_star_agrees():
    assert decide(motion(kind="static", value=None), spectrum(klass="T5", lo=5, hi=8)).label == "disagree"
    assert decide(motion(kind="static", value=None), spectrum(klass="M2", lo=200, hi=300)).label == "agree"


def test_missing_measurements_cant_tell():
    assert decide(motion(kind="unknown", value=None), spectrum()).label == "cant_tell"
    assert decide(motion(), spectrum(kind="none", klass=None, lo=None, hi=None, unit=None)).label == "cant_tell"
    assert decide(motion(), spectrum(), saturated=True).label == "cant_tell"


def test_asteroid_ranges():
    m = motion(kind="sso_rate", value=30.0, unit="arcsec/hr", lo=2.0, hi=3.2, dunit="au")
    assert label_class(decide(m, spectrum(kind="thermal", klass=None, lo=2.5, hi=3.5, unit="au"))) == (
        "agree",
        "asteroid",
    )
    assert decide(m, spectrum(kind="thermal", klass=None, lo=5.0, hi=6.0, unit="au")).label == "disagree"
    assert decide(m, spectrum(kind="thermal", klass=None, lo=None, hi=None, unit=None)).label == "cant_tell"
