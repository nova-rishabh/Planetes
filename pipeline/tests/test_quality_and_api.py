"""Automated unit & integration tests for D2.5 scientific quality reports and API endpoints."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from planetes import quality, stack
from planetes.contracts import (
    Detector,
    SpectrumPoint,
    SpectrumProvenance,
    SpectrumResult,
    SpectrumSummary,
    SpectrumTarget,
)


def _sample_spectrum_result() -> SpectrumResult:
    pts = [
        SpectrumPoint(
            obs_id=f"obs_{d}",
            mjd=61000.0 + d,
            detector=d,
            wavelength_um=0.8 + 0.65 * d,
            bandwidth_um=0.03,
            flux_ujy=250.0 + 10.0 * d,
            flux_err_ujy=25.0,
            snr=10.0,
            flags=0,
            saturated=False,
            used=True,
            reject_reason=None,
            pair_id={1: "D1&D4", 4: "D1&D4", 2: "D2&D5", 5: "D2&D5", 3: "D3&D6", 6: "D3&D6"}[d],
            method="psf" if d != 6 else "aperture",
            ra=180.0,
            dec=0.0,
        )
        for d in range(1, 7)
    ]
    return SpectrumResult(
        schema_version="1.0",
        target=SpectrumTarget(ra=180.0, dec=0.0, pm=None),
        points=pts,
        summary=SpectrumSummary(
            n_points=6,
            n_used=6,
            n_rejected=0,
            bands_covered=[Detector(d) for d in range(1, 7)],
        ),
        provenance=SpectrumProvenance(release="QR3", code_version="test"),
    )


def test_quality_report_generation_json_and_markdown(tmp_path: Path) -> None:
    """D2.5 quality report must score Grade A for 6-band high-SNR spectra and write JSON + Markdown."""
    spec_res = _sample_spectrum_result()
    spec_q = quality.evaluate_spectrum_quality(spec_res)

    assert spec_q.quality_grade == "A"
    assert spec_q.detectors_covered == [1, 2, 3, 4, 5, 6]
    assert spec_q.missing_detectors == []
    assert spec_q.pairs_covered == ["D1&D4", "D2&D5", "D3&D6"]
    assert spec_q.psf_fit_count == 5
    assert spec_q.aperture_fallback_count == 1

    coadd = stack.CoaddResult(
        image=np.ones((10, 10)),
        variance=np.full((10, 10), 0.25),
        coverage=np.full((10, 10), 4, dtype=np.int32),
        detector=1,
        epoch_index=0,
        mjd_start=61000.0,
        mjd_end=61005.0,
        n_frames=4,
    )
    stack_q = quality.evaluate_stack_quality(coadd, single_frame_variances=[np.ones((10, 10))] * 4)
    assert stack_q.empirical_variance_reduction == 4.0

    json_path, md_path = quality.save_quality_report(tmp_path, spec_q, [stack_q])
    assert json_path.exists() and md_path.exists()
    parsed = json.loads(json_path.read_text(encoding="utf-8"))
    assert parsed["spectrum"]["quality_grade"] == "A"
    assert "Empirical Var Reduction" in md_path.read_text(encoding="utf-8")


def test_api_routes_registered() -> None:
    """FastAPI router must expose /api/health, /api/timelapse, /api/spectrum, /api/jobs/{job_id}, and frame routes."""
    from api import main as api_main

    paths = {r.path for r in api_main.router.routes}
    expected = {
        "/api/health",
        "/api/timelapse",
        "/api/spectrum",
        "/api/jobs/{job_id}",
        "/api/frames/{frame_id}.webp",
        "/api/frames/{frame_id}/flags.png",
    }
    assert expected.issubset(paths)
