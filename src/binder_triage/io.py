"""Loading candidate designs from the kind of CSV a design pipeline emits.

Expected columns:
  design_id, sequence, method, <one column per metric>, liab_<flag> (0/1)

Any column matching a metric name in the target config is read as that metric.
Any column prefixed ``liab_`` is read as a developability liability flag.
Unknown columns are ignored, so real pipeline dumps with extra bookkeeping
columns load without complaint.
"""
from __future__ import annotations

import csv
from pathlib import Path

from .schema import Candidate, Target


def load_candidates(path: str | Path, target: Target) -> list[Candidate]:
    metric_names = set(target.metrics.keys())
    candidates: list[Candidate] = []

    with open(path, newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            metrics: dict[str, float] = {}
            liabilities: dict[str, bool] = {}
            for col, val in row.items():
                if col in metric_names:
                    if val not in ("", None):
                        metrics[col] = float(val)
                elif col.startswith("liab_"):
                    flag = col[len("liab_"):]
                    liabilities[flag] = str(val).strip() in ("1", "True", "true", "yes")
            candidates.append(
                Candidate(
                    design_id=row["design_id"],
                    sequence=row.get("sequence", ""),
                    metrics=metrics,
                    liabilities=liabilities,
                    method=row.get("method", ""),
                )
            )
    return candidates
