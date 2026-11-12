"""Two Opinions verdict engine (D4.4): combine the motion opinion and the spectrum opinion per docs/04 §2–§3.

Stars and brown dwarfs: tangential speed v_t = 4.74 × μ[″/yr] × d[pc] km/s, with d from the spectrum.
  5–150 km/s → agree · 150–400 km/s → agree, possible old/halo object · > 400 km/s → disagree ·
  no motion for a claimed nearby dwarf → disagree.
Asteroids: the motion distance range and the thermometer distance range (AU) overlap → agree, else disagree;
  thermometer can't measure → can't tell.
Anything unmeasured → can't tell. Wording follows docs/04 §8 ("consistent with", never "discovered").
"""

from __future__ import annotations

from planetes.contracts import Distance, MotionOpinion, SpectrumOpinion, Verdict

KM_S_PER_ARCSEC_YR_PC = 4.74
V_T_NORMAL_KMS = (5.0, 150.0)
V_T_HALO_MAX_KMS = 400.0
# A brown dwarf "nearby" claim: spectrum distance below this (pc).
NEARBY_PC = 50.0
QUALITY_CONFIDENCE = {"good": 0.9, "fair": 0.7, "poor": 0.4}


def _range(d: Distance) -> tuple[float, float] | None:
    if d.lo is None and d.hi is None:
        return None
    lo = d.lo if d.lo is not None else d.hi
    hi = d.hi if d.hi is not None else d.lo
    return (min(lo, hi), max(lo, hi))  # type: ignore[type-var]


def _confidence(m: MotionOpinion, s: SpectrumOpinion) -> float:
    return min(QUALITY_CONFIDENCE[m.quality], QUALITY_CONFIDENCE[s.quality])


def _star_class(s: SpectrumOpinion) -> str:
    """Spectral types L, T, Y are brown dwarfs; anything else typed is a star."""
    return "brown_dwarf" if s.class_ and s.class_.strip()[:1].upper() in {"L", "T", "Y"} else "nearby_star"


def _fmt(x: float) -> str:
    return f"{x:.0f}" if abs(x) >= 100 else f"{x:.3g}"


def cant_tell(reason: str, *more: str) -> Verdict:
    return Verdict(label="cant_tell", **{"class": "unknown"}, confidence=None, reasons=[reason, *more])


def decide(motion: MotionOpinion, spectrum: SpectrumOpinion, saturated: bool = False) -> Verdict:
    """The verdict for one object. `saturated`: the spectrum points were saturated (never used, docs/04 §8)."""
    if saturated:
        return cant_tell(
            "The object is too bright for SPHEREx: its pixels are saturated, so its spectrum is not used.",
            "The motion opinion stands on its own; the spectrum can't confirm it.",
        )
    if motion.kind == "sso_rate" or spectrum.kind == "thermal":
        return _decide_asteroid(motion, spectrum)
    return _decide_star(motion, spectrum)


def _decide_star(m: MotionOpinion, s: SpectrumOpinion) -> Verdict:
    d = _range(s.distance)
    if s.kind != "template" or d is None or s.distance.unit != "pc":
        return cant_tell(
            "The spectrum does not match a star or brown-dwarf template well enough to estimate a distance."
        )
    klass = _star_class(s)
    if m.kind == "static":
        if klass == "brown_dwarf" and d[1] < NEARBY_PC:
            return Verdict(
                label="disagree",
                **{"class": "unknown"},
                confidence=_confidence(m, s),
                reasons=[
                    f"The spectrum looks like a brown dwarf about {_fmt(d[0])}–{_fmt(d[1])} pc away, "
                    "but a dwarf that close should move across the sky, and this object does not.",
                    "Unexplained candidate, needs follow-up: possibly a wrong type, a blend or an image artifact.",
                ],
            )
        return Verdict(
            label="agree",
            **{"class": klass},
            confidence=_confidence(m, s),
            reasons=[f"No motion was seen, which fits an object about {_fmt(d[0])}–{_fmt(d[1])} pc away."],
        )
    if m.kind != "proper_motion" or m.value is None or m.unit != "arcsec/yr":
        return cant_tell("The motion could not be measured, so the two opinions can't be compared.")

    mu = abs(m.value)
    vt_lo, vt_hi = KM_S_PER_ARCSEC_YR_PC * mu * d[0], KM_S_PER_ARCSEC_YR_PC * mu * d[1]
    vt = KM_S_PER_ARCSEC_YR_PC * mu * (d[0] + d[1]) / 2
    speed = (
        f"Moving {_fmt(mu)}″/yr at {_fmt(d[0])}–{_fmt(d[1])} pc means a sideways speed of "
        f"{_fmt(vt_lo)}–{_fmt(vt_hi)} km/s."
    )
    conf = _confidence(m, s)
    if vt > V_T_HALO_MAX_KMS:
        return Verdict(
            label="disagree",
            **{"class": "unknown"},
            confidence=conf,
            reasons=[
                speed,
                "That is faster than stars near the Sun move, so the distance or the type is probably wrong.",
                "Unexplained candidate, needs follow-up: possibly a blend or an image artifact.",
            ],
        )
    if vt > V_T_NORMAL_KMS[1]:
        return Verdict(
            label="agree",
            **{"class": klass},
            confidence=round(conf * 0.85, 2),
            reasons=[speed, "That is fast but possible for an old star from the Milky Way's halo."],
        )
    note = "a normal speed for stars near the Sun" if vt >= V_T_NORMAL_KMS[0] else "slow, but possible"
    what = "a brown dwarf" if klass == "brown_dwarf" else "a nearby star"
    return Verdict(
        label="agree",
        **{"class": klass},
        confidence=conf,
        reasons=[speed, f"That is {note}, so both opinions are consistent with {what}."],
    )


def _decide_asteroid(m: MotionOpinion, s: SpectrumOpinion) -> Verdict:
    rm, rs = _range(m.distance), _range(s.distance)
    if rs is None or s.kind != "thermal" or s.distance.unit != "au":
        return cant_tell("The thermometer could not measure this object (too faint at 4–5 µm).")
    if m.kind != "sso_rate" or rm is None or m.distance.unit != "au":
        return cant_tell("The motion did not give a distance range, so the two opinions can't be compared.")
    motion_txt = f"Its motion puts it {_fmt(rm[0])}–{_fmt(rm[1])} AU from the Sun"
    warm_txt = f"its warmth puts it {_fmt(rs[0])}–{_fmt(rs[1])} AU away"
    if rm[0] <= rs[1] and rs[0] <= rm[1]:
        return Verdict(
            label="agree",
            **{"class": "asteroid"},
            confidence=_confidence(m, s),
            reasons=[
                f"{motion_txt}, and {warm_txt}: the ranges overlap.",
                "Both opinions are consistent with an asteroid.",
            ],
        )
    return Verdict(
        label="disagree",
        **{"class": "unknown"},
        confidence=_confidence(m, s),
        reasons=[
            f"{motion_txt}, but {warm_txt}: the ranges do not overlap.",
            "Unexplained candidate, needs follow-up: possibly a wrong link between frames, an artifact "
            "or an unusual object.",
        ],
    )
