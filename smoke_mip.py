"""Step 3 check: one MIP solve"""
import pickle, pandas as pd
from params import P
from sustmine_search.precedence import pushback_precedence
from sustmine_search.scheduler_mip import value_table, solve_by, schedule_aggregates

bp = pickle.load(open("bench_phases.pkl", "rb"))
preds = pushback_precedence(bp)
d = value_table(bp, P)
print(f"{len(d)} bench-phases, total value of positive units ${d.value_usd[d.value_usd>0].sum()/1e6:,.0f}M")

out = solve_by(d, preds, mining_cap=40e6, processing_cap=20e6, T=20,
               discount=(1 + P["discount"])**2 - 1, time_limit=180, gap=0.02, solver="highs")
agg = schedule_aggregates(d, out)
print(f"status {out['status']}, objective ${out['objective']/1e6:,.0f}M, life {agg['life']} yr, "
      f"solve {out['seconds']:.1f} s")
print("ore/yr (Mt):  ", agg["ore"].round(1))
print("waste/yr (Mt):", agg["waste"].round(1))
