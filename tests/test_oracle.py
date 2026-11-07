"""Orakel (ORACLE-PLAYBOOK §5): ein unabhängiger Rechenweg gegen das exakte Verfahren, den Split und jedes Verfahren auf kleinen Instanzen.

Das Orakel rechnet eigene kürzeste Wege (Floyd-Warshall in der Testdatei), zählt alle Zerlegungen der Pflichtkanten in Gruppen auf (Mengenpartitionen) und nimmt je Gruppe die kürzeste Route aus allen
Reihenfolgen und Richtungen. Jedes Verfahren muss Pläne liefern, die jede Pflichtkante genau einmal bedienen, die Kapazität einhalten, deren gemessene Länge den Kosten entspricht und die nie unter dem Optimum liegen."""

import itertools
import math

import pytest

import bgs_evaluation as ev
import bgs_solver as S
from bgs_model import make_instance


def dist(inst):
    n = inst.n_nodes
    d = [[math.inf] * n for _ in range(n)]
    for i in range(n):
        d[i][i] = 0.0
    for a, b in inst.edges:
        d[a][b] = d[b][a] = math.dist(inst.pts[a], inst.pts[b])
    for k in range(n):
        for i in range(n):
            for j in range(n):
                d[i][j] = min(d[i][j], d[i][k] + d[k][j])
    return d


def route_cost(inst, d, arcs):
    """Länge einer Route aus Bögen (e, o) von Hand: Leerfahrten auf kürzesten Wegen."""
    pos, total = 0, 0.0
    for e, o in arcs:
        a, b = inst.req[e] if o == 0 else inst.req[e][::-1]
        total += d[pos][a] + math.dist(inst.pts[a], inst.pts[b])
        pos = b
    return total + d[pos][0]


def best_route(inst, d, edges):
    return min(route_cost(inst, d, list(zip(p, o))) for p in itertools.permutations(edges) for o in itertools.product((0, 1), repeat=len(edges)))


def partitions(items):
    if not items:
        yield []
        return
    first, rest = items[0], items[1:]
    for part in partitions(rest):
        yield [[first]] + part
        for i in range(len(part)):
            yield part[:i] + [[first] + part[i]] + part[i + 1:]


def brute_optimum(inst):
    d = dist(inst)
    cache = {}
    best = math.inf
    for part in partitions(list(range(inst.m))):
        if all(sum(inst.q[e] for e in g) <= inst.Q for g in part):
            total = 0.0
            for g in part:
                key = tuple(g)
                if key not in cache:
                    cache[key] = best_route(inst, d, g)
                total += cache[key]
            best = min(best, total)
    return best


def test_brute_force_oracle_on_the_hand_instance(hand):
    assert brute_optimum(hand) == pytest.approx(42.0, abs=1e-9)


@pytest.mark.parametrize("m,seed,nodes,routes", [(2, 1, 6, 1), (3, 2, 6, 2), (4, 3, 7, 2), (4, 4, 8, 3), (5, 5, 8, 2), (5, 6, 8, 3)])
def test_exact_equals_brute_force_and_every_method_is_valid_and_not_below_it(m, seed, nodes, routes):
    s = ev.Settings(m, 1, nodes, routes, seed)
    a = ev.analyse(s)
    inst, d = a.inst, dist(a.inst)
    opt = brute_optimum(inst)
    assert a.opt == pytest.approx(opt, abs=1e-9)
    assert a.w_all == pytest.approx(best_route(inst, d, list(range(m))), abs=1e-9)
    meth = ev.run_methods(a, 30)
    assert set(meth.results) == {"OPT", "RPP", "NN", "PS", "R1", "R200", "BLK"}
    for key, (cost, plan) in meth.results.items():
        assert S.is_valid_plan(inst, plan), key
        assert sum(route_cost(inst, d, r) for r in plan) == pytest.approx(cost, abs=1e-9), key
        assert cost >= opt - 1e-9, key
    assert meth.results["OPT"][0] == pytest.approx(opt, abs=1e-9)


@pytest.mark.parametrize("seed", range(6))
def test_split_equals_the_enumeration_of_all_cuts(seed):
    inst = make_instance(5, 40 + seed, 8, 2)
    d = dist(inst)
    seq = [(e, (seed + e) % 2) for e in [2, 0, 4, 1, 3]]
    best = math.inf
    for cuts in itertools.product((0, 1), repeat=4):
        blocks, cur = [], [seq[0]]
        for c, arc in zip(cuts, seq[1:]):
            if c:
                blocks.append(cur)
                cur = [arc]
            else:
                cur.append(arc)
        blocks.append(cur)
        if all(sum(inst.q[e] for e, _ in b) <= inst.Q for b in blocks):
            best = min(best, sum(route_cost(inst, d, b) for b in blocks))
    assert S.split_cost(inst, seq) == pytest.approx(best, abs=1e-9)
    cost, blocks = S.split_arcs(inst, seq)
    assert cost == pytest.approx(best, abs=1e-9) and [a for b in blocks for a in b] == seq


def test_dominance_on_the_hand_instance_over_all_oriented_sequences(hand):
    ex = S.exact(hand)
    opt, _ = S.partition(ex)
    best = min(S.split_cost(hand, list(zip(p, o))) for p in itertools.permutations(range(5)) for o in itertools.product((0, 1), repeat=5))
    assert best == pytest.approx(opt, abs=1e-9)
    wl = S.limited(ex, hand.Q)
    assert min(S.split_sets_cost(wl, 5, p) for p in itertools.permutations(range(5))) == pytest.approx(opt, abs=1e-9)
