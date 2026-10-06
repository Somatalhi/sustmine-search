"""pymoo problem with the MIP scheduler as evaluation model. Put in sustmine_search/."""
import numpy as np
from pymoo.core.problem import ElementwiseProblem
from .evaluate_mip import evaluate


class SustMineMIP(ElementwiseProblem):
    """x = [capex $M, mining rate Mt/y, throughput Mt/y, final pushback]"""
    def __init__(self, bp, p, time_limit=60, gap=0.02, **kwargs):
        self.bp, self.p, self.time_limit, self.gap = bp, p, time_limit, gap
        K = int(bp.pb.max())
        super().__init__(n_var=4, n_obj=5, n_ieq_constr=4,
                         xl=np.array([500.0, 12.0,  6.0, 1.0]),
                         xu=np.array([1500.0, 30.0, 15.0, float(K)]),
                         **kwargs)

    def _evaluate(self, x, out, *args, **kwargs):
        F, G, _ = evaluate(x, self.bp, self.p, time_limit=self.time_limit, gap=self.gap)
        out["F"], out["G"] = F, G
