#!/usr/bin/env python3
"""Generate a realistic synthetic set of binder designs for the demo.

These numbers are *synthetic* -- no wet-lab data is implied -- but the
distributions and correlations are modelled on what real de novo binder
campaigns (RFdiffusion/BindCraft -> ProteinMPNN -> AlphaFold2 -> PyRosetta)
produce: most designs are junk, a minority clear the gates, and the good
in-silico metrics are correlated through a shared latent "quality".

The design families (shared backbones with point mutations) exist so that the
diversity-selection stage has something real to cluster.

Run:
    python scripts/generate_demo_data.py --n 600 --out data/candidates_demo.csv
"""
from __future__ import annotations

import argparse
import csv
import random

AA = "ACDEFGHIKLMNPQRSTVWY"


def random_seq(length: int, rng: random.Random) -> str:
    return "".join(rng.choice(AA) for _ in range(length))


def mutate(seq: str, rate: float, rng: random.Random) -> str:
    chars = list(seq)
    for i in range(len(chars)):
        if rng.random() < rate:
            chars[i] = rng.choice(AA)
    return "".join(chars)


def has_n_glyc(seq: str) -> bool:
    # N-X-[S/T], X != P
    for i in range(len(seq) - 2):
        if seq[i] == "N" and seq[i + 1] != "P" and seq[i + 2] in ("S", "T"):
            return True
    return False


def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=600, help="number of designs")
    ap.add_argument("--families", type=int, default=40, help="distinct backbones")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out", default="data/candidates_demo.csv")
    args = ap.parse_args()

    rng = random.Random(args.seed)
    methods = [
        ("RFdiffusion+ProteinMPNN", 0.45),
        ("BindCraft", 0.35),
        ("de novo hallucination", 0.12),
        ("Cetuximab-graft (optimised)", 0.08),  # a few high-quality graft families
    ]

    # Build backbone families: a base sequence + a "family quality" bias so that
    # some backbones are intrinsically better (as happens in real campaigns).
    families = []
    for _ in range(args.families):
        length = rng.choice([58, 62, 65, 68, 72, 75])
        families.append({
            "base": random_seq(length, rng),
            "bias": rng.gauss(0, 0.8),
        })

    rows = []
    for i in range(args.n):
        fam = rng.choice(families)
        method = rng.choices([m for m, _ in methods],
                             weights=[w for _, w in methods])[0]
        seq = mutate(fam["base"], rate=rng.uniform(0.02, 0.12), rng=rng)

        # Latent quality drives all the correlated metrics.
        method_bonus = 1.1 if method.startswith("Cetuximab") else 0.0
        q = rng.gauss(0, 1) + fam["bias"] + method_bonus

        # Map quality -> each metric with realistic ranges and noise.
        plddt = clamp(72 + 9 * q + rng.gauss(0, 4), 40, 98)
        pae = clamp(12 - 4.2 * q + rng.gauss(0, 2.2), 1.5, 30)
        iptm = clamp(0.55 + 0.14 * q + rng.gauss(0, 0.07), 0.05, 0.97)
        rmsd = clamp(2.1 - 0.22 * q + rng.gauss(0, 0.9), 0.3, 8.0)
        mpnn = clamp(1.2 - 0.05 * q + rng.gauss(0, 0.28), 0.4, 2.6)
        ddg = clamp(-22 - 7.5 * q + rng.gauss(0, 5), -60, 10)
        sasa = clamp(850 + 180 * q + rng.gauss(0, 140), 300, 2200)
        # shape_complementarity, rmsd and mpnn are only weakly tied to the
        # latent quality here -- they make decent gates but carry little
        # ranking signal, so the calibration step can show how to down-weight
        # metrics that turn out not to predict binding.
        sc = clamp(0.60 + 0.012 * q + rng.gauss(0, 0.055), 0.2, 0.85)
        # pH selectivity is only weakly tied to quality -- it's a separate ask.
        ph_sel = clamp(3.5 + 2.0 * q + rng.gauss(0, 3.0), 0.4, 25)

        # Liabilities, partly tied to the actual sequence.
        liab_free_cys = 1 if (seq.count("C") % 2 == 1) else 0
        liab_nglyc = 1 if has_n_glyc(seq) else 0
        hydrophobic_frac = sum(c in "FILMVWY" for c in seq) / len(seq)
        liab_hydro = 1 if hydrophobic_frac > 0.42 else 0
        liab_unstruct = 1 if (plddt < 60 and rng.random() < 0.6) else 0

        rows.append({
            "design_id": f"DES_{i:04d}",
            "method": method,
            "sequence": seq,
            "plddt": round(plddt, 1),
            "pae_interaction": round(pae, 2),
            "iptm": round(iptm, 3),
            "rmsd_design": round(rmsd, 2),
            "mpnn_score": round(mpnn, 3),
            "ddg": round(ddg, 1),
            "interface_sasa": round(sasa, 0),
            "shape_complementarity": round(sc, 3),
            "ph_selectivity_fold": round(ph_sel, 2),
            "liab_free_cysteine": liab_free_cys,
            "liab_n_glyc_motif": liab_nglyc,
            "liab_high_hydrophobicity": liab_hydro,
            "liab_long_unstructured": liab_unstruct,
        })

    fieldnames = list(rows[0].keys())
    import os
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {len(rows)} designs to {args.out}")


if __name__ == "__main__":
    main()
