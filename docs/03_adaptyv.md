# 03 — How this maps onto Adaptyv Bio

[Adaptyv Bio](https://www.adaptyvbio.com/) runs an **automated protein
characterisation lab** and has hosted the best-known open **protein design
competitions**. Anyone can submit designed binders; Adaptyv expresses them and
measures binding, turning the field's in-silico claims into real numbers. This
repo is a self-contained version of the **triage** every serious entrant runs
before submitting — the step that picks which designs are worth a well.

## The competitions (what actually happened)

- **Round 1 (2024) — EGFR.** First open call for de novo EGFR binders.
- **Round 2 (2024/25) — EGFR.** 130+ teams, ~1,100+ designs; **601** expressed
  and measured. Winner **Cradle** at **1.21 nM** — ~4× the next entry and ~8×
  an scFv of cetuximab. Rule: differ from known therapeutic binders in **≥ 10**
  positions. Most entrants used **RFdiffusion** or **BindCraft**.
- **2025 — Nipah virus glycoprotein G.** De novo and lead-optimisation tracks.
- **2026 — Anthropic × Adaptyv.** A multi-challenge series with **5,000+**
  validations sponsored. **Challenge 1 = conditional EGFR** — bind in the acidic
  tumour microenvironment (pH ~6.5), not at healthy-tissue pH (~7.4). Later
  challenges cycle other targets (e.g. TfR1). *This is the "latest target"
  framing this repo is configured for.*

The community analysis of the EGFR rounds
([bioRxiv 2025.04.17.648362](https://www.biorxiv.org/content/10.1101/2025.04.17.648362))
concluded the field lacks **standardised benchmarks and robust computational
metrics for method comparison** — which is precisely the gap a transparent,
config-driven triage like this one is meant to make legible.

## Where this repo sits

| Adaptyv competition step | This repo |
|--------------------------|-----------|
| Pick the target & epitope | `config/targets/egfr.yaml` (epitope, hotspots) |
| Design binders | out of scope — feed in any model's output |
| Decide which to submit | **the triage engine** — gate, rank, diversify |
| Adaptyv expresses & measures (BLI/SPR) | the `selected_plate.csv` is what you'd submit |
| Leaderboard by measured Kd | the wet-lab labels you feed back into the YAML |

## Configuring the conditional (pH) challenge

`egfr.yaml` sets `conditional.enabled: true`, which switches on the
`ph_selectivity_fold` metric (predicted affinity fold-change between off-pH 7.4
and on-pH 6.5). It gates at ≥ 5× and is weighted into the score. For a plain
(non-conditional) target, set `conditional.enabled: false` and that metric
drops out automatically — the engine reads `active_metrics()` and ignores
conditional-only metrics when the target isn't conditional.

## Submitting for real

1. Run your designs through `binder_triage` → `outputs/selected_plate.csv`.
2. Sanity-check the four figures (funnel, rejections, landscape, contributions).
3. Submit the shortlist to the live competition / Adaptyv's platform.
4. When Kd values come back, follow the loop in `docs/02_metrics.md`:
   score each predictor, reweight, re-run. Your config gets smarter every plate.

> Always confirm the **current** target, rules, and dates on Adaptyv's own site
> and the competition platform before submitting — challenges rotate.
