# Binder triage report — EGFR (Epidermal Growth Factor Receptor)

- **UniProt**: P00533
- **Conditional challenge**: pH-conditional binding - engage tumour (acidic), spare healthy tissue (on pH 6.5, off pH 7.4)
- **Reference binder**: Cetuximab (scFv format) (Kd ≈ 9.94 nM)

## Funnel

- Designs in: **600**
- Passed all hard gates: **21** (4%)
- Distinct sequence clusters among survivors: **18**
- Selected for the 96-well plate: **21**

## Rejection breakdown

| gate | designs dropped |
|------|-----------------|
| plddt | 422 |
| ph_selectivity_fold | 370 |
| pae_interaction | 362 |
| liability:free_cysteine | 339 |
| rmsd_design | 306 |
| ddg | 233 |
| interface_sasa | 226 |
| iptm | 211 |
| liability:n_glyc_motif | 155 |
| shape_complementarity | 120 |
| mpnn_score | 73 |
| liability:long_unstructured | 68 |
| liability:high_hydrophobicity | 59 |

## Top 15 ranked designs

| rank | design_id | score | method | ddg | pae_int | plddt | iptm |
|------|-----------|-------|--------|-----|---------|-------|------|
| 1 | DES_0451 | 18.52 | BindCraft | -45.0 | 2.6 | 98 | 0.90 |
| 2 | DES_0563 | 13.34 | RFdiffusion+ProteinMPNN | -42.7 | 1.5 | 95 | 0.92 |
| 3 | DES_0164 | 8.19 | BindCraft | -43.7 | 3.9 | 82 | 0.73 |
| 4 | DES_0562 | 7.98 | BindCraft | -37.7 | 7.9 | 94 | 0.97 |
| 5 | DES_0312 | 7.48 | BindCraft | -36.0 | 2.4 | 96 | 0.97 |
| 6 | DES_0554 | 5.61 | Cetuximab-graft (optimised) | -37.2 | 5.5 | 98 | 0.87 |
| 7 | DES_0097 | 4.63 | RFdiffusion+ProteinMPNN | -33.4 | 1.5 | 82 | 0.80 |
| 8 | DES_0274 | 1.86 | de novo hallucination | -35.8 | 3.9 | 88 | 0.84 |
| 9 | DES_0214 | 0.27 | BindCraft | -31.3 | 3.4 | 98 | 0.81 |
| 10 | DES_0492 | 0.16 | de novo hallucination | -39.3 | 5.3 | 90 | 0.78 |
| 11 | DES_0026 | -0.48 | Cetuximab-graft (optimised) | -31.1 | 4.8 | 89 | 0.82 |
| 12 | DES_0152 | -0.55 | Cetuximab-graft (optimised) | -35.2 | 7.0 | 98 | 0.81 |
| 13 | DES_0337 | -0.69 | BindCraft | -33.9 | 6.1 | 82 | 0.70 |
| 14 | DES_0419 | -1.72 | BindCraft | -31.4 | 5.5 | 89 | 0.74 |
| 15 | DES_0071 | -3.17 | RFdiffusion+ProteinMPNN | -31.8 | 4.6 | 83 | 0.70 |

## Figures

![funnel.png](funnel.png)

![rejections.png](rejections.png)

![landscape.png](landscape.png)

![contributions.png](contributions.png)
