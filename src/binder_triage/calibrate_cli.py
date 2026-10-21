"""Command-line entry for the calibration (feedback) loop.

Join designs to measured binding results, score how predictive each metric was,
and emit suggested scoring weights plus figures.

Example:
    python -m binder_triage.calibrate_cli \
        --target config/targets/egfr.yaml \
        --candidates data/candidates_demo.csv \
        --results data/results_demo.csv \
        --outdir outputs/calibration
"""
from __future__ import annotations

import argparse
from pathlib import Path

from .calibration import calibrate, load_results
from .io import load_candidates
from .report import (
    plot_calibration_auroc,
    plot_weight_shift,
    write_calibration_markdown,
)
from .schema import Target


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Calibrate metric weights against assay data.")
    ap.add_argument("--target", required=True)
    ap.add_argument("--candidates", required=True)
    ap.add_argument("--results", required=True, help="CSV: design_id, binds and/or kd_nm")
    ap.add_argument("--outdir", default="outputs/calibration")
    args = ap.parse_args(argv)

    target = Target.from_yaml(args.target)
    candidates = load_candidates(args.candidates, target)
    results = load_results(args.results)
    print(f"Loaded {len(candidates)} designs and {len(results)} assay results.")

    report = calibrate(candidates, results, target)

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    figs = []
    plot_calibration_auroc(report, outdir / "calibration_auroc.png")
    figs.append("calibration_auroc.png")
    plot_weight_shift(report, outdir / "weight_shift.png")
    figs.append("weight_shift.png")
    write_calibration_markdown(report, outdir / "calibration_report.md", figs)
    (outdir / "suggested_weights.yaml").write_text(report.weight_yaml() + "\n")

    print(f"  matched designs: {report.n_matched}  (binders: {report.n_binders})")
    print("  metric            AUROC   weight -> suggested")
    for m in report.metrics:
        print(f"  {m.name:<18}{m.auroc:5.2f}   {m.current_weight:4.2f} -> {m.suggested_weight:4.2f}")
    print(f"Wrote calibration report + figures to {outdir}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
