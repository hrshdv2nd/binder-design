"""Tests for the triage engine. Run with:  python -m pytest -q  (or unittest)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from binder_triage.schema import Candidate, MetricSpec, Target  # noqa: E402
from binder_triage.filters import gate  # noqa: E402
from binder_triage.diversity import sequence_identity, select_plate  # noqa: E402
from binder_triage.scoring import score  # noqa: E402
from binder_triage.triage import TriageEngine  # noqa: E402


def make_target(**overrides):
    metrics = {
        "pae_interaction": MetricSpec("pae_interaction", "", "lower",
                                      weight=2.0, hard_max=10.0),
        "ddg": MetricSpec("ddg", "", "lower", weight=1.0, hard_max=-20.0),
        "plddt": MetricSpec("plddt", "", "higher", weight=1.0, hard_min=80),
    }
    cfg = dict(
        name="TEST", full_name="Test target", uniprot="X",
        metrics=metrics, liabilities=["free_cysteine"],
        selection={"plate_size": 3, "diversity_identity_cutoff": 0.9,
                   "max_per_cluster": 1},
    )
    cfg.update(overrides)
    return Target(**cfg)


def cand(cid, seq, pae, ddg, plddt, cys=False):
    return Candidate(
        design_id=cid, sequence=seq,
        metrics={"pae_interaction": pae, "ddg": ddg, "plddt": plddt},
        liabilities={"free_cysteine": cys},
    )


class TestGate(unittest.TestCase):
    def test_pass(self):
        g = gate(cand("a", "AAAA", 5.0, -30, 90), make_target())
        self.assertTrue(g.passed)
        self.assertEqual(g.failed_metrics, [])

    def test_fail_hard_max(self):
        g = gate(cand("b", "AAAA", 25.0, -30, 90), make_target())
        self.assertFalse(g.passed)
        self.assertIn("pae_interaction", g.failed_metrics)

    def test_fail_hard_min(self):
        g = gate(cand("c", "AAAA", 5.0, -30, 50), make_target())
        self.assertFalse(g.passed)
        self.assertIn("plddt", g.failed_metrics)

    def test_liability_rejects(self):
        g = gate(cand("d", "AAAA", 5.0, -30, 90, cys=True), make_target())
        self.assertFalse(g.passed)
        self.assertIn("free_cysteine", g.tripped_liabilities)

    def test_missing_metric_fails(self):
        c = Candidate("e", "AAAA", {"pae_interaction": 5.0})  # no ddg/plddt
        g = gate(c, make_target())
        self.assertFalse(g.passed)


class TestScoring(unittest.TestCase):
    def test_better_designs_rank_higher(self):
        cands = [
            cand("good", "AAAA", 3.0, -45, 95),
            cand("mid", "CCCC", 7.0, -30, 85),
            cand("weak", "DDDD", 9.5, -21, 81),
        ]
        ranked = score(cands, make_target())
        self.assertEqual([r.candidate.design_id for r in ranked],
                         ["good", "mid", "weak"])

    def test_empty(self):
        self.assertEqual(score([], make_target()), [])


class TestDiversity(unittest.TestCase):
    def test_identity_identical(self):
        self.assertEqual(sequence_identity("ABCDEF", "ABCDEF"), 1.0)

    def test_identity_half(self):
        self.assertAlmostEqual(sequence_identity("AAAA", "AABB"), 0.5)

    def test_cap_per_cluster(self):
        # Three near-identical top designs; cap of 1 should keep only the best.
        cands = [
            cand("x1", "AAAAAAAAAA", 3.0, -50, 95),
            cand("x2", "AAAAAAAAAB", 3.1, -49, 95),  # ~90% identical to x1
            cand("y1", "QQQQQQQQQQ", 4.0, -40, 90),
        ]
        ranked = score(cands, make_target())
        sel = select_plate(ranked, plate_size=3, identity_cutoff=0.9,
                           max_per_cluster=1)
        ids = {s.candidate.design_id for s in sel.selected}
        self.assertIn("y1", ids)
        # x1 and x2 are one cluster capped at 1 -> only one of them selected.
        self.assertEqual(len({"x1", "x2"} & ids), 1)


class TestEngineFunnel(unittest.TestCase):
    def test_end_to_end(self):
        cands = [
            cand("keep1", "MKMKMKMKMK", 3.0, -45, 95),
            cand("keep2", "WYWYWYWYWY", 4.0, -35, 88),
            cand("drop_pae", "AAAAAAAAAA", 22.0, -45, 95),
            cand("drop_cys", "CECECECECE", 3.0, -45, 95, cys=True),
        ]
        result = TriageEngine(make_target()).run(cands)
        self.assertEqual(result.n_input, 4)
        self.assertEqual(result.n_passed_gate, 2)
        self.assertLessEqual(result.n_selected, 2)
        bd = result.rejection_breakdown()
        self.assertEqual(bd.get("pae_interaction"), 1)
        self.assertEqual(bd.get("liability:free_cysteine"), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
