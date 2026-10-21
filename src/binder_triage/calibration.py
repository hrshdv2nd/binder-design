"""Close the loop: calibrate metric trust against measured binding data.

The triage weights and gates in a target config start as a *hypothesis* about
which in-silico metrics predict real binding. Once an assay returns labels --
Kd values, or a simple binds / doesn't-bind call -- you can check that
hypothesis and correct it:

    1. For each metric, measure how well it actually separated binders from
       non-binders on THIS target (AUROC for the binary question; Spearman
       correlation with pKd when affinities are available).
    2. Propose new scoring weights proportional to that measured discrimination,
       keeping the overall scale so before/after are comparable.
    3. You paste the new weights into the target YAML and the next shortlist is
       ranked by what demonstrably worked, not by what you guessed.

No external ML dependencies: AUROC (Mann-Whitney) and Spearman are computed from
ranks with numpy. The point is transparency -- every number here is one you can
re-derive by hand.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .schema import Candidate, Target


# --------------------------------------------------------------------------- #
# Measured results
# --------------------------------------------------------------------------- #
@dataclass
class AssayResult:
    design_id: str
    binds: bool                 # the outcome we calibrate against
    kd_nm: float | None = None  # affinity when the assay quantified it


def load_results(path: str | Path, binder_kd_threshold_nm: float = 1000.0) -> dict[str, AssayResult]:
    """Read an assay results CSV into a {design_id: AssayResult} map.

    Accepts either a ``binds`` column (0/1, true/false, yes/no) or a ``kd_nm``
    column (a design counts as a binder if Kd <= ``binder_kd_threshold_nm``),
    or both. This is the one place the loop touches wet-lab data; everything
    else is derived from it.
    """
    import csv

    out: dict[str, AssayResult] = {}
    with open(path, newline="") as fh:
        for row in csv.DictReader(fh):
            did = row["design_id"]
            kd = None
            if row.get("kd_nm") not in (None, ""):
                kd = float(row["kd_nm"])
            if row.get("binds") not in (None, ""):
                binds = str(row["binds"]).strip().lower() in ("1", "true", "yes", "y")
            elif kd is not None:
                binds = kd <= binder_kd_threshold_nm
            else:
                continue  # no usable outcome in this row
            out[did] = AssayResult(design_id=did, binds=binds, kd_nm=kd)
    return out


# --------------------------------------------------------------------------- #
# Rank statistics (no scipy)
# --------------------------------------------------------------------------- #
def _ranks(x: np.ndarray) -> np.ndarray:
    """Average ranks (ties share the mean rank), as Spearman/AUROC need."""
    order = np.argsort(x, kind="mergesort")
    ranks = np.empty(len(x), dtype=float)
    ranks[order] = np.arange(1, len(x) + 1)
    # resolve ties to their average rank
    _, inv, counts = np.unique(x, return_inverse=True, return_counts=True)
    sums = np.zeros(len(counts))
    np.add.at(sums, inv, ranks)
    return (sums / counts)[inv]


def auroc(values: np.ndarray, labels: np.ndarray) -> float:
    """Area under ROC = P(value(binder) > value(non-binder)).

    ``values`` must already be oriented so larger = more binder-like.
    0.5 means no discrimination; <0.5 means the metric points the wrong way.
    """
    pos = labels == 1
    n_pos, n_neg = int(pos.sum()), int((~pos).sum())
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    r = _ranks(values)
    return (r[pos].sum() - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg)


def spearman(a: np.ndarray, b: np.ndarray) -> float:
    if len(a) < 3:
        return float("nan")
    ra, rb = _ranks(a), _ranks(b)
    ra, rb = ra - ra.mean(), rb - rb.mean()
    denom = np.sqrt((ra**2).sum() * (rb**2).sum())
    return float((ra * rb).sum() / denom) if denom else float("nan")


# --------------------------------------------------------------------------- #
# Calibration
# --------------------------------------------------------------------------- #
@dataclass
class MetricCalibration:
    name: str
    auroc: float               # oriented so >0.5 = predictive
    discrimination: float      # 2*|auroc-0.5| in [0,1]; 0 = useless
    spearman_pkd: float        # vs pKd among quantified binders (nan if n/a)
    n: int
    current_weight: float
    suggested_weight: float


@dataclass
class CalibrationReport:
    target_name: str
    n_matched: int
    n_binders: int
    metrics: list[MetricCalibration]  # scored metrics, most discriminative first

    def weight_yaml(self) -> str:
        """A ready-to-paste `weight:` update for the target config."""
        lines = ["# suggested scoring weights from calibration",
                 "# (paste each into the matching metric in the target YAML)"]
        for m in self.metrics:
            lines.append(f"{m.name}: {m.suggested_weight:.2f}   "
                         f"# was {m.current_weight:.2f}, AUROC {m.auroc:.2f}")
        return "\n".join(lines)


def calibrate(
    candidates: list[Candidate],
    results: dict[str, AssayResult],
    target: Target,
) -> CalibrationReport:
    # Join designs to their measured outcome.
    matched = [(c, results[c.design_id]) for c in candidates if c.design_id in results]
    if not matched:
        raise ValueError("no candidates matched the results file by design_id")

    labels = np.array([1 if r.binds else 0 for _, r in matched])
    scored = {n: s for n, s in target.active_metrics().items() if s.weight > 0}

    cals: list[MetricCalibration] = []
    for name, spec in scored.items():
        vals = np.array([c.metrics.get(name, np.nan) for c, _ in matched], dtype=float)
        ok = ~np.isnan(vals)
        if ok.sum() < 3:
            continue
        oriented = spec.orient(vals[ok])          # larger = better = more binder-like
        a = auroc(oriented, labels[ok])
        disc = 2 * abs(a - 0.5) if a == a else 0.0  # NaN-safe

        # Spearman vs pKd among quantified binders only.
        pkd_pairs = [
            (c.metrics.get(name), -np.log10(r.kd_nm * 1e-9))
            for c, r in matched
            if r.binds and r.kd_nm and c.metrics.get(name) is not None
        ]
        if len(pkd_pairs) >= 3:
            mv = spec.orient(np.array([p[0] for p in pkd_pairs], dtype=float))
            sp = spearman(mv, np.array([p[1] for p in pkd_pairs]))
        else:
            sp = float("nan")

        cals.append(MetricCalibration(
            name=name, auroc=a, discrimination=disc, spearman_pkd=sp,
            n=int(ok.sum()), current_weight=spec.weight, suggested_weight=0.0,
        ))

    # Suggested weights: proportional to discrimination, rescaled to preserve
    # the current total weight so the composite score keeps its familiar range.
    # A metric that showed no signal (AUROC ~0.5) is driven toward zero.
    total_current = sum(c.current_weight for c in cals)
    total_disc = sum(c.discrimination for c in cals)
    for c in cals:
        if total_disc > 0:
            c.suggested_weight = round(total_current * c.discrimination / total_disc, 2)

    cals.sort(key=lambda c: c.discrimination, reverse=True)
    return CalibrationReport(
        target_name=target.name,
        n_matched=len(matched),
        n_binders=int(labels.sum()),
        metrics=cals,
    )
