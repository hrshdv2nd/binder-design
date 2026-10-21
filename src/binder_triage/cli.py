"""Command-line entry point for the triage pipeline.

Example:
    python -m binder_triage.cli \
        --target config/targets/egfr.yaml \
        --candidates data/candidates_demo.csv \
        --outdir outputs
"""
from __future__ import annotations

import argparse
from pathlib import Path

from .io import load_candidates
from .report import (
    plot_contributions,
    plot_funnel,
    plot_landscape,
    plot_rejections,
    write_markdown,
    write_plate_csv,
)
from .schema import Target
from .triage import TriageEngine


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Triage protein-binder designs.")
    ap.add_argument("--target", required=True, help="path to target YAML")
    ap.add_argument("--candidates", required=True, help="path to candidates CSV")
    ap.add_argument("--outdir", default="outputs", help="where to write results")
    args = ap.parse_args(argv)

    target = Target.from_yaml(args.target)
    candidates = load_candidates(args.candidates, target)
    print(f"Loaded {len(candidates)} candidate designs for target {target.name}.")

    result = TriageEngine(target).run(candidates)

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    figures = []
    plot_funnel(result, outdir / "funnel.png"); figures.append("funnel.png")
    plot_rejections(result, outdir / "rejections.png"); figures.append("rejections.png")
    plot_landscape(result, outdir / "landscape.png"); figures.append("landscape.png")
    plot_contributions(result, outdir / "contributions.png"); figures.append("contributions.png")

    write_plate_csv(result, outdir / "selected_plate.csv")
    write_markdown(result, outdir / "report.md", figures)

    print(f"  input:         {result.n_input}")
    print(f"  passed gates:  {result.n_passed_gate}")
    print(f"  clusters:      {result.n_clusters}")
    print(f"  selected:      {result.n_selected}")
    print(f"Wrote report + figures + plate CSV to {outdir}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
