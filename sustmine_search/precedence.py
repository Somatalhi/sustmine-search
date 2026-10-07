"""Pushback precedence for bench-phases.
Bench-phase (pb k, bench b) can be mined only after
  (k, b-1)  the bench-phase directly above it in the same pushback, and
  (k-1, b)  the bench-phase inside it on the same bench (inner pushback).
This is the standard pushback sequencing rule for nested-pit designs
(Munoz et al., 2018, OPPSP; Hustrulid, Kuchta & Martin, 2013).
Put this file in sustmine_search/.
"""
import pandas as pd


def bp_id(pb, bench):
    return f"P{pb}_{bench}"


def pushback_precedence(bp: pd.DataFrame) -> dict:
    """Returns {bench_phase_id: [predecessor_ids]} for every row of bp."""
    exists = {(r.pb, r.bench) for r in bp.itertuples()}
    preds = {}
    for r in bp.itertuples():
        pr = []
        if (r.pb, r.bench - 1) in exists:
            pr.append(bp_id(r.pb, r.bench - 1))
        if (r.pb - 1, r.bench) in exists:
            pr.append(bp_id(r.pb - 1, r.bench))
        preds[bp_id(r.pb, r.bench)] = pr
    return preds
