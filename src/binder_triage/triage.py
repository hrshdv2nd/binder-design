"""The triage pipeline: gate -> score -> diversify -> select.

This is the public entry point. Hand it a list of ``Candidate`` objects and a
``Target`` and it returns a ``TriageResult`` describing the whole funnel: what
came in, what was rejected and why, how the survivors ranked, and which designs
should go on the plate.
"""
from __future__ import annotations

from dataclasses import dataclass

from .diversity import SelectionResult, select_plate
from .filters import GateResult, gate_all
from .schema import Candidate, Target
from .scoring import ScoredCandidate, score


@dataclass
class TriageResult:
    target: Target
    gate_results: list[GateResult]
    ranked: list[ScoredCandidate]         # admissible designs, best first
    selection: SelectionResult

    # -- funnel accounting ------------------------------------------------- #
    @property
    def n_input(self) -> int:
        return len(self.gate_results)

    @property
    def n_passed_gate(self) -> int:
        return sum(g.passed for g in self.gate_results)

    @property
    def n_selected(self) -> int:
        return len(self.selection.selected)

    @property
    def n_clusters(self) -> int:
        return len(self.selection.clusters)

    def rejection_breakdown(self) -> dict[str, int]:
        """Count how many designs each gate was responsible for dropping."""
        counts: dict[str, int] = {}
        for g in self.gate_results:
            if g.passed:
                continue
            for m in g.failed_metrics:
                counts[m] = counts.get(m, 0) + 1
            for lab in g.tripped_liabilities:
                counts[f"liability:{lab}"] = counts.get(f"liability:{lab}", 0) + 1
        return dict(sorted(counts.items(), key=lambda kv: kv[1], reverse=True))


class TriageEngine:
    def __init__(self, target: Target):
        self.target = target

    def run(self, candidates: list[Candidate]) -> TriageResult:
        # Stage 1 -- hard gates.
        gate_results = gate_all(candidates, self.target)
        survivors = [g.candidate for g in gate_results if g.passed]

        # Stage 2 -- composite scoring / ranking.
        ranked: list[ScoredCandidate] = score(survivors, self.target)

        # Stage 3 -- diversity-aware plate selection.
        sel_cfg = self.target.selection
        selection = select_plate(
            ranked,
            plate_size=int(sel_cfg.get("plate_size", 96)),
            identity_cutoff=float(sel_cfg.get("diversity_identity_cutoff", 0.9)),
            max_per_cluster=int(sel_cfg.get("max_per_cluster", 3)),
        )

        return TriageResult(
            target=self.target,
            gate_results=gate_results,
            ranked=ranked,
            selection=selection,
        )
