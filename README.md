# Constrained Region Recovery

Recover hidden output constraints from samples and distances, with proofs and reproducible uncertainty bounds.

At a fixed input, the original output law is `P0`, the unknown allowed region is `B`, and the constrained sampler follows `Q(A) = P0(A intersect B) / P0(B)`. The project asks what can be recovered from sampled outputs, their distances, and samples from `P0`.

## Layout

| Directory | Contents |
|---|---|
| [`papers/`](papers/) | Original inverse sampling paper and shared-reference extension, with LaTeX sources and PDFs. |
| [`experiments/original_region/`](experiments/original_region/) | Script and figure for the original paper's two-interval simulation. |
| [`experiments/shared_references/`](experiments/shared_references/) | Two-sample anchor experiment and its saved results. |
| [`slides/`](slides/) | Similarity-mass slide and its generator. |
| [`deprecated/`](deprecated/) | Earlier conditional-region-area paper. |
| [`scripts/`](scripts/) | Paper build helper. |

## Where the work stands

- The [inverse sampling paper](papers/inverse_sampling_region.pdf) shows that distances within the constrained sample may not identify `B`, even when `P0` is known. It also gives an exact-law identification result and a two-interval estimator with a 1,000-run normal simulation.
- The [shared-reference note](papers/inverse_sampling_shared_references.pdf) uses distances to common anchors to locate constrained outputs. For a fixed family of `M` candidate regions containing the true `B`, it proves bounds on the original mass of the symmetric difference `P0(B symmetric_difference B_est)`. The [LaTeX sources](papers/) contain the assumptions and full proofs.
- These are focused explanatory results. The note does not establish research novelty over the support-estimation literature; its finite-family and concentration arguments build on standard methods.

## Shared-reference experiment

The [experiment script](experiments/shared_references/run_experiment.py) uses `P0 = N(0,1)` and `B = [-1.55,-0.45] union [0.55,1.35]`, matching the original paper. It fixes 625 candidate regions by placing five possible grid values at each of the four endpoints, including the truth. Each trial draws constrained outputs, hides their coordinates, reconstructs them from distances to two independent known-coordinate anchors, and selects the smallest feasible candidate using either exact `P0` masses or masses estimated from a separate original sample.

The committed run uses seed `20261018`, 500 repeats for each `n in {40, 100, 250, 500}` and `m in {100, 1,000, 10,000}`, and confidence parameter `delta = 0.05`. Its [results and plot](experiments/shared_references/results/README.md) include all 6,000 trial records, grouped statistics, the figure, and library versions. No trial exceeded either stated bound; maximum anchor reconstruction error was below `4e-15`. At `m = 100`, sampled masses changed the chosen candidate in 663 of 2,000 trials; at `m >= 1,000`, the choices matched in this run. The bounds are conservative, and the finite grid often yields exact recovery by `n = 100`.

The script also reproduces the original distance-only counterexample: translated samples have the same pairwise distances while their original masses are `1/3` and `2/3`. This checks the ambiguity claim separately from the anchor experiment.

## Next experiments

1. Make recovery harder with finer candidate grids, smaller `n`, and varied region masses. Keep the true region in the fixed family when checking the current theorems; report bound violations and exact-recovery rates as well as average error.
2. Add controlled noise to anchor distances and measure how coordinate error affects region error. State anchor separation and boundary-mass assumptions before claiming a new bound.
3. Test a shared representation learned from an independent pilot sample. Compare it with exact anchors under the same samples and candidate family, then prove how representation error enters the guarantee.
4. Explore a two-sample estimator that penalizes both original mass and constrained outputs left outside a candidate. Compare its rate with the current sampled-mass bound and with prior minimum-volume set work before making a novelty claim.

## Reproduce

From the repo root, with Python and the packages in [`requirements.txt`](requirements.txt):

```powershell
python experiments/original_region/inverse_region_experiment.py
python experiments/shared_references/run_experiment.py --repeats 500
```

The shared-reference run writes its per-run data, summary, plot, seed, library versions, and a short interpretation to [`experiments/shared_references/results/`](experiments/shared_references/results/). Its candidate family contains the true region and is fixed before sampling, as the note requires. The original samples used as anchors are separate from the original samples used to estimate masses.

To rebuild the papers with MiKTeX installed:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build_papers.ps1
```

The helper compiles in `build/latex/` and copies the finished PDFs into `papers/`.
