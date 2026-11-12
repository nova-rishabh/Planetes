"""Scientific quality assessment and reporting for SPHEREx photometry and stacks (Deliverable D2.5).

Generates structured JSON diagnostics and human-readable Markdown quality reports covering:
- Detector & simultaneous pair coverage (D1..D6, D1&D4, D2&D5, D3&D6)
- Photometry method breakdown (forced ePSF vs. circular aperture fallback)
- Flag & rejection statistics (saturation, cosmic rays/bad pixels, out-of-bounds)
- Signal-to-noise (SNR) distribution and wavelength span
- Inverse-variance coadd noise reduction efficiency
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC_DIR = str(Path(__file__).resolve().parents[1])
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

import json
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Sequence

import numpy as np

from planetes.contracts import SpectrumResult, TimelapseResult
from planetes.stack import CoaddResult

ALL_DETECTORS = (1, 2, 3, 4, 5, 6)
ALL_PAIRS = ("D1&D4", "D2&D5", "D3&D6")


@dataclass
class SpectrumQualityMetrics:
    """Quantitative quality summary for a SPHEREx 1D spectrum extraction."""

    target_ra: float
    target_dec: float
    release: str
    n_points_total: int
    n_points_used: int
    n_points_rejected: int
    acceptance_rate: float
    detectors_covered: list[int]
    missing_detectors: list[int]
    pairs_covered: list[str]
    psf_fit_count: int
    aperture_fallback_count: int
    psf_fit_fraction: float
    rejection_reasons: dict[str, int]
    median_snr: float | None
    max_snr: float | None
    min_wavelength_um: float | None
    max_wavelength_um: float | None
    quality_grade: str
    warnings: list[str] = field(default_factory=list)


@dataclass
class StackQualityMetrics:
    """Quantitative quality summary for SPHEREx coadded / stacked images."""

    detector: int | None
    n_frames: int
    valid_pixel_fraction: float
    median_coverage: float
    median_variance: float | None
    theoretical_noise_gain: float
    empirical_variance_reduction: float | None
    peak_signal_mjy_sr: float | None
    warnings: list[str] = field(default_factory=list)


def evaluate_spectrum_quality(result: SpectrumResult) -> SpectrumQualityMetrics:
    """Compute scientific quality metrics and diagnostic warnings for a SpectrumResult."""
    pts = result.points
    used_pts = [p for p in pts if p.used]
    rej_pts = [p for p in pts if not p.used]

    n_total = len(pts)
    n_used = len(used_pts)
    n_rej = len(rej_pts)
    acceptance_rate = round(n_used / n_total, 4) if n_total > 0 else 0.0

    covered = sorted({int(p.detector) for p in used_pts})
    missing = [d for d in ALL_DETECTORS if d not in covered]
    pairs = sorted({p.pair_id for p in used_pts if p.pair_id is not None})

    psf_count = sum(1 for p in used_pts if p.method == "psf")
    ap_count = sum(1 for p in used_pts if p.method == "aperture")
    psf_frac = round(psf_count / n_used, 4) if n_used > 0 else 0.0

    reasons = Counter(p.reject_reason or "unknown" for p in rej_pts)

    snrs = [float(p.snr) for p in used_pts if p.snr is not None and np.isfinite(p.snr)]
    waves = [float(p.wavelength_um) for p in used_pts if p.wavelength_um is not None and np.isfinite(p.wavelength_um)]

    med_snr = round(float(np.median(snrs)), 2) if snrs else None
    max_snr = round(float(np.max(snrs)), 2) if snrs else None
    min_wave = round(float(np.min(waves)), 4) if waves else None
    max_wave = round(float(np.max(waves)), 4) if waves else None

    diag_warnings: list[str] = []
    if n_used == 0:
        diag_warnings.append("No usable spectral points survived flag/bounds filtering.")
    if missing:
        diag_warnings.append(f"Missing coverage in detector(s): {missing}.")
    if n_used > 0 and psf_frac < 0.5:
        diag_warnings.append(
            f"High aperture-fallback rate ({ap_count}/{n_used}); check EPSF availability or edge proximity."
        )
    if med_snr is not None and med_snr < 3.0:
        diag_warnings.append(f"Low median SNR ({med_snr}); target may be faint in single exposures.")
    if reasons.get("saturated", 0) > 0:
        diag_warnings.append(f"{reasons['saturated']} exposure(s) rejected due to core saturation.")

    if n_used == 0:
        grade = "FAIL"
    elif len(covered) == 6 and acceptance_rate >= 0.75 and (med_snr is None or med_snr >= 3.0):
        grade = "A"
    elif len(covered) >= 4 and acceptance_rate >= 0.5:
        grade = "B"
    else:
        grade = "C"

    return SpectrumQualityMetrics(
        target_ra=result.target.ra,
        target_dec=result.target.dec,
        release=result.provenance.release,
        n_points_total=n_total,
        n_points_used=n_used,
        n_points_rejected=n_rej,
        acceptance_rate=acceptance_rate,
        detectors_covered=covered,
        missing_detectors=missing,
        pairs_covered=pairs,
        psf_fit_count=psf_count,
        aperture_fallback_count=ap_count,
        psf_fit_fraction=psf_frac,
        rejection_reasons=dict(reasons),
        median_snr=med_snr,
        max_snr=max_snr,
        min_wavelength_um=min_wave,
        max_wavelength_um=max_wave,
        quality_grade=grade,
        warnings=diag_warnings,
    )


def evaluate_stack_quality(
    coadd: CoaddResult,
    single_frame_variances: Sequence[np.ndarray] | None = None,
) -> StackQualityMetrics:
    """Evaluate noise reduction, coverage, and dynamic range of a stacked CoaddResult."""
    valid_px = np.isfinite(coadd.image) & (coadd.coverage > 0)
    valid_frac = round(float(np.mean(valid_px)), 4)
    med_cov = round(float(np.median(coadd.coverage[valid_px])), 2) if np.any(valid_px) else 0.0

    finite_var = coadd.variance[np.isfinite(coadd.variance) & (coadd.variance > 0)]
    med_var = float(np.median(finite_var)) if finite_var.size > 0 else None

    emp_reduction: float | None = None
    if med_var is not None and single_frame_variances:
        single_meds = [
            float(np.median(v[np.isfinite(v) & (v > 0)]))
            for v in single_frame_variances
            if np.any(np.isfinite(v) & (v > 0))
        ]
        if single_meds:
            emp_reduction = round(float(np.median(single_meds)) / med_var, 3)

    peak_sig = round(float(np.nanmax(coadd.image)), 4) if np.any(np.isfinite(coadd.image)) else None
    theo_gain = round(float(np.sqrt(max(1, coadd.n_frames))), 3)

    stack_warnings: list[str] = []
    if valid_frac < 0.8:
        stack_warnings.append(f"Only {valid_frac * 100:.1f}% of grid pixels have valid coverage.")
    if emp_reduction is not None and coadd.n_frames > 1 and emp_reduction < 0.7 * coadd.n_frames:
        stack_warnings.append(
            f"Empirical variance reduction ({emp_reduction}x) is below ideal ({coadd.n_frames}x) due to masked pixels or unequal exposure weights."
        )

    return StackQualityMetrics(
        detector=coadd.detector,
        n_frames=coadd.n_frames,
        valid_pixel_fraction=valid_frac,
        median_coverage=med_cov,
        median_variance=round(med_var, 6) if med_var is not None else None,
        theoretical_noise_gain=theo_gain,
        empirical_variance_reduction=emp_reduction,
        peak_signal_mjy_sr=peak_sig,
        warnings=stack_warnings,
    )


def evaluate_timelapse_quality(result: TimelapseResult) -> dict[str, object]:
    """Summarize frame coverage and flag statistics across a TimelapseResult."""
    n_frames = len(result.frames)
    flagged_fracs = [f.flagged_frac for f in result.frames]
    sat_center = sum(1 for f in result.frames if f.saturated_near_center)
    detectors = sorted({int(f.detector.root) for f in result.frames})
    return {
        "mode": result.request.mode,
        "release": result.request.release,
        "n_frames": n_frames,
        "n_epochs": len(result.epochs),
        "detectors_present": detectors,
        "mean_flagged_fraction": round(float(np.mean(flagged_fracs)), 4) if flagged_fracs else 0.0,
        "frames_saturated_near_center": sat_center,
    }


def render_quality_markdown(
    spec_metrics: SpectrumQualityMetrics,
    stack_metrics: Sequence[StackQualityMetrics] | None = None,
) -> str:
    """Format spectrum and optional stacking quality metrics into a Markdown report."""
    lines = [
        "# SPHEREx Pipeline Scientific Quality Report",
        "",
        f"- **Generated (UTC):** {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S')}",
        f"- **Target Coordinates:** RA = `{spec_metrics.target_ra:.5f}°`, Dec = `{spec_metrics.target_dec:.5f}°`",
        f"- **Data Release:** `{spec_metrics.release}`",
        f"- **Overall Quality Grade:** **{spec_metrics.quality_grade}**",
        "",
        "## 1. Photometry & Spectral Coverage",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Total / Used Points | {spec_metrics.n_points_used} / {spec_metrics.n_points_total} ({spec_metrics.acceptance_rate * 100:.1f}%) |",
        f"| Detectors Covered | {spec_metrics.detectors_covered} (Missing: {spec_metrics.missing_detectors or 'None'}) |",
        f"| Simultaneous Pairs | {', '.join(spec_metrics.pairs_covered) or 'None'} |",
        f"| Wavelength Range | {spec_metrics.min_wavelength_um} – {spec_metrics.max_wavelength_um} µm |",
        f"| Forced ePSF Fits | {spec_metrics.psf_fit_count} ({spec_metrics.psf_fit_fraction * 100:.1f}%) |",
        f"| Aperture Fallbacks | {spec_metrics.aperture_fallback_count} |",
        f"| Median / Max SNR | {spec_metrics.median_snr} / {spec_metrics.max_snr} |",
        "",
    ]

    if spec_metrics.rejection_reasons:
        lines.extend(["### Rejection Breakdown", ""])
        for reason, count in sorted(spec_metrics.rejection_reasons.items()):
            lines.append(f"- `{reason}`: {count} frame(s)")
        lines.append("")

    if stack_metrics:
        lines.extend(
            [
                "## 2. Image Stacking & Noise Reduction",
                "",
                "| Detector | Frames | Valid Area | Median Coverage | Median Variance | Empirical Var Reduction |",
                "|---|---|---|---|---|---|",
            ]
        )
        for sm in stack_metrics:
            det_label = f"D{sm.detector}" if sm.detector is not None else "All"
            red_label = f"{sm.empirical_variance_reduction}x" if sm.empirical_variance_reduction is not None else "N/A"
            lines.append(
                f"| {det_label} | {sm.n_frames} | {sm.valid_pixel_fraction * 100:.1f}% | "
                f"{sm.median_coverage} | {sm.median_variance} | {red_label} |"
            )
        lines.append("")

    all_warnings = list(spec_metrics.warnings)
    if stack_metrics:
        for sm in stack_metrics:
            all_warnings.extend(sm.warnings)

    lines.extend(["## 3. Diagnostic Notes", ""])
    if all_warnings:
        for w in all_warnings:
            lines.append(f"- {w}")
    else:
        lines.append("- All quality checks passed with no anomalies.")

    return "\n".join(lines) + "\n"


def save_quality_report(
    output_dir: str | Path,
    spec_metrics: SpectrumQualityMetrics,
    stack_metrics: Sequence[StackQualityMetrics] | None = None,
) -> tuple[Path, Path]:
    """Write quality_report.json and quality_report.md into output_dir."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    payload = {
        "generated_utc": datetime.now(UTC).isoformat(),
        "spectrum": asdict(spec_metrics),
        "stacks": [asdict(s) for s in stack_metrics] if stack_metrics else [],
    }
    json_path = out / "quality_report.json"
    md_path = out / "quality_report.md"

    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    md_path.write_text(render_quality_markdown(spec_metrics, stack_metrics), encoding="utf-8")
    return json_path, md_path


if __name__ == "__main__":
    from planetes import frames, photometry, stack
    from astropy.io import fits
    from astropy.wcs import WCS

    root = Path(__file__).resolve().parents[3]
    fits_files = sorted((root / ".planetes-cache").rglob("*.fits"))
    if not fits_files:
        fits_files = sorted((root / "pipeline" / "tests" / "data").glob("*.fits"))

    print(f"Running D2.5 quality evaluation on {len(fits_files)} cached FITS files...")
    if fits_files:
        spec_res = photometry.extract_spectrum(fits_files, ra=269.46293, dec=4.72563)
        spec_q = evaluate_spectrum_quality(spec_res)

        with fits.open(fits_files[0]) as hdul:
            w0 = WCS(hdul["IMAGE"].header)
            ra_c, dec_c = w0.pixel_to_world_values(11, 11)
        ref_wcs, _ = frames.make_reference_grid(float(ra_c), float(dec_c), size_pixels=32)

        imgs, vars_, goods = [], [], []
        for f in fits_files[:4]:
            im, va, gd = stack.prepare_reprojected_variance(f.read_bytes(), ref_wcs, grid_shape=(32, 32))
            imgs.append(im)
            vars_.append(va)
            goods.append(gd)
        coadd = stack.inverse_variance_stack(imgs, vars_, goods, detector=1)
        stack_q = evaluate_stack_quality(coadd, single_frame_variances=vars_)

        md = render_quality_markdown(spec_q, [stack_q])
        print(md)
        