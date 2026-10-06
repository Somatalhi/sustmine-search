# sustmine-search

Search-based generation of sustainable mine planning alternatives, benchmarked
against SustMine's evaluative Pareto ranking. The evaluation model is the
open-source "by" MIP production scheduler of Lotsu, Bimpong & Boakye (2026),
run on bench-phase units with pushback precedence.

## Pipeline

0. `reduceBlocks.m` (MATLAB, workstation) — Vulcan CSV export → un-rotated 20 m grid, `blocks_small.csv`
1. `make_shells.py` — nested pit shells by max-flow across revenue factors → `shells.pkl`, `shell_of_block.npy`
2. `make_bench_phases.py` — blocks inside the ultimate pit → equal-tonnage pushbacks × benches → `bench_phases.pkl`
3. `check_precedence.py` — verifies the pushback precedence structure
4. `smoke_mip.py` — one MIP schedule on the full model
5. `smoke_evaluate.py` — two designs through `evaluate()`
6. `run_smoke_mip.py` — short parallel NSGA-II run; proof of plumbing
7. `run_exp1_mip.py --algo {nsga2,nsga3,lhs} --seed S --budget B` — Experiment 1, one run per call
8. `metrics_exp1.py` — hypervolume, IGD+, set coverage, Wilcoxon / A12
9. `run_exp2.py` — Experiment 2: flat vs SustMine hierarchical ranking of the search population
10. `run_exp3.py` — Experiment 3: robustness under indicator noise

## Package

* `sustmine_search/blocks.py` — loads the block grid
* `sustmine_search/pit.py` — Lerchs–Grossmann pit limit by max-flow (igraph), slope template, nested shells
* `sustmine_search/precedence.py` — pushback precedence for bench-phases
* `sustmine_search/scheduler_mip.py` — Lotsu et al. "by" formulation (PuLP, HiGHS/CBC) with units, capacities and horizon as arguments
* `sustmine_search/evaluate_mip.py` — design vector → five objectives and four constraints
* `sustmine_search/problem_mip.py` — pymoo `ElementwiseProblem`
* `sustmine_search/ranking.py` — SustMine hierarchical Pareto ranking (Jenks + nondominated sorting)
* `params.py` — all case-study parameters in one place

## Install

PuLP must be version 2.x (`pulp<3`); the scheduler uses its original API.

## On the cluster

Only `blocks_small.csv` needs to travel; steps 1–2 regenerate everything else.
Each `run_exp1_mip.py` call is independent and can be submitted as one job.
