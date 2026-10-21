"""binder_triage -- an in-silico triage engine for protein binder design.

Turns the raw output of binder-design models (RFdiffusion backbones scored by
AlphaFold2/ESMFold, ProteinMPNN and PyRosetta) into a ranked, diversified
shortlist of lead candidates to validate in the wet lab.

This is the "triage" box in the standard biotech workflow:

    generate  ->  predict / score  ->  TRIAGE  ->  wet-lab validation
"""

from .schema import Target, MetricSpec, Candidate
from .triage import TriageEngine, TriageResult

__all__ = [
    "Target",
    "MetricSpec",
    "Candidate",
    "TriageEngine",
    "TriageResult",
]

__version__ = "0.1.0"
