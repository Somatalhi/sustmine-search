"""
cpit_adapter.py -- bench-phase instance -> MineLib CPIT -> schedule, as a drop-in for solve_by.

Takes the same inputs as scheduler_mip.solve_by (value table d, precedence dict preds,
capacities per period, horizon T, per-period discount) and returns the same dict
(status, objective, seconds, mined_at), so evaluate_mip's objective code is unchanged.

CPIT resources:
    r=0  rock tonnes mined in period t      <= mining_cap
    r=1  ore tonnes processed in period t   <= processing_cap
    r=2,3 (optional blending, if blend=(Gmin, Gmax) in g/t):
         sum_b (metal_b - Gmax*ore_b) x_bt <= 0      (head grade <= Gmax)
         sum_b (Gmin*ore_b - metal_b) x_bt <= 0      (head grade >= Gmin)
Discounting: solve_by discounts period t (1..T) by (1+i)^-t (end of period). CPIT discounts
period t (0..T-1) by (1/(1+i))^t, so block values are pre-multiplied by 1/(1+i) to match.
"""
import time
import numpy as np
import pandas as pd
from .cpit import solve_cpit, check_solution


def build_cpit(d: pd.DataFrame, preds: dict, mining_cap: float, processing_cap: float,
               T: int, discount: float, blend=None):
    """Return (I, pred_idx, ids). I has the keys read_cpit produces."""
    ids = d.block_id.tolist()
    idx = {b: i for i, b in enumerate(ids)}
    nb = len(ids)
    nr = 2 + (2 if blend is not None else 0)

    p = d.value_usd.values / (1.0 + discount)                 # end-of-period convention
    Q = np.zeros((nb, nr))
    Q[:, 0] = d.tonnes.values
    Q[:, 1] = d.processing_tonnes.values
    lb = np.full((nr, T), -np.inf)
    ub = np.full((nr, T), np.inf)
    ub[0, :] = mining_cap
    ub[1, :] = processing_cap
    if blend is not None:
        gmin, gmax = blend
        metal = d.metal_g.values                              # grams of metal per unit
        ore = d.processing_tonnes.values
        Q[:, 2] = metal - gmax * ore
        Q[:, 3] = gmin * ore - metal
        ub[2, :] = 0.0
        ub[3, :] = 0.0

    pred_idx = [[idx[q] for q in preds.get(b, [])] for b in ids]
    I = dict(NAME="benchphase", NBLOCKS=nb, NPERIODS=T, NRES=nr,
             DISCOUNT_RATE=discount, p=p, Q=Q, lb=lb, ub=ub)
    return I, pred_idx, ids


def solve_cpit_by(d: pd.DataFrame, preds: dict, mining_cap: float, processing_cap: float,
                  T: int, discount: float, time_limit: int = 120, gap: float = 0.02,
                  blend=None, check: bool = False) -> dict:
    """Same signature/return as scheduler_mip.solve_by, solved as CPIT."""
    I, pred_idx, ids = build_cpit(d, preds, mining_cap, processing_cap, T, discount, blend)
    t0 = time.time()
    res = solve_cpit(I, pred_idx, time_limit=time_limit, gap=gap, msg=False)
    elapsed = time.time() - t0

    mined_at = {t: [] for t in range(1, T + 1)}
    for i, per in enumerate(res["period"]):
        if per >= 0:
            mined_at[int(per) + 1].append(ids[i])
    obj = res["objective"] if res["objective"] is not None else 0.0
    out = dict(status=res["status"], objective=obj, seconds=elapsed, mined_at=mined_at,
               mip_gap=res.get("mip_gap", float("nan")), highs_status=res.get("highs_status", ""))
    if check:
        out["check"] = check_solution(I, pred_idx, res["X"])
    return out