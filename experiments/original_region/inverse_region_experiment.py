"""Reproduce the finite-sample inverse-region figure and repeated-run study."""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import norm

SEED = 20261012
N_OUTPUTS = 40
N_REPEATS = 1000
TRUE_REGION = ((-1.55, -0.45), (0.55, 1.35))
OUTPUT_STEM = Path(__file__).with_suffix("")


def original_mass(intervals):
    return float(sum(norm.cdf(b) - norm.cdf(a) for a, b in intervals))


def overlap_mass(first, second):
    return original_mass(tuple((max(a, c), min(b, d)) for a, b in first
                               for c, d in second if max(a, c) < min(b, d)))


def draw_constrained(rng, count):
    """Draw exactly from the standard normal law conditioned on TRUE_REGION."""
    edges = np.array([norm.cdf(z) for pair in TRUE_REGION for z in pair])
    masses = np.array([edges[1] - edges[0], edges[3] - edges[2]])
    component = rng.choice(2, size=count, p=masses / masses.sum())
    u = rng.random(count)
    cdf_values = np.where(component == 0, edges[0] + u * masses[0],
                          edges[2] + u * masses[1])
    return norm.ppf(cdf_values)


def recover_two_intervals(outputs):
    if len(outputs) < 4:
        raise ValueError("At least four outputs are needed: two per interval.")
    ordered = np.sort(outputs)
    cdf_gaps = np.diff(norm.cdf(ordered))
    split = int(np.argmax(cdf_gaps[1:-1]) + 1)
    recovered = ((float(ordered[0]), float(ordered[split])),
                 (float(ordered[split + 1]), float(ordered[-1])))
    correct_split = (ordered[split] <= TRUE_REGION[0][1]
                     and ordered[split + 1] >= TRUE_REGION[1][0])
    return recovered, correct_split


def difference_mass(recovered):
    return original_mass(TRUE_REGION) + original_mass(recovered) - 2 * overlap_mass(TRUE_REGION, recovered)


def make_figure(outputs, recovered, errors, correct_splits):
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False,
                         "axes.spines.right": False, "pdf.fonttype": 42})
    fig = plt.figure(figsize=(10, 5.5))
    grid = fig.add_gridspec(2, 2, height_ratios=[2.5, 1.3],
                           width_ratios=[1.3, 1], hspace=0.34, wspace=0.29)
    ax = fig.add_subplot(grid[0, :])
    tracks = fig.add_subplot(grid[1, 0], sharex=ax)
    repeat = fig.add_subplot(grid[1, 1])
    green, orange, red = "#4D8C67", "#C47A29", "#C74740"

    z = np.linspace(-2.7, 2.7, 500)
    ax.plot(z, norm.pdf(z), color="#59636D", lw=1.3, label="Original density $p_0$")
    # Every constraint endpoint lies on this grid; bars do not straddle an edge.
    bins = np.arange(-2.75, 2.751, 0.1)
    ax.hist(outputs, bins=bins, density=True, color="#316989", alpha=0.65,
            label=f"Constrained outputs ($n={N_OUTPUTS}$)")
    for left, right in TRUE_REGION:
        ax.axvspan(left, right, color=green, alpha=0.12, zorder=0)
    for (left, right), (est_left, est_right) in zip(TRUE_REGION, recovered):
        for lo, hi in ((left, est_left), (est_right, right)):
            ax.axvspan(lo, hi, color=red, alpha=0.38, zorder=3)
        ax.axvline(est_left, color=orange, ls="--", lw=1.7)
        ax.axvline(est_right, color=orange, ls="--", lw=1.7)
    ax.set(xlim=(-2.35, 2.25), ylim=(0, 0.83), ylabel="Density")
    ax.set_title("A median-error run: red bands mark missed parts of the input region",
                 loc="left", fontsize=11, pad=10)
    ax.tick_params(labelbottom=False)

    for y, intervals, color in ((1, TRUE_REGION, green), (0, recovered, orange)):
        for left, right in intervals:
            tracks.plot([left, right], [y, y], color=color, lw=11,
                        solid_capstyle="butt")
            tracks.plot([left, right], [y, y], ".", color=color, ms=6)
    for (left, right), (est_left, est_right) in zip(TRUE_REGION, recovered):
        for lo, hi in ((left, est_left), (est_right, right)):
            tracks.axvspan(lo, hi, color=red, alpha=0.3)
    tracks.set(xlim=(-2.35, 2.25), ylim=(-0.5, 1.55), xlabel="Output coordinate $z$")
    tracks.set_yticks([1, 0], ["Input $B$", "Recovered $\\widehat B$"])
    tracks.tick_params(axis="y", length=0)
    tracks.grid(axis="x", alpha=0.17)
    tracks.set_title("Input versus recovered intervals", loc="left", fontsize=10)

    repeat.hist(errors, bins=np.linspace(0, max(0.16, errors.max()), 27),
                color="#9AAFC0", edgecolor="white", lw=0.4)
    observed_error = difference_mass(recovered)
    repeat.axvline(observed_error, color=red, lw=2,
                   label=f"Shown run: {observed_error:.3f}")
    repeat.axvline(np.median(errors), color="#333E48", lw=1.5, ls="--",
                   label=f"Median: {np.median(errors):.3f}")
    repeat.set(xlabel="$P_0(B\\triangle\\widehat B)$", ylabel="Runs")
    repeat.set_title(f"{N_REPEATS:,} independent repeats", loc="left", fontsize=10)
    repeat.legend(frameon=False, fontsize=8)

    fig.text(0.12, 0.025,
             f"Known $P_0=N(0,1)$; two intervals assumed; largest eligible CDF gap. "
             f"Correct split in {sum(correct_splits)}/{N_REPEATS} runs.",
             fontsize=9, color="#3C4852")
    fig.subplots_adjust(left=0.12, right=0.98, top=0.91, bottom=0.15)
    fig.savefig(OUTPUT_STEM.with_suffix(".png"), dpi=220)
    fig.savefig(OUTPUT_STEM.with_suffix(".pdf"))
    plt.close(fig)


def main():
    rng = np.random.default_rng(SEED)
    runs = []
    for _ in range(N_REPEATS):
        outputs = draw_constrained(rng, N_OUTPUTS)
        estimate, correct = recover_two_intervals(outputs)
        runs.append((outputs, estimate, correct, difference_mass(estimate)))
    errors = np.asarray([run[3] for run in runs])
    shown_index = int(np.argmin(np.abs(errors - np.median(errors))))
    outputs, recovered, _, shown_error = runs[shown_index]
    correct_splits = [run[2] for run in runs]
    make_figure(outputs, recovered, errors, correct_splits)
    print(f"seed={SEED}; n={N_OUTPUTS}; repeats={N_REPEATS}")
    print(f"input_region={TRUE_REGION}; input_mass={original_mass(TRUE_REGION):.6f}")
    print(f"shown_run={shown_index + 1} (nearest median error)")
    print(f"recovered_region={recovered}; recovered_mass={original_mass(recovered):.6f}")
    print(f"shown_symmetric_difference_mass={shown_error:.6f}")
    print(f"median_error={np.median(errors):.6f}; q90_error={np.quantile(errors, .9):.6f}")
    print(f"correct_splits={sum(correct_splits)}/{N_REPEATS}")


if __name__ == "__main__":
    main()
