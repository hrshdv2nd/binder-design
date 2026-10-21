"""Reporting: a markdown summary, a selected-plate CSV, and diagnostic plots.

The plots are the point for a visual learner: they make the triage funnel and
the metric trade-offs legible at a glance instead of as a table of numbers.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless: write files, never open a window
import matplotlib.pyplot as plt
import numpy as np

from .triage import TriageResult

# A calm, colour-blind-safe palette reused across every figure.
C_INPUT = "#9aa5b1"
C_PASS = "#2d8f6f"
C_SELECT = "#1f6feb"
C_REJECT = "#c0523f"
C_ACCENT = "#d98c2b"


# --------------------------------------------------------------------------- #
# Plots
# --------------------------------------------------------------------------- #
def plot_funnel(result: TriageResult, path: Path) -> None:
    """Horizontal funnel: input -> passed gate -> selected for the plate."""
    stages = ["Designs in", "Passed gates", "On the plate"]
    values = [result.n_input, result.n_passed_gate, result.n_selected]
    colors = [C_INPUT, C_PASS, C_SELECT]

    fig, ax = plt.subplots(figsize=(8, 3.6))
    ypos = np.arange(len(stages))[::-1]
    ax.barh(ypos, values, color=colors, height=0.6)
    for y, v, total in zip(ypos, values, [result.n_input] * 3):
        pct = 100 * v / total if total else 0
        ax.text(v + max(values) * 0.01, y, f"{v:,}  ({pct:.0f}%)",
                va="center", fontsize=10)
    ax.set_yticks(ypos)
    ax.set_yticklabels(stages)
    ax.set_xlabel("number of designs")
    ax.set_title(f"Triage funnel — {result.target.name}")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def plot_rejections(result: TriageResult, path: Path) -> None:
    """Which gate was responsible for each rejected design."""
    breakdown = result.rejection_breakdown()
    if not breakdown:
        return
    labels = list(breakdown.keys())
    counts = list(breakdown.values())
    fig, ax = plt.subplots(figsize=(8, max(3, 0.45 * len(labels) + 1.5)))
    ypos = np.arange(len(labels))[::-1]
    ax.barh(ypos, counts, color=C_REJECT, height=0.6)
    for y, v in zip(ypos, counts):
        ax.text(v + max(counts) * 0.01, y, str(v), va="center", fontsize=9)
    ax.set_yticks(ypos)
    ax.set_yticklabels(labels)
    ax.set_xlabel("designs rejected by this gate")
    ax.set_title("Why designs were filtered out (counted per failing gate)")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def plot_landscape(result: TriageResult, path: Path) -> None:
    """The decisive 2-D view: pae_interaction (x) vs ddG (y).

    All designs are plotted; gate failures are greyed, survivors coloured by
    composite score, and plate picks ringed. This is the chart binder-design
    teams stare at -- the bottom-left corner (low pAE, strong ddG) is where
    real binders concentrate.
    """
    xk, yk = "pae_interaction", "ddg"
    all_g = result.gate_results
    have = [g for g in all_g if xk in g.candidate.metrics and yk in g.candidate.metrics]
    if not have:
        return

    fail_x = [g.candidate.metrics[xk] for g in have if not g.passed]
    fail_y = [g.candidate.metrics[yk] for g in have if not g.passed]

    ranked = result.ranked
    pass_x = [sc.candidate.metrics[xk] for sc in ranked]
    pass_y = [sc.candidate.metrics[yk] for sc in ranked]
    pass_s = [sc.score for sc in ranked]

    sel_ids = {id(sc) for sc in result.selection.selected}
    sel_x = [sc.candidate.metrics[xk] for sc in ranked if id(sc) in sel_ids]
    sel_y = [sc.candidate.metrics[yk] for sc in ranked if id(sc) in sel_ids]

    fig, ax = plt.subplots(figsize=(7.5, 6))
    ax.scatter(fail_x, fail_y, s=18, c=C_INPUT, alpha=0.45,
               label="failed a gate", edgecolors="none")
    sctr = ax.scatter(pass_x, pass_y, s=42, c=pass_s, cmap="viridis",
                      label="passed gates", edgecolors="white", linewidths=0.4)
    ax.scatter(sel_x, sel_y, s=150, facecolors="none", edgecolors=C_SELECT,
               linewidths=1.8, label="selected for plate")

    # Draw the two hard-threshold lines that define the admissible box.
    tgt = result.target
    if tgt.metrics.get(xk) and tgt.metrics[xk].hard_max is not None:
        ax.axvline(tgt.metrics[xk].hard_max, ls="--", c=C_REJECT, lw=1, alpha=0.7)
    if tgt.metrics.get(yk) and tgt.metrics[yk].hard_max is not None:
        ax.axhline(tgt.metrics[yk].hard_max, ls="--", c=C_REJECT, lw=1, alpha=0.7)

    cbar = fig.colorbar(sctr, ax=ax)
    cbar.set_label("composite score")
    ax.set_xlabel("pae_interaction  (Å)  — lower is better →")
    ax.set_ylabel("ddG  (REU)  — lower is better ↑")
    ax.invert_yaxis()  # strong (very negative) ddG at the top
    ax.set_title("Design landscape: interface confidence vs predicted binding")
    ax.legend(loc="upper right", framealpha=0.9, fontsize=8)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def plot_contributions(result: TriageResult, path: Path, top_n: int = 15) -> None:
    """Stacked bars: what each metric contributed to the top designs' scores.

    Shows *why* the leaders lead -- whether a design wins on ddG, on interface
    confidence, or by being well-rounded.
    """
    top = result.ranked[:top_n]
    if not top:
        return
    metric_names = list(top[0].contributions.keys())
    cmap = plt.get_cmap("tab10")
    colors = {m: cmap(i % 10) for i, m in enumerate(metric_names)}

    fig, ax = plt.subplots(figsize=(10, 5))
    xpos = np.arange(len(top))
    pos_bottom = np.zeros(len(top))
    neg_bottom = np.zeros(len(top))
    for m in metric_names:
        vals = np.array([sc.contributions[m] for sc in top])
        pos = np.where(vals >= 0, vals, 0)
        neg = np.where(vals < 0, vals, 0)
        ax.bar(xpos, pos, bottom=pos_bottom, color=colors[m], label=m, width=0.8)
        ax.bar(xpos, neg, bottom=neg_bottom, color=colors[m], width=0.8)
        pos_bottom += pos
        neg_bottom += neg

    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(xpos)
    ax.set_xticklabels([sc.candidate.design_id for sc in top],
                       rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("weighted z-score contribution")
    ax.set_title(f"What drives the top {len(top)} designs' scores")
    ax.legend(ncol=2, fontsize=8, loc="upper right", framealpha=0.9)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Text + CSV outputs
# --------------------------------------------------------------------------- #
def write_plate_csv(result: TriageResult, path: Path) -> None:
    import csv

    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["rank", "design_id", "method", "composite_score",
                    "length", "sequence"])
        for i, sc in enumerate(result.selection.selected, start=1):
            c = sc.candidate
            w.writerow([i, c.design_id, c.method, f"{sc.score:.3f}",
                        c.length, c.sequence])


def write_markdown(result: TriageResult, path: Path, figures: list[str]) -> None:
    tgt = result.target
    lines: list[str] = []
    lines.append(f"# Binder triage report — {tgt.name} ({tgt.full_name})\n")
    lines.append(f"- **UniProt**: {tgt.uniprot}")
    if tgt.is_conditional:
        c = tgt.conditional
        lines.append(f"- **Conditional challenge**: {c.get('description','')} "
                     f"(on pH {c.get('on_ph')}, off pH {c.get('off_ph')})")
    if tgt.reference_binder:
        rb = tgt.reference_binder
        lines.append(f"- **Reference binder**: {rb.get('name','?')} "
                     f"(Kd ≈ {rb.get('kd_nm','?')} nM)")
    lines.append("")

    lines.append("## Funnel\n")
    lines.append(f"- Designs in: **{result.n_input:,}**")
    lines.append(f"- Passed all hard gates: **{result.n_passed_gate:,}** "
                 f"({100*result.n_passed_gate/max(result.n_input,1):.0f}%)")
    lines.append(f"- Distinct sequence clusters among survivors: "
                 f"**{result.n_clusters}**")
    lines.append(f"- Selected for the {tgt.selection.get('plate_size',96)}-well "
                 f"plate: **{result.n_selected}**")
    lines.append("")

    bd = result.rejection_breakdown()
    if bd:
        lines.append("## Rejection breakdown\n")
        lines.append("| gate | designs dropped |")
        lines.append("|------|-----------------|")
        for k, v in bd.items():
            lines.append(f"| {k} | {v} |")
        lines.append("")

    lines.append(f"## Top {min(15, len(result.ranked))} ranked designs\n")
    lines.append("| rank | design_id | score | method | ddg | pae_int | plddt | iptm |")
    lines.append("|------|-----------|-------|--------|-----|---------|-------|------|")
    for i, sc in enumerate(result.ranked[:15], start=1):
        m = sc.candidate.metrics
        lines.append(
            f"| {i} | {sc.candidate.design_id} | {sc.score:.2f} | "
            f"{sc.candidate.method} | {m.get('ddg',float('nan')):.1f} | "
            f"{m.get('pae_interaction',float('nan')):.1f} | "
            f"{m.get('plddt',float('nan')):.0f} | {m.get('iptm',float('nan')):.2f} |"
        )
    lines.append("")

    if figures:
        lines.append("## Figures\n")
        for f in figures:
            lines.append(f"![{f}]({f})\n")

    path.write_text("\n".join(lines))
