# Shared-reference experiment

Seed: `20261018`. Repeats per `(n,m)` setting: `500`. True original mass: `0.468436`. Candidate regions: `625`. Confidence level: `95%`.

The data follow the original paper: `P0 = N(0,1)` and `B = [-1.55,-0.45] union [0.55,1.35]`. Each of the four endpoints has five fixed grid values, including its true value. Two independent original-law samples provide known-coordinate anchors. Only distances to those anchors are passed to the estimator; coordinates are recovered from them. A separate set of `m` original samples estimates candidate masses.

| n | m | Known median | Known p90 | Sampled median | Sampled p90 | Known bound | Sampled bound | Violations K/S | Different choice |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 40 | 100 | 0.01296 | 0.03656 | 0.01296 | 0.03765 | 0.22095 | 0.70237 | 0/0 | 155/500 |
| 40 | 1,000 | 0.01296 | 0.03520 | 0.01296 | 0.03520 | 0.22095 | 0.38429 | 0/0 | 0/500 |
| 40 | 10,000 | 0.01296 | 0.03520 | 0.01296 | 0.03520 | 0.22095 | 0.28370 | 0/0 | 0/500 |
| 100 | 100 | 0.00000 | 0.00000 | 0.00000 | 0.02051 | 0.08838 | 0.56006 | 0/0 | 160/500 |
| 100 | 1,000 | 0.00000 | 0.01296 | 0.00000 | 0.01296 | 0.08838 | 0.24198 | 0/0 | 0/500 |
| 100 | 10,000 | 0.00000 | 0.00000 | 0.00000 | 0.00000 | 0.08838 | 0.14139 | 0/0 | 0/500 |
| 250 | 100 | 0.00000 | 0.00000 | 0.00000 | 0.02051 | 0.03535 | 0.50313 | 0/0 | 181/500 |
| 250 | 1,000 | 0.00000 | 0.00000 | 0.00000 | 0.00000 | 0.03535 | 0.18505 | 0/0 | 0/500 |
| 250 | 10,000 | 0.00000 | 0.00000 | 0.00000 | 0.00000 | 0.03535 | 0.08447 | 0/0 | 0/500 |
| 500 | 100 | 0.00000 | 0.00000 | 0.00000 | 0.02051 | 0.01768 | 0.48416 | 0/0 | 167/500 |
| 500 | 1,000 | 0.00000 | 0.00000 | 0.00000 | 0.00000 | 0.01768 | 0.16608 | 0/0 | 0/500 |
| 500 | 10,000 | 0.00000 | 0.00000 | 0.00000 | 0.00000 | 0.01768 | 0.06549 | 0/0 | 0/500 |

Maximum anchor reconstruction error: `3.77e-15`. The error and bounds use original probability mass, not Euclidean length. Violations K/S counts errors exceeding the respective known-mass and sampled-mass 95% theorem bounds. Different choice counts when the sampled-mass estimator selected a different region than the known-mass estimator. The bounds may be loose; this experiment checks their empirical coverage.

The distance-only control couples uniform samples on `[0,1]` and their translation to `[2,3]`. Its maximum difference between pairwise distance matrices was `4.44e-16`, while the respective original masses were `1/3` and `2/3`. Distances to a fixed anchor distinguish the locations.

Files: `runs.csv` contains each replicate; `summary.csv` contains grouped statistics; `run_config.json` records parameters and library versions; `distance_only_control.json` contains the ambiguity check; `recovery_bounds.pdf` and `.png` show error and bounds.
