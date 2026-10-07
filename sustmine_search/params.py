""" Hybrid Case study parameters. Single source of truth; import everywhere.

Values marked [TRS] are informed by the technical report summary of the used mine site and cited as such; values marked [assumed] are study
assumptions stated in the paper.
"""
#===============================================================
# 0. Baseline optimization parameters
#===============================================================
P = dict(
    # Economics
    price=4000.0,            # $/oz            [assumed]
    recovery=0.82,           #                 [assumed]
    cost_mine=3.28,          # $/t moved       [assumed]
    cost_proc=19.25,         # $/t processed   [assumed]
    reclam=3.0,              # $M at closure   [assumed]
    discount=0.10,           #                 [assumed]
    max_life=60,             # scheduler horizon, periods

    # Geotechnical
    slope=55.0,              # overall slope, deg   [assumed]

    # Capital cost model: C = plant_ref*(thr/thr_ref)^0.6 + fleet_ref*(rate/rate_ref)^0.6
    thr_ref=10.0,  capex_plant_ref=540.0,    # $M at 10 Mt/y    [assumed]
    rate_ref=17.0, capex_fleet_ref=360.0,    # $M at 17 Mt/y    [assumed]

    # Workforce: E = a*rate + b*thr + fixed
    emp_per_mtpa_mine=8.4,
    emp_per_mtpa_proc=7.5,
    emp_fixed=163.0,

    # Mine-life bounds, years   [assumed]
    life_min=10,
    life_max=50,
)
COG = P["cost_proc"] / (P["recovery"] * P["price"] / 31.1035)   # marginal cut-off, g/t
