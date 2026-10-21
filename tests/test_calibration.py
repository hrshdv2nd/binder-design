"""Tests for the calibration (feedback-loop) module."""
import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from binder_triage.calibration import (  # noqa: E402
    AssayResult, auroc, calibrate, spearman,
)
from binder_triage.schema import Candidate, MetricSpec, Target  # noqa: E402


class TestRankStats(unittest.TestCase):
    def test_auroc_perfect(self):
        # binders all score above non-binders -> AUROC 1.0
        vals = np.array([1.0, 2.0, 3.0, 4.0])
        labels = np.array([0, 0, 1, 1])
        self.assertAlmostEqual(auroc(vals, labels), 1.0)

    def test_auroc_inverted(self):
        vals = np.array([4.0, 3.0, 2.0, 1.0])
        labels = np.array([0, 0, 1, 1])
        self.assertAlmostEqual(auroc(vals, labels), 0.0)

    def test_auroc_chance(self):
        # binders at the extremes (1,4), non-binders in the middle (2,3):
        # pairs win and lose equally -> 0.5
        vals = np.array([1.0, 2.0, 3.0, 4.0])
        labels = np.array([1, 0, 0, 1])
        self.assertAlmostEqual(auroc(vals, labels), 0.5)

    def test_spearman_monotonic(self):
        a = np.array([1.0, 2, 3, 4, 5])
        b = np.array([2.0, 4, 6, 8, 10])   # perfectly monotonic
        self.assertAlmostEqual(spearman(a, b), 1.0)
        self.assertAlmostEqual(spearman(a, -b), -1.0)


def _target():
    metrics = {
        "good": MetricSpec("good", "", "higher", weight=1.0),
        "noise": MetricSpec("noise", "", "higher", weight=1.0),
    }
    return Target(name="T", full_name="T", uniprot="X", metrics=metrics)


class TestCalibrate(unittest.TestCase):
    def test_recovers_predictive_metric(self):
        # 'good' tracks binding; 'noise' is constant -> no discrimination.
        cands, results = [], {}
        for i in range(40):
            binds = i % 2 == 0
            cands.append(Candidate(
                f"D{i}", "AAAA",
                metrics={"good": (10.0 if binds else 0.0), "noise": 1.0},
            ))
            results[f"D{i}"] = AssayResult(f"D{i}", binds=binds)

        report = calibrate(cands, results, _target())
        by = {m.name: m for m in report.metrics}
        self.assertAlmostEqual(by["good"].auroc, 1.0, places=5)
        # the perfectly predictive metric should take essentially all the weight
        self.assertGreater(by["good"].suggested_weight, by["noise"].suggested_weight)
        self.assertAlmostEqual(by["noise"].suggested_weight, 0.0, places=2)

    def test_total_weight_preserved(self):
        cands, results = [], {}
        for i in range(30):
            binds = i % 3 == 0
            cands.append(Candidate(
                f"D{i}", "AAAA",
                metrics={"good": float(i), "noise": float((i * 7) % 5)},
            ))
            results[f"D{i}"] = AssayResult(f"D{i}", binds=binds)
        report = calibrate(cands, results, _target())
        total_before = sum(m.current_weight for m in report.metrics)
        total_after = sum(m.suggested_weight for m in report.metrics)
        # rescaling preserves the overall weight budget (within rounding)
        self.assertAlmostEqual(total_before, total_after, delta=0.05)

    def test_requires_matches(self):
        with self.assertRaises(ValueError):
            calibrate([Candidate("Z", "AA", {"good": 1.0, "noise": 1.0})],
                      {"OTHER": AssayResult("OTHER", binds=True)}, _target())


if __name__ == "__main__":
    unittest.main(verbosity=2)
