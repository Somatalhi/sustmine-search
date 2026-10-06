"""Step 4: design vector -> objectives, with the Lotsu et al. MIP as the scheduler.

x = [capex ($M), mining rate (Mt/y), throughput (Mt/y), final pushback (1..K)]
F = [-NPV ($M), waste (Mt), land (ha.yr), -employees, -job security (yr)]   all minimised
Job security is the SustMine social indicator SDI 10.16, measured as mine life in years.
G = [thr - rate, C(rate,thr) - capex, life_min - life, life - life_max]   g <= 0 feasible

Periods are PERIOD_YEARS long; capacities and discounting are per period;
job security (mine life) is reported in years.
"""
import numpy as np, pandas as pd
from .precedence import pushback_precedence
from .scheduler_mip import value_table, solve_by, schedule_aggregates

PERIOD_YEARS = 2


def capex_required(rate, thr, p):
    return (p["capex_plant_ref"] * (thr / p["thr_ref"]) ** 0.6
            + p["capex_fleet_ref"] * (rate / p["rate_ref"]) ** 0.6)


def employees(rate, thr, p):
    return p["emp_per_mtpa_mine"] * rate + p["emp_per_mtpa_proc"] * thr + p["emp_fixed"]


def evaluate(x, bp, p, time_limit=60, gap=0.02, solver="highs"):
    cx, rate, thr = float(x[0]), float(x[1]), float(x[2])
    k_ult = int(np.clip(round(x[3]), 1, bp.pb.max()))

    sub   = bp[bp.pb <= k_ult].reset_index(drop=True)
    preds = pushback_precedence(sub)
    d     = value_table(sub, p)

    T     = int(np.ceil(p["life_max"] / PERIOD_YEARS))
    disc  = (1.0 + p["discount"]) ** PERIOD_YEARS - 1.0
    out   = solve_by(d, preds, mining_cap=rate * 1e6 * PERIOD_YEARS,
                     processing_cap=thr * 1e6 * PERIOD_YEARS,
                     T=T, discount=disc, time_limit=time_limit, gap=gap, solver=solver)
    agg   = schedule_aggregates(d, out)
    L_per = agg["life"]
    L     = L_per * PERIOD_YEARS                 # job security = mine life, years

    # NPV: MIP objective is discounted operating value in $; add capital and closure
    npv = out["objective"] / 1e6 - cx - p["reclam"] / (1.0 + p["discount"]) ** max(L, 1)
    waste = float(agg["waste"].sum())
    area  = float(sub.drop_duplicates("pb").area_ha.sum())        # footprint of pushbacks 1..k_ult
    land  = area * L
    emp   = employees(rate, thr, p)

    F = np.array([-npv, waste, land, -emp, -L], float)
    G = np.array([thr - rate, capex_required(rate, thr, p) - cx,
                  p["life_min"] - L, L - p["life_max"]], float)
    info = dict(npv=npv, job_security=L, waste=waste, land=land, employees=emp, pit=k_ult,
                ore=float(agg["ore"].sum()), status=out["status"], seconds=out["seconds"])
    return F, G, info
