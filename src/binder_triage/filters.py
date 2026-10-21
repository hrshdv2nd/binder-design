"""Stage 1 of triage: hard gatekeeping filters.

Before anything is ranked, each design must clear every metric's hard threshold
and carry no developability liabilities. This mirrors how a real campaign works:
a design with a beautiful ddG but a pae_interaction of 25 is almost certainly a
false positive and should never reach a plate, no matter how it scores.

Filtering is kept separate from scoring on purpose -- gates answer "is this
design admissible?" (yes/no), scoring answers "among the admissible, which are
best?" (ranking). Conflating the two hides why a design was dropped.
"""
from __future__ import annotations

from dataclasses import dataclass

from .schema import Candidate, Target


@dataclass
class GateResult:
    candidate: Candidate
    passed: bool
    failed_metrics: list[str]      # metric names whose hard threshold was missed
    tripped_liabilities: list[str] # liability flags that were set

    @property
    def reason(self) -> str:
        if self.passed:
            return "pass"
        bits = []
        if self.failed_metrics:
            bits.append("metrics:" + ",".join(self.failed_metrics))
        if self.tripped_liabilities:
            bits.append("liabilities:" + ",".join(self.tripped_liabilities))
        return "; ".join(bits)


def gate(candidate: Candidate, target: Target) -> GateResult:
    """Apply all hard filters to a single candidate."""
    failed_metrics: list[str] = []
    for name, spec in target.active_metrics().items():
        if name not in candidate.metrics:
            # A missing required metric is itself a failure -- we cannot vouch
            # for a design we have not fully scored.
            failed_metrics.append(f"{name}(missing)")
            continue
        if not spec.passes_gate(candidate.metrics[name]):
            failed_metrics.append(name)

    tripped = [
        flag for flag in target.liabilities
        if candidate.liabilities.get(flag, False)
    ]

    passed = not failed_metrics and not tripped
    return GateResult(candidate, passed, failed_metrics, tripped)


def gate_all(candidates: list[Candidate], target: Target) -> list[GateResult]:
    return [gate(c, target) for c in candidates]
