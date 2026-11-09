"""Time-lapse job: wires POST /api/timelapse to the planetes pipeline.

The pipeline pieces it needs are still being built: frame search and cutouts (access.py, D2.1) and
reprojection/rendering (frames.py and render.py, D2.2). Until they are merged, the job ends with a clear
error instead of returning anything made up. When they land, the calls go in run_timelapse below,
written against their real function signatures.
"""

from __future__ import annotations

import importlib.util

from planetes.contracts import TimelapseRequest, TimelapseResult

from .jobs import JobContext, JobError

REQUIRED_MODULES = ("planetes.access", "planetes.frames", "planetes.render")


def missing_modules() -> list[str]:
    return [m for m in REQUIRED_MODULES if importlib.util.find_spec(m) is None]


def run_timelapse(req: TimelapseRequest, ctx: JobContext) -> TimelapseResult:
    ctx.progress(0, None, "checking pipeline")
    missing = missing_modules()
    if missing:
        raise JobError(
            "INTERNAL",
            "Live time-lapses are not available yet.",
            "The frame search and rendering steps are still being built (" + ", ".join(missing) + ").",
        )
    raise JobError(
        "INTERNAL",
        "Live time-lapses are not available yet.",
        "The pipeline modules exist but are not wired into the API yet.",
    )
