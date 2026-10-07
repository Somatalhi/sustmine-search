"""Experiment 1 with the MIP scheduler. One invocation = one run.

  python run_exp1_mip.py --algo nsga2 --seed 0 --budget 500
  python run_exp1_mip.py --algo nsga3 --seed 0 --budget 500
  python run_exp1_mip.py --algo lhs   --seed 0 --budget 500

Writes results/exp1_mip_<budget>/<algo>_seed<seed>.npz with X, F, G.
Evaluations run in parallel over --workers processes (default: all cores but one).
"""
import argparse, os, pickle, time, multiprocessing as mp
import numpy as np
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.algorithms.moo.nsga3 import NSGA3
from pymoo.util.ref_dirs import get_reference_directions
from pymoo.operators.sampling.lhs import LHS
from pymoo.optimize import minimize
from pymoo.parallelization import StarmapParallelization
from params import P
from sustmine_search.problem_mip import SustMineMIP

POP_II   = 100
REF_DIRS = get_reference_directions("das-dennis", 5, n_partitions=5)   # 126


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--algo", choices=["nsga2", "nsga3", "lhs"], required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--budget", type=int, required=True)
    ap.add_argument("--workers", type=int, default=max(1, mp.cpu_count() - 1))
    ap.add_argument("--time_limit", type=int, default=60)
    a = ap.parse_args()

    out_dir = f"results/exp1_mip_{a.budget}"
    os.makedirs(out_dir, exist_ok=True)
    out_path = f"{out_dir}/{a.algo}_seed{a.seed}.npz"
    if os.path.exists(out_path):
        print(f"{out_path} exists, skipping"); return

    bp = pickle.load(open("bench_phases.pkl", "rb"))
    pool = mp.Pool(a.workers)
    prob = SustMineMIP(bp, P, time_limit=a.time_limit,
                       elementwise_runner=StarmapParallelization(pool.starmap))
    t0 = time.time()
    if a.algo == "nsga2":
        res = minimize(prob, NSGA2(pop_size=POP_II), ("n_evals", a.budget), seed=a.seed, verbose=True)
        X, F, G = res.pop.get("X"), res.pop.get("F"), res.pop.get("G")
    elif a.algo == "nsga3":
        res = minimize(prob, NSGA3(pop_size=len(REF_DIRS), ref_dirs=REF_DIRS),
                       ("n_evals", a.budget), seed=a.seed, verbose=True)
        X, F, G = res.pop.get("X"), res.pop.get("F"), res.pop.get("G")
    else:
        X = LHS().do(prob, a.budget, seed=a.seed).get("X")
        F, G = prob.evaluate(X, return_values_of=["F", "G"])
    pool.close(); pool.join()

    np.savez(out_path, X=X, F=F, G=G)
    feas = (G <= 0).all(axis=1).sum()
    print(f"{a.algo} seed {a.seed} budget {a.budget}: {len(F)} saved, {feas} feasible, "
          f"{(time.time()-t0)/60:.1f} min -> {out_path}")


if __name__ == "__main__":
    main()
