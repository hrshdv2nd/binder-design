#!/usr/bin/env python3
"""Synthesize an 'assay results' file for the demo plate.

Stands in for wet-lab data (which you would really get from Adaptyv's lab or a
CRO -- see docs/04_calibration.md). A hidden 'truth' model decides each design's
binding from its own metrics, but with weights DIFFERENT from the target
config's guessed weights, so the calibration step has something real to correct:

  truth leans hardest on interface confidence (pae_interaction, ipTM), only
  modestly on ddG, and ignores shape-complementarity / rmsd / mpnn entirely --
  whereas egfr.yaml starts out over-trusting ddG. Calibration should recover
  this and down-weight ddG.

A chunk of designs are 'nulls' that don't bind no matter how good they look --
the in-silico false positives every real campaign hits.

Run (after generate_demo_data.py):
    python scripts/generate_demo_results.py --seed 11 --out data/results_demo.csv
"""
from __future__ import annotations

import argparse
import csv
import math
import random

# Hidden truth: how much each metric REALLY drives binding (oriented so higher
# metric value after orientation = more binder-like). Deliberately unlike the
# config's scoring weights.
TRUTH = {
    "pae_interaction": 1.7,   # strongest real signal
    "iptm": 1.3,
    "ddg": 0.7,               # matters, but less than the config assumes
    "interface_sasa": 0.4,
    "plddt": 0.3,
    "shape_complementarity": 0.0,  # config weights these; truth says noise
    "rmsd_design": 0.0,
    "mpnn_score": 0.0,
}
# Which way is "better" for each metric (to orient before combining).
HIGHER_BETTER = {"iptm", "interface_sasa", "plddt", "shape_complementarity"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", default="data/candidates_demo.csv")
    ap.add_argument("--out", default="data/results_demo.csv")
    ap.add_argument("--seed", type=int, default=11)
    ap.add_argument("--null-rate", type=float, default=0.45,
                    help="fraction that never bind regardless of metrics")
    args = ap.parse_args()
    rng = random.Random(args.seed)

    rows = list(csv.DictReader(open(args.candidates)))
    cols = {m: [float(r[m]) for r in rows] for m in TRUTH}
    means = {m: sum(v) / len(v) for m, v in cols.items()}
    stds = {m: (sum((x - means[m]) ** 2 for x in v) / len(v)) ** 0.5 or 1.0
            for m, v in cols.items()}

    out = []
    n_binders = 0
    for r in rows:
        # oriented z-score per metric -> weighted hidden quality
        q = 0.0
        for m, w in TRUTH.items():
            if w == 0:
                continue
            z = (float(r[m]) - means[m]) / stds[m]
            if m not in HIGHER_BETTER:   # lower-is-better -> flip
                z = -z
            q += w * z
        q += rng.gauss(0, 1.1)           # irreducible assay + biology noise

        is_null = rng.random() < args.null_rate
        if is_null:
            binds = False
            kd_nm = ""
        else:
            # map quality -> pKd (higher q = tighter). ~6-10 range -> uM..0.1nM
            pkd = 6.4 + 0.85 * q
            kd_nm = 10 ** (9 - pkd)
            binds = kd_nm <= 1000.0       # 1 uM detection cutoff
            if not binds:
                kd_nm = ""                # below detection -> no quantified Kd
            else:
                kd_nm = round(kd_nm, 3)
                n_binders += 1

        out.append({
            "design_id": r["design_id"],
            "binds": 1 if binds else 0,
            "kd_nm": kd_nm,
        })

    with open(args.out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["design_id", "binds", "kd_nm"])
        w.writeheader()
        w.writerows(out)
    print(f"Wrote {len(out)} results to {args.out} "
          f"({n_binders} binders, {100*n_binders/len(out):.0f}%)")


if __name__ == "__main__":
    main()
