"""Stage 2 of triage: composite scoring of the admissible designs.

Each scored metric is turned into a robust z-score (centred on the median,
scaled by the median absolute deviation so a few outliers don't dominate),
oriented so that higher is always better, then combined with the per-metric
weights from the target config. The result is one number per design that is
comparable across metrics measured in wildly different units (REU vs Angstrom
vs a 0-1 probability).

Why z-scores instead of raw values: ddG lives around -30 REU, pae_interaction
around 5 A, iptm around 0.7. Summing them raw would let ddG swamp everything.
Standardising each metric puts them on the same footing; the weights then encode
*how much we trust each metric*, which is the real domain knowledge.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .schema import Candidate, Target


@dataclass
class ScoredCandidate:
    candidate: Candidate
    score: float                         # final weighted composite
    contributions: dict[str, float]      # per-metric weighted z contribution


def _robust_z(values: np.ndarray) -> np.ndarray:
    """Median/MAD z-score. Falls back to 0 when a metric has no spread."""
    med = np.median(values)
    mad = np.median(np.abs(values - med))
    if mad == 0:
        # No variation (or <=2 points): nothing to discriminate on.
        std = values.std()
        if std == 0:
            return np.zeros_like(values)
        return (values - values.mean()) / std
    # 1.4826 scales MAD to be a consistent estimator of std for normal data.
    return (values - med) / (1.4826 * mad)


def score(candidates: list[Candidate], target: Target) -> list[ScoredCandidate]:
    """Rank the admissible candidates by weighted composite score (desc)."""
    if not candidates:
        return []

    scored_metrics = {
        name: spec
        for name, spec in target.active_metrics().items()
        if spec.weight > 0
    }

    # Build an oriented value matrix: rows = candidates, cols = metrics,
    # every column already flipped so "larger is better".
    oriented: dict[str, np.ndarray] = {}
    for name, spec in scored_metrics.items():
        raw = np.array([c.metrics[name] for c in candidates], dtype=float)
        oriented[name] = spec.orient(raw)

    # z-score each metric column independently.
    zcols = {name: _robust_z(vals) for name, vals in oriented.items()}

    results: list[ScoredCandidate] = []
    for i, cand in enumerate(candidates):
        contributions = {
            name: scored_metrics[name].weight * zcols[name][i]
            for name in scored_metrics
        }
        total = float(sum(contributions.values()))
        results.append(ScoredCandidate(cand, total, contributions))

    results.sort(key=lambda sc: sc.score, reverse=True)
    return results
