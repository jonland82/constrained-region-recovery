"""Reproduce the shared-reference note's finite-family recovery experiment.

Run from anywhere with ``python experiments/shared_references/run_experiment.py``.
The candidate family and anchors are fixed independently of each inference sample.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from itertools import product
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import scipy
from scipy.stats import norm


TRUE_ENDPOINTS = np.array([-1.55, -0.45, 0.55, 1.35])
SAMPLE_SIZES = (40, 100, 250, 500)
REFERENCE_SIZES = (100, 1_000, 10_000)
DELTA = 0.05
SEED = 20261018
REPEATS = 500


def interval_masses(endpoints: np.ndarray) -> np.ndarray:
    """Return P0 mass for rows [left1, right1, left2, right2]."""
    cdf = norm.cdf(endpoints)
    return cdf[..., 1] - cdf[..., 0] + cdf[..., 3] - cdf[..., 2]


def build_candidates() -> np.ndarray:
    offsets = np.linspace(-0.2, 0.2, 5)
    candidates = np.array(
        [TRUE_ENDPOINTS + np.array(offset) for offset in product(offsets, repeat=4)]
    )
    assert np.all(candidates[:, 0] < candidates[:, 1])
    assert np.all(candidates[:, 1] < candidates[:, 2])
    assert np.all(candidates[:, 2] < candidates[:, 3])
    assert np.any(np.all(np.isclose(candidates, TRUE_ENDPOINTS), axis=1))
    return candidates


def symmetric_difference_masses(candidates: np.ndarray) -> np.ndarray:
    masses = interval_masses(candidates)
    overlap = np.zeros(len(candidates))
    for left_index, right_index in ((0, 1), (2, 3)):
        left = np.maximum(candidates[:, left_index], TRUE_ENDPOINTS[left_index])
        right = np.minimum(candidates[:, right_index], TRUE_ENDPOINTS[right_index])
        overlap += np.maximum(0.0, norm.cdf(right) - norm.cdf(left))
    return np.maximum(0.0, interval_masses(TRUE_ENDPOINTS) + masses - 2 * overlap)


def draw_constrained(rng: np.random.Generator, count: int) -> np.ndarray:
    """Use inverse CDF sampling from P0 conditioned on the two true intervals."""
    cdf = norm.cdf(TRUE_ENDPOINTS)
    component_masses = np.array([cdf[1] - cdf[0], cdf[3] - cdf[2]])
    right_component = rng.random(count) < component_masses[1] / component_masses.sum()
    uniforms = rng.random(count)
    cdf_values = np.where(
        right_component,
        cdf[2] + uniforms * component_masses[1],
        cdf[0] + uniforms * component_masses[0],
    )
    return norm.ppf(cdf_values)


def reconstruct_from_anchors(
    outputs: np.ndarray, rng: np.random.Generator
) -> tuple[np.ndarray, float]:
    """Keep only two anchor distances, then trilaterate in one dimension."""
    anchors = rng.normal(size=2)
    while abs(anchors[1] - anchors[0]) < 0.5:
        anchors = rng.normal(size=2)
    left_anchor, right_anchor = anchors
    r_left = np.abs(outputs - left_anchor)
    r_right = np.abs(outputs - right_anchor)
    recovered = (
        right_anchor**2 - left_anchor**2 + r_left**2 - r_right**2
    ) / (2 * (right_anchor - left_anchor))
    error = float(np.max(np.abs(recovered - outputs)))
    return recovered, error


def feasible_candidates(outputs: np.ndarray, candidates: np.ndarray) -> np.ndarray:
    left_outputs = outputs[outputs < 0]
    right_outputs = outputs[outputs > 0]
    feasible = np.ones(len(candidates), dtype=bool)
    if len(left_outputs):
        feasible &= (candidates[:, 0] <= left_outputs.min()) & (
            candidates[:, 1] >= left_outputs.max()
        )
    if len(right_outputs):
        feasible &= (candidates[:, 2] <= right_outputs.min()) & (
            candidates[:, 3] >= right_outputs.max()
        )
    return feasible


def sampled_masses(original_outputs: np.ndarray, candidates: np.ndarray) -> np.ndarray:
    ordered = np.sort(original_outputs)
    counts = (
        np.searchsorted(ordered, candidates[:, 1], side="right")
        - np.searchsorted(ordered, candidates[:, 0], side="left")
        + np.searchsorted(ordered, candidates[:, 3], side="right")
        - np.searchsorted(ordered, candidates[:, 2], side="left")
    )
    return counts / len(ordered)


def choose_smallest(feasible: np.ndarray, masses: np.ndarray) -> int:
    assert feasible.any(), "The true region must be a feasible candidate."
    return int(np.argmin(np.where(feasible, masses, np.inf)))


def distance_only_control(rng: np.random.Generator) -> dict[str, float]:
    """Couple the original note's two indistinguishable distance laws."""
    first = rng.uniform(0, 1, size=40)
    second = first + 2
    distance_first = np.abs(first[:, None] - first[None, :])
    distance_second = np.abs(second[:, None] - second[None, :])
    return {
        "first_original_mass": 1 / 3,
        "second_original_mass": 2 / 3,
        "maximum_pairwise_distance_difference": float(
            np.max(np.abs(distance_first - distance_second))
        ),
        "mean_distance_to_anchor_zero_first": float(np.mean(np.abs(first))),
        "mean_distance_to_anchor_zero_second": float(np.mean(np.abs(second))),
    }


def summarize(rows: list[dict], beta: float, candidate_count: int) -> list[dict]:
    summary = []
    for n in SAMPLE_SIZES:
        for m in REFERENCE_SIZES:
            group = [row for row in rows if row["n"] == n and row["m"] == m]
            known = np.array([row["known_error"] for row in group])
            sampled = np.array([row["sampled_error"] for row in group])
            summary.append(
                {
                    "n": n,
                    "m": m,
                    "runs": len(group),
                    "known_median_error": float(np.median(known)),
                    "known_p90_error": float(np.quantile(known, 0.9)),
                    "sampled_median_error": float(np.median(sampled)),
                    "sampled_p90_error": float(np.quantile(sampled, 0.9)),
                    "known_bound": group[0]["known_bound"],
                    "sampled_bound": group[0]["sampled_bound"],
                    "known_bound_violations": sum(row["known_bound_violation"] for row in group),
                    "sampled_bound_violations": sum(
                        row["sampled_bound_violation"] for row in group
                    ),
                    "known_exact_recovery": sum(row["known_error"] < 1e-12 for row in group),
                    "sampled_exact_recovery": sum(
                        row["sampled_error"] < 1e-12 for row in group
                    ),
                    "sampled_differs_from_known": sum(
                        row["sampled_candidate_index"] != row["known_candidate_index"]
                        for row in group
                    ),
                    "maximum_anchor_error": max(row["anchor_error"] for row in group),
                }
            )
    assert candidate_count == 625
    assert 0 < beta < 1
    return summary


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def make_figure(summary: list[dict], output_dir: Path) -> None:
    plt.rcParams.update(
        {"font.size": 10, "axes.spines.top": False, "axes.spines.right": False, "pdf.fonttype": 42}
    )
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    n_values = np.array(SAMPLE_SIZES)
    known = [next(row for row in summary if row["n"] == n) for n in n_values]
    axes[0].plot(n_values, [row["known_p90_error"] for row in known], "o-", color="#316989", label="Known masses")
    axes[1].plot(n_values, [row["known_bound"] for row in known], "s-", color="#C74740", label="Known masses")
    for m, color in zip(REFERENCE_SIZES, ("#9F69A2", "#C47A29", "#4D8C67")):
        group = [row for row in summary if row["m"] == m]
        axes[0].plot(n_values, [row["sampled_p90_error"] for row in group], "o--", color=color, label=f"Sampled masses, $m={m:,}$")
        axes[1].plot(n_values, [row["sampled_bound"] for row in group], "s--", color=color, label=f"Sampled masses, $m={m:,}$")
    axes[0].set(title="Observed error: 90th percentile", xlabel="Constrained samples $n$", ylabel="$P_0(B\\triangle\\widehat B)$")
    axes[1].set(title="Theorem bounds at 95% confidence", xlabel="Constrained samples $n$", ylabel="Upper bound on error")
    for axis in axes:
        axis.set_ylim(bottom=0)
        axis.grid(alpha=0.15)
        axis.legend(frameon=False, fontsize=8)
    fig.subplots_adjust(left=0.10, right=0.98, bottom=0.16, top=0.88, wspace=0.30)
    fig.savefig(output_dir / "recovery_bounds.png", dpi=200, bbox_inches="tight")
    fig.savefig(output_dir / "recovery_bounds.pdf", bbox_inches="tight")
    plt.close(fig)


def write_readme(
    output_dir: Path, summary: list[dict], control: dict, beta: float, seed: int, repeats: int
) -> None:
    lines = [
        "# Shared-reference experiment",
        "",
        f"Seed: `{seed}`. Repeats per `(n,m)` setting: `{repeats}`. "
        f"True original mass: `{beta:.6f}`. Candidate regions: `625`. Confidence level: `95%`.",
        "",
        "The data follow the original paper: `P0 = N(0,1)` and "
        "`B = [-1.55,-0.45] union [0.55,1.35]`. Each of the four endpoints "
        "has five fixed grid values, including its true value. Two independent "
        "original-law samples provide known-coordinate anchors. Only distances "
        "to those anchors are passed to the estimator; coordinates are recovered "
        "from them. A separate set of `m` original samples estimates candidate masses.",
        "",
        "| n | m | Known median | Known p90 | Sampled median | Sampled p90 | "
        "Known bound | Sampled bound | Violations K/S | Different choice |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary:
        lines.append(
            f"| {row['n']} | {row['m']:,} | {row['known_median_error']:.5f} | "
            f"{row['known_p90_error']:.5f} | {row['sampled_median_error']:.5f} | "
            f"{row['sampled_p90_error']:.5f} | {row['known_bound']:.5f} | "
            f"{row['sampled_bound']:.5f} | "
            f"{row['known_bound_violations']}/{row['sampled_bound_violations']} | "
            f"{row['sampled_differs_from_known']}/{repeats} |"
        )
    max_anchor = max(row["maximum_anchor_error"] for row in summary)
    lines += [
        "",
        f"Maximum anchor reconstruction error: `{max_anchor:.3g}`. "
        "The error and bounds use original probability mass, not Euclidean length. "
        "Violations K/S counts errors exceeding the respective known-mass and "
        "sampled-mass 95% theorem bounds. "
        "Different choice counts when the sampled-mass estimator selected a "
        "different region than the known-mass estimator. The bounds may be loose; "
        "this experiment checks their empirical coverage.",
        "",
        "The distance-only control couples uniform samples on `[0,1]` and "
        "their translation to `[2,3]`. Its maximum difference between pairwise "
        f"distance matrices was `{control['maximum_pairwise_distance_difference']:.3g}`, "
        "while the respective original masses were `1/3` and `2/3`. "
        "Distances to a fixed anchor distinguish the locations.",
        "",
        "Files: `runs.csv` contains each replicate; `summary.csv` contains grouped "
        "statistics; `run_config.json` records parameters and library versions; "
        "`distance_only_control.json` contains the ambiguity check; "
        "`recovery_bounds.pdf` and `.png` show error and bounds.",
        "",
    ]
    (output_dir / "README.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeats", type=int, default=REPEATS)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).parent / "results")
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error("--repeats must be positive")
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    candidates = build_candidates()
    candidate_masses = interval_masses(candidates)
    candidate_errors = symmetric_difference_masses(candidates)
    beta = float(interval_masses(TRUE_ENDPOINTS))
    candidate_count = len(candidates)
    rng = np.random.default_rng(args.seed)
    rows = []

    for n in SAMPLE_SIZES:
        for m in REFERENCE_SIZES:
            known_bound = 2 * beta * np.log(candidate_count / DELTA) / n
            sampled_bound = (
                2 * beta * np.log(2 * candidate_count / DELTA) / n
                + np.sqrt(2 * np.log(4 * candidate_count / DELTA) / m)
            )
            for repeat in range(args.repeats):
                constrained = draw_constrained(rng, n)
                recovered, anchor_error = reconstruct_from_anchors(constrained, rng)
                if anchor_error > 1e-10:
                    raise AssertionError(f"Anchor reconstruction error: {anchor_error}")
                feasible = feasible_candidates(recovered, candidates)
                original = rng.normal(size=m)
                known_index = choose_smallest(feasible, candidate_masses)
                sampled_index = choose_smallest(
                    feasible, sampled_masses(original, candidates)
                )
                known_error = float(candidate_errors[known_index])
                sampled_error = float(candidate_errors[sampled_index])
                rows.append(
                    {
                        "n": n,
                        "m": m,
                        "repeat": repeat + 1,
                        "anchor_error": anchor_error,
                        "known_candidate_index": known_index,
                        "sampled_candidate_index": sampled_index,
                        "known_error": known_error,
                        "sampled_error": sampled_error,
                        "known_bound": known_bound,
                        "sampled_bound": sampled_bound,
                        "known_bound_violation": int(known_error > known_bound + 1e-12),
                        "sampled_bound_violation": int(sampled_error > sampled_bound + 1e-12),
                    }
                )
            print(f"Completed n={n}, m={m:,}: {args.repeats} repeats", flush=True)

    summary = summarize(rows, beta, candidate_count)
    control = distance_only_control(rng)
    config = {
        "seed": args.seed,
        "repeats_per_setting": args.repeats,
        "sample_sizes": SAMPLE_SIZES,
        "reference_sizes": REFERENCE_SIZES,
        "delta": DELTA,
        "true_endpoints": TRUE_ENDPOINTS.tolist(),
        "true_mass": beta,
        "candidate_count": candidate_count,
        "python": sys.version.split()[0],
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "matplotlib": matplotlib.__version__,
    }
    write_csv(output_dir / "runs.csv", rows)
    write_csv(output_dir / "summary.csv", summary)
    (output_dir / "run_config.json").write_text(
        json.dumps(config, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "distance_only_control.json").write_text(
        json.dumps(control, indent=2) + "\n", encoding="utf-8"
    )
    make_figure(summary, output_dir)
    write_readme(output_dir, summary, control, beta, args.seed, args.repeats)
    print(f"Results: {output_dir}")


if __name__ == "__main__":
    main()
