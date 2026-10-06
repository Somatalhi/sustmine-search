# sustmine-search

Search-based generation of sustainable mine planning alternatives, benchmarked
against SustMine's evaluative ranking.

## Pipeline
1. `make_shells.py` — loads the grid, sweeps revenue factors, writes `shells.pkl`.
2. `run_smoke.py` — one NSGA-II run, plots the front. Proof of plumbing, not the experiment.

## Package
- `sustmine_search/blocks.py` — loads the block grid
- `sustmine_search/pit.py` — Lerchs–Grossmann pit limit solved with Hochbaum's pseudoflow; slope template; nested shells
- `sustmine_search/_hpf.py` — direct call to the pseudoflow C library
- `sustmine_search/scheduler.py` — shell-walk scheduler and `evaluate(x, shells, p)`
- `sustmine_search/problem.py` — pymoo `ElementwiseProblem`
- `params.py` — all case-study parameters in one place

## Install
    pip install -r requirements.txt

## On the cluster
Only `blocks_small.csv` (or `shells.pkl`) needs to travel.
