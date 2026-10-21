# 01 — The de novo binder design workflow

This is the full pipeline a modern binder-design team runs. This repo implements
the **triage** stage, but you can't triage well without understanding what
feeds it, so here's the whole thing.

```
┌─────────────┐   ┌──────────────┐   ┌───────────────┐   ┌──────────┐   ┌───────────┐
│ 1. TARGET   │ → │ 2. GENERATE  │ → │ 3. SCORE      │ → │ 4. TRIAGE│ → │ 5. VALIDATE│
│   & epitope │   │   backbones  │   │   every design│   │  shortlist│  │   wet lab  │
└─────────────┘   └──────────────┘   └───────────────┘   └──────────┘   └───────────┘
   pick where       RFdiffusion        AlphaFold2          THIS REPO       Adaptyv:
   to bind          ProteinMPNN        ESMFold                             BLI / SPR
                    BindCraft          PyRosetta                           → real Kd
```

## 1. Target & epitope selection

You don't bind "a protein", you bind a **patch** on it. For EGFR that's the
domain III ligand-binding face (the cetuximab epitope). The config file names
hotspot residues — where the designed binder should make its key contacts.

Choosing the epitope is a scientific decision: it should be functionally
relevant (block the thing the receptor does), accessible, and not already
drugged in a way you can't differentiate from. The 2026 Adaptyv Challenge 1
adds a twist — bind only in the **acidic tumour microenvironment** (pH ~6.5),
not in healthy tissue (pH ~7.4) — turning a binding problem into a *selectivity*
problem.

## 2. Backbone generation

Generate 3-D protein shapes that could sit on the epitope.

- **RFdiffusion** — diffusion model that grows a backbone against the target
  surface and specified hotspots.
- **BindCraft** — an AlphaFold2-in-the-loop pipeline that hallucinates binders
  and is popular precisely because it bakes in some scoring as it designs.
- **Hallucination / other diffusion models** — various.

Output: thousands of backbones (just geometry, no sequence yet).

## 3. Sequence design + scoring

Two questions: *what sequence folds into this backbone?* and *will it actually
bind?*

- **ProteinMPNN / LigandMPNN** — given a backbone, design an amino-acid sequence
  likely to fold into it. Emits a per-sequence score (log-likelihood).
- **AlphaFold2 (multimer / "initial guess") or ESMFold** — refold the designed
  binder *with* the target and read out confidence:
  - **pLDDT** — does the binder fold confidently on its own?
  - **pae_interaction** — how confident is the predicted binder↔target
    interface? *The single most predictive cheap metric.*
  - **ipTM** — are the two chains docked correctly?
  - **RMSD(design)** — did the refold match what you designed (self-consistency)?
- **PyRosetta / Rosetta** — physics-based interface analysis:
  - **ddG** — predicted binding free energy.
  - **interface SASA** — how much surface is buried (bigger, well-packed = better).
  - **shape complementarity** — how well the surfaces mesh.

Output: every design annotated with a vector of metrics — this is exactly the
CSV `binder_triage` consumes.

## 4. Triage — *this repo*

Thousands of scored designs, a budget of ~96 wells. Turn one into the other:

1. **Gate** out the inadmissible (false-positive-prone, undevelopable).
2. **Rank** the rest by a trust-weighted composite score.
3. **Diversify** so the plate explores many backbones, not one.

See `docs/02_metrics.md` for exactly how each metric is used, and the code in
`src/binder_triage/`.

## 5. Experimental validation

The shortlist is synthesised and measured. Adaptyv Bio's automated lab expresses
the designs and measures binding by **BLI (bio-layer interferometry)** / **SPR**,
returning real **Kd** values — e.g. the Cradle round-2 winner at **1.21 nM**,
~8× tighter than an scFv of cetuximab.

## The loop that actually matters

Validation isn't the end — it's a label. The designs that bound (and the ones
that didn't, despite great in-silico scores) tell you **which metrics and
thresholds were actually predictive for this target**. Feed that back into the
weights and gates in the YAML and the next shortlist is better. Teams that close
this loop fastest win; see `docs/02_metrics.md` for how.
