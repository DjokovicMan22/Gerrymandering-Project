"""Test exact boundary-kernel detailed balance, feasibility and determinism.

We enumerate ALL feasible two-district labeled partitions of a six-node cycle,
then construct every possible non-self transition from first principles.
This is a complete small-state check, not an empirical claim about Michigan.
"""
from __future__ import annotations

from itertools import combinations

import networkx as nx
import pytest
from gerrychain import Graph, Partition
from gerrychain.constraints import contiguous

from redistricting.ensemble.partition import make_updaters
from redistricting.ensemble.reversible import (
    BoundaryMH, BoundaryMHConfig, boundary_edges,
    mh_probability, neighboring_label_count,
)


def make_toy():
    g = nx.cycle_graph(6)
    for n in g:
        g.nodes[n].update(TOTPOP=1, PRE20D=10+n, PRE20R=20-n,
                          COUNTYFIPS="001", MCDFIPS="003")
    return Graph.from_networkx(g)


def plan(graph, membership):
    return Partition(
        graph=graph,
        assignment={n: ("A" if n in membership else "B") for n in range(6)},
        updaters=make_updaters(),
    )


def valid_toy_plans():
    graph = make_toy()
    valid = {}
    for mask in range(1, (1<<6)-1):
        membership = {i for i in range(6) if (mask >> i) & 1}
        if not (2 <= len(membership) <= 4):
            continue
        part = plan(graph, membership)
        if contiguous(part):
            valid[mask] = part
    return valid


def direct_q(source, target, flip_probability=0.55):
    """Independently enumerate boundary-edge selections and orientations.

    Each directed boundary edge initiates a single flip; every undirected
    boundary edge initiates a swap. The probabilities are sums of selections
    yielding the exact requested target labels.
    """
    edges = tuple(source["cut_edges"])
    if not edges:
        return 0.0
    expected = dict(target.assignment.items())
    probability = 0.0
    for u, v in edges:
        a = dict(source.assignment.items())
        swapped = dict(a)
        swapped[u], swapped[v] = a[v], a[u]
        if swapped == expected:
            probability += (1-flip_probability) / len(edges)
        for node, other in ((u,v), (v,u)):
            flipped = dict(a)
            flipped[node] = a[other]
            if flipped == expected:
                probability += flip_probability / (2*len(edges))
    return probability


def test_full_tiny_feasible_state_space_has_exact_detailed_balance():
    valid = valid_toy_plans()
    assert len(valid) >= 6
    for a in valid.values():
        assert len(boundary_edges(a)) == 2
        probs = []
        for b in valid.values():
            if dict(a.assignment.items()) == dict(b.assignment.items()):
                continue
            qa = direct_q(a, b)
            qb = direct_q(b, a)
            if qa:
                assert qb > 0, "Every valid local move must have a reverse"
                pab = qa * mh_probability(qa, qb)
                pba = qb * mh_probability(qb, qa)
                assert pab == pytest.approx(pba, abs=1e-14)
                probs.append(pab)
            else:
                assert qb == 0, "One-way move would break detailed balance"
        assert sum(probs) <= 1 + 1e-14  # remainder is holding self-loop


def test_mh_reversibility_accounts_for_different_boundary_cut_counts():
    g = make_toy()
    a=plan(g, {0,1,2})
    b=plan(g, {0,1,2,3})
    qa=direct_q(a,b)
    qb=direct_q(b,a)
    assert qa > 0 and qb > 0
    assert qa * mh_probability(qa,qb) == pytest.approx(qb*mh_probability(qb,qa))
    assert 0 <= mh_probability(qa,qb) <= 1


def test_seeded_mh_step_is_deterministic_and_tracks_every_rejection():
    g=make_toy()
    initial=plan(g, {0,1,2})
    cfg=BoundaryMHConfig(epsilon=.34, seed=33, flip_probability=.55,
                          max_cut_edges=None, max_split_counties=None,
                          max_split_county_mcd=None)
    def series():
        runner=BoundaryMH(initial,cfg)
        state=initial
        rows=[]
        for _ in range(200):
            event=runner.step(state)
            state=event.partition
            assert runner.valid(state)
            rows.append((tuple(sorted(state.assignment.items())),event.outcome,
                         event.move,event.acceptance_probability))
        return rows,runner.conservation_audit()
    assert series()==series()
    assert series()[1]["accepted"]>0


def test_strict_population_rejection_becomes_counted_self_loop():
    g=make_toy()
    initial=plan(g,{0,1,2})
    mh=BoundaryMH(initial,BoundaryMHConfig(
        epsilon=.001,seed=11,max_cut_edges=None,
        max_split_counties=None,max_split_county_mcd=None))
    for _ in range(35):
        event=mh.step(initial)
        assert event.partition is initial
        assert event.outcome in {"population_rejected", "contiguity_rejected"}
    audit=mh.conservation_audit()
    assert audit["attempted"]==35
    assert audit["population_rejected"]+audit["contiguity_rejected"]==35
    assert audit.get("accepted",0)==0


def test_reverse_neighbor_counts_and_zero_reverse_handled_explicitly():
    g=make_toy()
    a=plan(g,{0,1,2})
    assert neighboring_label_count(g,a.assignment,2,"B")==1
    assert neighboring_label_count(g,a.assignment,2,"A")==1
    assert mh_probability(.2,0)==0
    assert mh_probability(.2,.4)==1
    with pytest.raises(ValueError,match="Invalid proposal probabilities"):
        mh_probability(0,.2)
    with pytest.raises(ValueError,match="Invalid proposal probabilities"):
        mh_probability(.2,-.1)


def test_probability_config_and_starting_feasibility_fail_closed():
    g=make_toy()
    a=plan(g,{0,1,2})
    with pytest.raises(ValueError,match="Mixing probability"):
        BoundaryMH(a,BoundaryMHConfig(flip_probability=1.0))
    with pytest.raises(ValueError,match="Seed"):
        BoundaryMH(a,BoundaryMHConfig(seed=-1))
    with pytest.raises(ValueError,match="not feasible"):
        BoundaryMH(a,BoundaryMHConfig(
            epsilon=.001,max_cut_edges=1,max_split_counties=None,
            max_split_county_mcd=None))
