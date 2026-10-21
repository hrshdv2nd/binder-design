# 02 — The metrics, and how triage uses them

Every metric plays one or both of two roles: a **gate** (hard pass/fail) and a
**scored dimension** (weighted contribution to the rank). Both roles are
declared per-metric in `config/targets/egfr.yaml`.

## The metric cheat-sheet

| metric | what it measures | good | gate (EGFR) | weight | role |
|--------|------------------|------|-------------|--------|------|
| `pae_interaction` | predicted aligned error across the interface (Å) | **low** | ≤ 10 | 2.5 | the big one |
| `ddg` | Rosetta binding free energy (REU) | **low** (very −) | ≤ −20 | 2.0 | strong signal |
| `iptm` | interface pTM — chains docked right? | **high** | ≥ 0.50 | 1.5 | strong signal |
| `ph_selectivity_fold` | affinity fold-change off-pH ÷ on-pH | **high** | ≥ 5 | 1.5 | conditional only |
| `plddt` | binder fold confidence (0–100) | **high** | ≥ 80 | 1.0 | foldability |
| `interface_sasa` | buried interface area (Å²) | **high** | ≥ 800 | 1.0 | interface size |
| `shape_complementarity` | Lawrence–Colman sc (0–1) | **high** | ≥ 0.55 | 1.0 | packing |
| `rmsd_design` | refold vs design backbone (Å) | **low** | ≤ 2.0 | 1.0 | self-consistency |
| `mpnn_score` | ProteinMPNN neg-log-likelihood | **low** | ≤ 1.5 | 0.5 | sequence fit |

### Why `pae_interaction` carries the most weight

Across published benchmarks and the Adaptyv competition analysis, interface
pAE (and the related ipTM) is the cheap in-silico metric that best separates
real binders from non-binders — better than ddG alone, which is prone to
confident-but-wrong false positives. So it both gates hard *and* carries the
heaviest scoring weight. **These weights are a hypothesis**, not a law: they're
exactly what you recalibrate once you have wet-lab labels (see below).

## Gates vs scores — the division of labour

- **Gates** answer *admissible?* They're intentionally strict and
  self-explaining: every rejected design records which gate(s) it failed, so
  `report.md`'s rejection breakdown tells you whether your funnel is
  foldability-limited, interface-limited, or liability-limited.
- **Scores** answer *best among the admissible?* Using **robust z-scores**
  (median / MAD) means a handful of outliers can't distort the ranking, and
  standardising puts REU, Å and probabilities on one comparable axis. The
  weighted sum is one number per design; the per-metric *contributions* are
  kept so the score-contribution plot can show **why** a design ranks where it
  does.

## Developability liabilities (separate red flags)

Scored metrics ask "will it bind?". Liabilities ask "can we make and use it?"
A design that won't express or will aggregate wastes a well regardless of its
ddG. Checked as binary flags, any one of which rejects (but is reported, so you
can override):

- **free_cysteine** — unpaired Cys → disulfide scrambling / dimerisation.
- **n_glyc_motif** — N-X-[S/T] sequon → unwanted glycosylation.
- **high_hydrophobicity** — aggregation / solubility risk (SAP-like).
- **long_unstructured** — disordered stretches → poor expression.

## Diversity — the metric that isn't about one design

`diversity_identity_cutoff` and `max_per_cluster` govern the plate's **spread**.
Two designs ≥ 90% identical are "the same bet". Capping members per cluster
turns "top 96 by score" into "best few from each of many distinct solutions" —
insurance against a single backbone's hidden flaw taking down the whole plate.

## Closing the loop (the part that compounds)

The thresholds and weights above are a starting hypothesis. Once Adaptyv (or any
assay) returns Kd values for a plate:

1. **Score the predictor.** For each metric, how well did it separate binders
   from non-binders on *this* target? (AUC, or correlation with pKd.)
2. **Reweight.** Raise weights on metrics that discriminated; lower the ones
   that didn't. Tighten or relax gates that let through duds or rejected hits.
3. **Re-run** the next generation of designs through the updated config.

Nothing in the code changes — only the YAML. That config *is* the accumulated,
target-specific knowledge of your campaign, and the reason a team's 10th plate
is far better than its 1st. This is what "superior binder design models help
triage lead selection" means in practice: not a single magic model, but a
calibrated funnel that learns from every plate.
