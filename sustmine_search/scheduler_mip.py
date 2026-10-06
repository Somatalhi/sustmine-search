"""'By' mixed-integer production scheduler — the formulation of Lotsu, Bimpong &
Boakye (2026), Front. Artif. Intell. 9:1759758 (Zenodo 10.5281/zenodo.19869809),
with the scheduling unit, precedence, capacities and horizon supplied as arguments.

Decision variables, objective and constraints (1)-(6) are unchanged from
solve_by_formulation in the original open_pit_scheduling.py. What differs:
  * units are bench-phases (not blocks) and precedence is the pushback rule
  * mining and processing capacities are absolute tonnes per period
  * the horizon T is an argument; mine life is read as the last non-empty period
  * environmental penalty is zero (sustainability enters as separate objectives)
"""
import time
import numpy as np, pandas as pd
import pulp

OZ_PER_G = 1.0 / 31.1035


def value_table(bp: pd.DataFrame, p: dict) -> pd.DataFrame:
    """Bench-phase economics. Returns a table with block_id, tonnes,
    processing_tonnes and value_usd — the columns the MIP reads."""
    d = pd.DataFrame({
        "block_id": [f"P{r.pb}_{r.bench}" for r in bp.itertuples()],
        "tonnes":   (bp.ore_t + bp.waste_t).values * 1e6,          # t
        "processing_tonnes": bp.ore_t.values * 1e6,               # t
    })
    rev  = bp.metal_g.values * 1e6 * OZ_PER_G * p["recovery"] * p["price"]   # $
    cost = bp.ore_t.values * 1e6 * p["cost_proc"] + d.tonnes.values * p["cost_mine"]
    d["value_usd"] = rev - cost
    return d


def solve_by(d: pd.DataFrame, preds: dict, mining_cap: float, processing_cap: float,
             T: int, discount: float, time_limit: int = 120, gap: float = 0.02,
             solver: str = "highs") -> dict:
    """Lotsu et al. 'by' formulation. Capacities in tonnes per period."""
    blocks = d.block_id.tolist()
    ton  = dict(zip(d.block_id, d.tonnes))
    proc = dict(zip(d.block_id, d.processing_tonnes))
    val  = dict(zip(d.block_id, d.value_usd))
    disc = [(1.0 + discount) ** (-t) for t in range(1, T + 1)]

    m  = pulp.LpProblem("OpenPit_BY", pulp.LpMaximize)
    y  = {(b, t): pulp.LpVariable(f"y_{b}_{t}",  cat="Binary")       for b in blocks for t in range(1, T + 1)}
    dy = {(b, t): pulp.LpVariable(f"dy_{b}_{t}", lowBound=0, upBound=1) for b in blocks for t in range(1, T + 1)}

    # objective: discounted value of each unit in the period it is mined
    m += pulp.lpSum(val[b] * disc[t - 1] * dy[(b, t)] for b in blocks for t in range(1, T + 1))

    for b in blocks:
        m += dy[(b, 1)] == y[(b, 1)]                                   # (1) linking
        for t in range(2, T + 1):
            m += dy[(b, t)] == y[(b, t)] - y[(b, t - 1)]               # (1) linking
            m += y[(b, t)] >= y[(b, t - 1)]                            # (2) monotone
        m += pulp.lpSum(dy[(b, t)] for t in range(1, T + 1)) <= 1      # (3) once only
    for b, pl in preds.items():                                        # (4) precedence
        for pr in pl:
            for t in range(1, T + 1):
                m += y[(b, t)] <= y[(pr, t)]
    for t in range(1, T + 1):
        m += pulp.lpSum(ton[b]  * dy[(b, t)] for b in blocks) <= mining_cap       # (5)
        m += pulp.lpSum(proc[b] * dy[(b, t)] for b in blocks) <= processing_cap   # (6)

    t0 = time.time()
    if solver == "highs":
        m.solve(pulp.HiGHS(msg=False, timeLimit=time_limit, gapRel=gap))
    else:
        m.solve(pulp.PULP_CBC_CMD(msg=False, timeLimit=time_limit, gapRel=gap))
    elapsed = time.time() - t0

    mined_at = {t: [] for t in range(1, T + 1)}
    for b in blocks:
        for t in range(1, T + 1):
            v = pulp.value(dy[(b, t)])
            if v is not None and v > 0.5:
                mined_at[t].append(b)
    obj = pulp.value(m.objective)
    return dict(status=pulp.LpStatus[m.status], objective=obj if obj is not None else 0.0,
                seconds=elapsed, mined_at=mined_at)


def schedule_aggregates(d: pd.DataFrame, out: dict) -> dict:
    """Annual ore (Mt), waste (Mt), metal (Moz) and life from a solve."""
    ton  = dict(zip(d.block_id, d.tonnes))
    proc = dict(zip(d.block_id, d.processing_tonnes))
    T = len(out["mined_at"])
    ore = np.array([sum(proc[b] for b in out["mined_at"][t]) for t in range(1, T + 1)]) / 1e6
    wst = np.array([sum(ton[b] - proc[b] for b in out["mined_at"][t]) for t in range(1, T + 1)]) / 1e6
    nz = np.where(ore + wst > 1e-9)[0]
    life = int(nz.max() + 1) if len(nz) else 0
    return dict(ore=ore[:life], waste=wst[:life], life=life)
