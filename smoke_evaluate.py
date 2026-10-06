"""Step 4 check: evaluate two designs through the MIP."""
import pickle
from params import P
from sustmine_search.evaluate_mip import evaluate

bp = pickle.load(open("bench_phases.pkl", "rb"))
K = bp.pb.max()
for x in ([900.0, 20.0, 10.0, K],          # full pit, mid capacities
          [700.0, 15.0,  8.0, K // 2]):    # half the pushbacks, smaller plant
    F, G, info = evaluate(x, bp, P)
    print(f"x = {x}")
    print(f"  NPV ${info['npv']:,.0f}M  job security {info['job_security']} yr  waste {info['waste']:.0f} Mt  "
          f"land {info['land']:,.0f} ha.yr  employees {info['employees']:.0f}  ore {info['ore']:.0f} Mt")
    print(f"  G = {G.round(1)}   feasible: {bool((G <= 0).all())}   [{info['status']}, {info['seconds']:.1f} s]")
