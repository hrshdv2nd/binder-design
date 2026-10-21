# 04 — Closing the loop: calibrating against measured binding

The thresholds and weights in a target config are a **hypothesis** about which
in-silico metrics predict real binding. This stage tests that hypothesis against
assay data and corrects it. It's the part that makes a team's 10th plate far
better than its 1st.

```
   design metrics ─┐
                   ├─►  calibrate  ─►  per-metric AUROC  ─►  new weights  ─►  edit YAML
   assay results ─┘                    + Spearman vs pKd                      ▲
        ▲                                                                     │
        └──────────────────  next plate is ranked by what worked  ───────────┘
```

## Where do the Kd / binding labels come from?

You do **not** compute Kd — no in-silico tool does. It's a **wet-lab
measurement**, and it's the one external input this whole loop needs.

| Source | What you get | Cost | Use it for |
|--------|--------------|------|-----------|
| **Adaptyv competition data (public)** — the [round 1](https://github.com/adaptyvbio/egfr_competition) and [round 2](https://github.com/adaptyvbio/egfr_competition_2) GitHub repos | Real expression + BLI/SPR binding for hundreds of EGFR designs | **Free** | **Learning the loop right now** |
| **Submitting to the live competition** | Adaptyv assays your plate and returns the data | Free (sponsored validation) | Your own designs |
| **Adaptyv's lab / a CRO** | BLI or SPR Kd on your shortlist | Paid per plate | Production campaigns |
| **BenchBB** (Adaptyv's benchmark) | A standardised binder benchmark set | Free | Method comparison |
| **BindingDB / SKEMPI / PDBbind / SAbDab** | Measured affinities for *known* complexes | Free | Pre-training, sanity checks — not de novo binders |

The practical starting point: **download the Adaptyv round-2 results, map them to
your design metrics, and run the calibration.** The module doesn't care where the
labels came from — it only needs a CSV.

## The results file

One row per design that was tested:

```csv
design_id,binds,kd_nm
DES_0001,1,0.031
DES_0002,0,
DES_0007,1,48.2
```

- `binds` — 1/0 (or true/false, yes/no). The outcome calibration scores against.
- `kd_nm` — measured affinity in nM when the assay quantified it (blank if the
  design didn't bind, or binding wasn't quantified).

Provide either column. With only `kd_nm`, a design counts as a binder when
`kd_nm <= 1000` (1 µM; configurable in `load_results`).

## Run it

```bash
# (demo) synthesize an assay result set, then calibrate
python scripts/generate_demo_results.py --out data/results_demo.csv

PYTHONPATH=src python -m binder_triage.calibrate_cli \
    --target config/targets/egfr.yaml \
    --candidates data/candidates_demo.csv \
    --results data/results_demo.csv \
    --outdir outputs/calibration
```

## What it computes

For each **scored** metric, oriented so higher = more binder-like:

- **AUROC** — probability the metric ranks a random binder above a random
  non-binder. **0.5 = no signal**; `>0.5` predictive; `<0.5` points the wrong
  way. Computed as the Mann-Whitney statistic from ranks (no scipy).
- **Discrimination** — `2·|AUROC − 0.5|`, in `[0, 1]`. A plain "how much did
  this metric matter" number.
- **Spearman vs pKd** — among quantified binders, does the metric rank-correlate
  with actual affinity? (Separating "predicts *whether* it binds" from "predicts
  *how tightly*".)
- **Suggested weight** — proportional to discrimination, rescaled to keep the
  current total weight so the composite score keeps its familiar range. Metrics
  that showed no signal are driven toward zero.

Outputs: `calibration_report.md`, `calibration_auroc.png`, `weight_shift.png`,
and `suggested_weights.yaml` (paste-ready).

## What the demo shows (and the real lesson)

On the synthetic demo, `mpnn_score` (AUROC ≈ 0.51) collapses from weight 0.50 →
~0.04, and `rmsd_design` / `shape_complementarity` are down-weighted — the
config *guessed* they mattered; the data says they carry little **ranking**
signal. The interface-confidence metrics (`pae_interaction`, `ipTM`) and `ddG`
are confirmed as the workhorses, echoing the real finding from the Adaptyv
analysis that **interface confidence metrics separate binders better than
physics-based ΔΔG alone**.

Two honest caveats this module makes visible:

1. **A good gate is not always a good ranker.** `rmsd_design` (self-consistency)
   is a sound admissibility gate yet a weak *ranker* of affinity — different jobs.
   Calibration speaks only to the ranking (weight) role; keep sensible gates even
   on low-AUROC metrics.
2. **Univariate AUROC is confounded by collinearity.** When metrics are
   correlated, each looks predictive partly because of the others. The
   per-metric numbers are the right *first* pass; a multivariate fit (logistic
   regression / a small gradient-boosted model over the metrics) is the natural
   next step once you have a few hundred labels, and slots in exactly where
   `calibrate()` produces weights today.

## The loop, in one line

**Assay → score each metric → reweight the YAML → re-rank the next generation.**
Nothing in the engine code changes; the target config *is* the accumulated,
target-specific knowledge of your campaign. That compounding is the real
"superior binder design model."
