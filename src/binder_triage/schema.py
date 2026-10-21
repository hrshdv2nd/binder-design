"""Data model for targets, metric specifications and candidate designs.

Kept deliberately dependency-light (dataclasses + PyYAML) so the schema is easy
to read and reason about -- it is the contract between the design models that
produce candidates and the triage engine that consumes them.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml


# --------------------------------------------------------------------------- #
# Metric specification
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class MetricSpec:
    """How one design metric should be interpreted during triage.

    A metric is both a *gate* (hard_min / hard_max reject failing designs) and,
    if ``weight > 0``, a *scored* dimension that feeds the composite rank.
    """

    name: str
    about: str
    direction: str  # "higher" or "lower" -- which way is better
    weight: float = 0.0
    hard_min: Optional[float] = None
    hard_max: Optional[float] = None
    unit: str = ""
    conditional_only: bool = False

    def __post_init__(self) -> None:
        if self.direction not in ("higher", "lower"):
            raise ValueError(
                f"metric {self.name!r}: direction must be 'higher' or 'lower', "
                f"got {self.direction!r}"
            )

    def passes_gate(self, value: float) -> bool:
        """True if ``value`` clears this metric's hard threshold(s)."""
        if self.hard_min is not None and value < self.hard_min:
            return False
        if self.hard_max is not None and value > self.hard_max:
            return False
        return True

    def orient(self, value: float) -> float:
        """Return the value flipped so that *larger is always better*.

        Lets the scorer treat every metric uniformly after this call.
        """
        return value if self.direction == "higher" else -value


# --------------------------------------------------------------------------- #
# Target
# --------------------------------------------------------------------------- #
@dataclass
class Target:
    """A design target plus everything the triage engine needs about it."""

    name: str
    full_name: str
    uniprot: str
    metrics: dict[str, MetricSpec]
    liabilities: list[str] = field(default_factory=list)
    reference_structures: list[dict] = field(default_factory=list)
    epitope: dict = field(default_factory=dict)
    reference_binder: dict = field(default_factory=dict)
    conditional: dict = field(default_factory=dict)
    selection: dict = field(default_factory=dict)

    @property
    def is_conditional(self) -> bool:
        return bool(self.conditional.get("enabled"))

    def active_metrics(self) -> dict[str, MetricSpec]:
        """Metrics that apply to this target.

        Conditional-only metrics (e.g. pH selectivity) are dropped when the
        target is not a conditional-binding challenge.
        """
        out = {}
        for name, spec in self.metrics.items():
            if spec.conditional_only and not self.is_conditional:
                continue
            out[name] = spec
        return out

    @classmethod
    def from_yaml(cls, path: str | Path) -> "Target":
        with open(path) as fh:
            raw = yaml.safe_load(fh)

        metrics: dict[str, MetricSpec] = {}
        for mname, mraw in raw.get("metrics", {}).items():
            metrics[mname] = MetricSpec(
                name=mname,
                about=mraw.get("about", ""),
                direction=mraw["direction"],
                weight=float(mraw.get("weight", 0.0)),
                hard_min=mraw.get("hard_min"),
                hard_max=mraw.get("hard_max"),
                unit=mraw.get("unit", ""),
                conditional_only=bool(mraw.get("conditional_only", False)),
            )

        return cls(
            name=raw["name"],
            full_name=raw.get("full_name", raw["name"]),
            uniprot=raw.get("uniprot", ""),
            metrics=metrics,
            liabilities=raw.get("liabilities", []),
            reference_structures=raw.get("reference_structures", []),
            epitope=raw.get("epitope", {}),
            reference_binder=raw.get("reference_binder", {}),
            conditional=raw.get("conditional", {}),
            selection=raw.get("selection", {}),
        )


# --------------------------------------------------------------------------- #
# Candidate
# --------------------------------------------------------------------------- #
@dataclass
class Candidate:
    """One designed binder and the model outputs attached to it."""

    design_id: str
    sequence: str
    metrics: dict[str, float]
    liabilities: dict[str, bool] = field(default_factory=dict)
    method: str = ""  # e.g. "RFdiffusion+ProteinMPNN", "BindCraft"

    @property
    def length(self) -> int:
        return len(self.sequence)
