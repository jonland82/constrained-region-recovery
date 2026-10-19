"""Build the paper's two-panel illustration from the committed experiment summary."""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
SUMMARY = ROOT / "experiments" / "shared_references" / "results" / "summary.csv"
OUTPUT = ROOT / "papers" / "figures" / "shared_reference_illustration.pdf"


def main() -> None:
    with SUMMARY.open(newline="", encoding="utf-8") as source:
        rows = [dict(row) for row in csv.DictReader(source)]
    by_setting = {(int(row["n"]), int(row["m"])): row for row in rows}
    sample_sizes = sorted({n for n, _ in by_setting})

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 8.5,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "pdf.fonttype": 42,
        }
    )
    fig, (ax_left, ax_right) = plt.subplots(
        1, 2, figsize=(7.0, 2.0), gridspec_kw={"width_ratios": [1, 1.1]}
    )
    blue, orange, dark = "#316989", "#C47A29", "#333333"

    # Translation preserves all within-sample distances, but the common anchor
    # places each sample on a different part of the original coordinate line.
    points = np.array([0.18, 0.45, 0.78])
    for center, shift, color, label in (
        (1.35, 0.0, blue, r"$B_1$: $P_0(B_1)=1/3$"),
        (0.58, 2.0, orange, r"$B_2$: $P_0(B_2)=2/3$"),
    ):
        ax_left.axvspan(shift, shift + 1, ymin=(center - 0.24) / 1.75,
                        ymax=(center + 0.24) / 1.75, color=color, alpha=0.13)
        ax_left.hlines(center, shift, shift + 1, color=color, linewidth=2.2)
        ax_left.scatter(points + shift, [center] * len(points), s=24,
                        color=color, edgecolor="white", linewidth=0.5, zorder=3)
        ax_left.text(shift + 0.5, center + 0.29, label, color=color,
                     ha="center", va="bottom", fontsize=8)
    ax_left.scatter([0], [0.08], marker="D", s=30, color=dark, clip_on=False)
    ax_left.text(0.08, 0.08, r"shared anchor $a=0$", va="center", fontsize=7.5)
    ax_left.set(xlim=(-0.15, 3.15), ylim=(-0.05, 1.8),
                xticks=[0, 1, 2, 3], yticks=[], xlabel="Original coordinate")
    ax_left.set_title("(a) Same internal distances, different location", fontsize=8.5,
                      loc="left", pad=8)
    ax_left.spines["left"].set_visible(False)

    def series(m: int, key: str) -> list[float]:
        return [float(by_setting[(n, m)][key]) for n in sample_sizes]

    ax_right.plot(sample_sizes, series(100, "known_p90_error"), "o-",
                  color=dark, linewidth=1.5, markersize=4, label="Known masses")
    ax_right.plot(sample_sizes, series(100, "sampled_p90_error"), "s-",
                  color=orange, linewidth=1.5, markersize=4, label=r"Estimated, $m=100$")
    ax_right.plot(sample_sizes, series(1000, "sampled_p90_error"), "^-",
                  color=blue, linewidth=1.5, markersize=4, label=r"Estimated, $m=1{,}000$")
    ax_right.set(xlim=(30, 515), ylim=(-0.002, 0.042), xticks=sample_sizes,
                 yticks=[0, 0.01, 0.02, 0.03, 0.04], xlabel=r"Constrained samples $n$",
                 ylabel=r"90th percentile $P_0(B\triangle\widehat B)$")
    ax_right.set_title("(b) Recovery error on a fixed candidate grid", fontsize=8.5,
                       loc="left", pad=8)
    ax_right.grid(axis="y", color="#E1E1E1", linewidth=0.6)
    ax_right.legend(loc="upper right", frameon=False, fontsize=7.2,
                    handlelength=1.6, labelspacing=0.25)

    fig.subplots_adjust(left=0.065, right=0.99, bottom=0.24, top=0.84, wspace=0.27)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT)
    fig.savefig(OUTPUT.with_suffix(".png"), dpi=200)
    plt.close(fig)
    print(OUTPUT)


if __name__ == "__main__":
    main()
