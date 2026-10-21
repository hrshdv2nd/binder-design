# binder-design — an in-silico triage system for protein binder design

A small, readable, end-to-end system that shows **how biotechs use protein
design models to triage lead candidate selection** — the step that turns
thousands of computer-generated binders into the ~96 worth testing in a lab.

Built target-agnostic, shipped configured for **EGFR**, the flagship target of
the [Adaptyv Bio](https://www.adaptyvbio.com/) protein design competitions
(2024 round 1, round 2, and Challenge 1 of the 2026 Anthropic × Adaptyv
competition, which adds a pH-conditional twist).

> The numbers in `data/` are **synthetic** — generated to mirror the
> *distributions* real pipelines produce. No wet-lab results are implied. The
> value here is the **method and the machinery**, which you point at your own
> model outputs.

---

## The one picture to hold in your head

Binder design is a funnel. Each stage is cheaper per design than the next is
expensive, so you spend compute to avoid spending lab wells:

```
  GENERATE            PREDICT / SCORE              TRIAGE  ◀── this repo      VALIDATE
  ─────────           ──────────────               ──────                    ────────
  RFdiffusion   →     AlphaFold2 / ESMFold    →    gate → rank → diversify → Adaptyv lab
  ProteinMPNN         PyRosetta: ddG, SASA, sc     → ~96 designs             BLI / SPR
  BindCraft           (pLDDT, pAE, ipTM, RMSD)        on a plate             → real Kd

  10,000s of designs       every design scored      96 chosen               a handful
                                                     deliberately           of real hits
```

A biotech's edge is **not** running one more RFdiffusion job. It's the triage
logic in the middle: trustworthy gates, a scoring function that weights metrics
by how predictive they actually are, and diversity so one bad backbone doesn't
sink the whole plate. That is what this repo implements and documents.

---

## What's in here

| Path | What it is |
|------|-----------|
| `config/targets/egfr.yaml` | The whole target definition — epitope, metrics, thresholds, weights, plate settings. **Retarget by copying this file.** |
| `src/binder_triage/` | The engine: `schema` → `filters` (gate) → `scoring` (rank) → `diversity` (select) → `triage` (orchestrate) → `report` (plots). |
| `scripts/generate_demo_data.py` | Reproducible synthetic candidate generator. |
| `data/candidates_demo.csv` | 600 example designs. |
| `outputs/` | Report, plate CSV, and four figures from the last run. |
| `docs/` | The learning material — workflow, metrics, and the Adaptyv mapping. |
| `tests/` | Unit tests for every stage. |

---

## Run it

```bash
pip install -r requirements.txt

# 1. (optional) regenerate the synthetic candidate set
python scripts/generate_demo_data.py --n 600 --out data/candidates_demo.csv

# 2. run the full triage pipeline
PYTHONPATH=src python -m binder_triage.cli \
    --target config/targets/egfr.yaml \
    --candidates data/candidates_demo.csv \
    --outdir outputs

# 3. read outputs/report.md and look at the figures
```

You'll get a funnel chart, a rejection breakdown, the **design landscape**
(pAE vs ddG — the chart that decides everything), a score-contribution
breakdown, `report.md`, and `selected_plate.csv` — the shortlist you'd order.

### Interactive explorer

`web/triage_explorer.html` is a self-contained interactive version: drag the
gate thresholds and metric weights and watch the funnel, the design landscape,
and the shortlist update live over the 600-design demo set. Open the file in a
browser, or rebuild it after changing the data with:

```bash
python scripts/build_explorer.py   # reads data/designs.json -> web/triage_explorer.html
```

---

## The three triage stages (and why they're separate)

1. **Gate** (`filters.py`) — hard thresholds answer *is this design even
   admissible?* A gorgeous ddG with a pae_interaction of 25 Å is almost
   certainly a false positive; it never reaches a plate. Gates are binary and
   explain themselves (every rejection records *which* gate dropped it).

2. **Rank** (`scoring.py`) — among admissible designs, a weighted composite of
   robust z-scores answers *which are best?* Metrics in different units (REU,
   Å, probabilities) are standardised so none swamps the others; the **weights
   encode how much you trust each metric** — the real domain knowledge.

3. **Diversify** (`diversity.py`) — the top 96 by score are often the same
   backbone 96 times. Greedy identity clustering caps near-duplicates so the
   plate explores many distinct solutions. If one backbone fails in the lab,
   you haven't lost the whole plate.

Keeping these separate is the whole point: you can always answer *why* a design
was dropped, *why* a survivor ranked where it did, and *why* it did or didn't
make the plate.

---

## Make it yours

- **New target** (TfR1, a viral glycoprotein, …): copy `egfr.yaml`, change the
  epitope, thresholds, and weights. No code changes.
- **Plug in real data**: emit a CSV with `design_id, sequence, method`, one
  column per metric, and `liab_<flag>` columns. See `src/binder_triage/io.py`.
- **Tune the triage**: the thresholds and weights in the YAML are where you
  encode what your own validated campaigns taught you. That feedback loop —
  wet-lab truth → reweight the metrics → better next shortlist — is the actual
  moat, and `docs/02_metrics.md` explains how to close it.

See `docs/` for the full workflow, a metric-by-metric guide, and how this maps
onto the Adaptyv competition and its automated wet lab.
