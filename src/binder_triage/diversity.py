"""Stage 3 of triage: sequence-diversity-aware selection.

A ranked list is not yet a plate. The top 96 designs by score are often minor
variations on the same two or three backbones -- if any one of them fails in the
wet lab, they likely all fail, and you have wasted a plate. Real campaigns
therefore impose diversity: explore many distinct solutions rather than drilling
into one.

We use greedy clustering by sequence identity. Walking the ranked list from best
to worst, each design either joins an existing cluster (if similar enough to that
cluster's representative) or starts a new one. We then fill the plate by taking
designs in score order but capping how many may come from any single cluster.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .scoring import ScoredCandidate


def _kmers(seq: str, k: int = 3) -> set[str]:
    return {seq[i : i + k] for i in range(len(seq) - k + 1)} if len(seq) >= k else {seq}


def sequence_identity(a: str, b: str) -> float:
    """Similarity in [0, 1].

    Equal-length sequences use positional identity (the standard definition).
    Unequal lengths fall back to k-mer Jaccard, a cheap alignment-free proxy
    that still clusters obvious relatives together.
    """
    if a == b:
        return 1.0
    if len(a) == len(b):
        matches = sum(x == y for x, y in zip(a, b))
        return matches / len(a)
    ka, kb = _kmers(a), _kmers(b)
    if not ka or not kb:
        return 0.0
    return len(ka & kb) / len(ka | kb)


@dataclass
class Cluster:
    representative: ScoredCandidate      # highest-scoring member (set first)
    members: list[ScoredCandidate] = field(default_factory=list)


def cluster_by_identity(
    ranked: list[ScoredCandidate], identity_cutoff: float
) -> list[Cluster]:
    """Greedy single-linkage-ish clustering against cluster representatives."""
    clusters: list[Cluster] = []
    for sc in ranked:  # already sorted best-first, so reps are the best members
        placed = False
        for cl in clusters:
            if sequence_identity(
                sc.candidate.sequence, cl.representative.candidate.sequence
            ) >= identity_cutoff:
                cl.members.append(sc)
                placed = True
                break
        if not placed:
            clusters.append(Cluster(representative=sc, members=[sc]))
    return clusters


@dataclass
class SelectionResult:
    selected: list[ScoredCandidate]
    clusters: list[Cluster]
    bumped: list[ScoredCandidate]  # would-be picks skipped for diversity capping


def select_plate(
    ranked: list[ScoredCandidate],
    plate_size: int,
    identity_cutoff: float,
    max_per_cluster: int,
) -> SelectionResult:
    """Pick up to ``plate_size`` designs, capping near-duplicates per cluster."""
    clusters = cluster_by_identity(ranked, identity_cutoff)

    # Map each candidate to its cluster index for O(1) cap bookkeeping.
    cluster_of: dict[int, int] = {}
    for ci, cl in enumerate(clusters):
        for m in cl.members:
            cluster_of[id(m)] = ci

    taken_per_cluster = [0] * len(clusters)
    selected: list[ScoredCandidate] = []
    bumped: list[ScoredCandidate] = []

    for sc in ranked:  # score order
        if len(selected) >= plate_size:
            break
        ci = cluster_of[id(sc)]
        if taken_per_cluster[ci] >= max_per_cluster:
            bumped.append(sc)
            continue
        selected.append(sc)
        taken_per_cluster[ci] += 1

    return SelectionResult(selected=selected, clusters=clusters, bumped=bumped)
