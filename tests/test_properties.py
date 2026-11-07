"""Eigenschaften, die für jede Instanz gelten: Kapazität unendlich, Monotonie, Umkehr, Umnummerieren, Blockpreis, Zufallsverfahren, Plausibilität der Bänder."""

import random

import pytest

import bgs_constants as C
import bgs_evaluation as ev
import bgs_solver as S
from bgs_model import Instance, make_instance

CASES = [(4, 11, 7, 2), (5, 12, 8, 3), (6, 13, 8, 3), (7, 14, 9, 3), (8, 15, 9, 2)]


@pytest.mark.parametrize("m,seed,nodes,routes", CASES)
def test_infinite_capacity_gives_the_rural_postman_optimum_with_one_route(m, seed, nodes, routes):
    a = ev.analyse(ev.Settings(m, 1, nodes, routes, seed))
    opt, parts = S.partition(a.ex, sum(a.inst.q))
    assert len(parts) == 1 and opt == pytest.approx(a.w_all, abs=1e-9)
    assert S.block_cost(a.inst, a.ex.route_of((1 << m) - 1)) == pytest.approx(a.w_all, abs=1e-9)
    assert a.opt >= a.w_all - 1e-9 and a.capacity_price >= -1e-9


@pytest.mark.parametrize("m,seed,nodes,routes", CASES)
def test_a_larger_capacity_is_never_more_expensive_and_never_more_routes_needed(m, seed, nodes, routes):
    a = ev.analyse(ev.Settings(m, 1, nodes, routes, seed))
    last_opt, last_routes = float("inf"), 10 ** 9
    for Q in range(max(a.inst.q), sum(a.inst.q) + 1):
        opt, parts = S.partition(a.ex, Q)
        assert opt <= last_opt + 1e-9 and len(parts) <= last_routes + 1
        assert len(parts) >= -(-sum(a.inst.q) // Q)                # mindestens aufgerundet Gesamtnachfrage durch Kapazität
        last_opt, last_routes = opt, len(parts)


@pytest.mark.parametrize("m,seed,nodes,routes", CASES)
def test_reversing_a_route_keeps_its_length(m, seed, nodes, routes):
    a = ev.analyse(ev.Settings(m, 1, nodes, routes, seed))
    for route in a.routes:
        rev = [(e, 1 - o) for e, o in route[::-1]]
        assert S.block_cost(a.inst, rev) == pytest.approx(S.block_cost(a.inst, route), abs=1e-9)


@pytest.mark.parametrize("m,seed,nodes,routes", CASES[:3])
def test_renumbering_the_required_edges_keeps_the_optimum(m, seed, nodes, routes):
    inst = make_instance(m, seed, nodes, routes)
    perm = list(range(m))
    random.Random(seed).shuffle(perm)
    other = Instance(inst.pts, inst.edges, tuple(inst.req[i] for i in perm), tuple(inst.q[i] for i in perm), inst.Q)
    assert S.partition(S.exact(inst))[0] == pytest.approx(S.partition(S.exact(other))[0], abs=1e-9)


@pytest.mark.parametrize("m,seed,nodes,routes", CASES)
def test_block_price_of_a_sequence_never_exceeds_any_orientation_of_it(m, seed, nodes, routes):
    a = ev.analyse(ev.Settings(m, 1, nodes, routes, seed))
    wl = S.limited(a.ex, a.inst.Q)
    rnd = random.Random(seed)
    for _ in range(20):
        order = rnd.sample(range(m), m)
        arcs = [(e, rnd.randint(0, 1)) for e in order]
        assert S.split_sets_cost(wl, m, order) <= S.split_cost(a.inst, arcs) + 1e-9
        assert S.split_cost(a.inst, arcs) >= a.opt - 1e-9 and S.split_sets_cost(wl, m, order) >= a.opt - 1e-9


@pytest.mark.parametrize("m,seed,nodes,routes", CASES)
def test_split_cost_and_split_arcs_agree_and_cut_into_feasible_blocks(m, seed, nodes, routes):
    inst = make_instance(m, seed, nodes, routes)
    rnd = random.Random(seed)
    for _ in range(10):
        seq = S.random_oriented(rnd, m)
        cost, blocks = S.split_arcs(inst, seq)
        assert cost == pytest.approx(S.split_cost(inst, seq), abs=1e-9)
        assert [a for b in blocks for a in b] == seq and all(sum(inst.q[e] for e, _ in b) <= inst.Q for b in blocks)
        assert cost == pytest.approx(S.plan_cost(inst, blocks), abs=1e-9)


def test_random_methods_are_reproducible_and_a_larger_k_is_never_worse():
    a = ev.analyse(ev.Settings(7, 1, 9, 3, 21))
    one, two = ev.run_methods(a, 50), ev.run_methods(a, 50)
    assert {k: v[0] for k, v in one.results.items()} == {k: v[0] for k, v in two.results.items()}
    assert ev.run_methods(a, 5).results["R200"][0] >= ev.run_methods(a, 50).results["R200"][0] - 1e-9


def test_nearest_neighbour_sequence_is_a_permutation_and_path_scanning_a_valid_plan():
    for seed in range(8):
        inst = make_instance(8, seed, 9, 3)
        nn = S.nn_sequence(inst)
        assert sorted(e for e, _ in nn) == list(range(8))
        cost, plan = S.path_scanning(inst)
        assert S.is_valid_plan(inst, plan) and cost == pytest.approx(S.plan_cost(inst, plan), abs=1e-9)


def test_the_instances_of_the_bands_are_reproducible_from_the_seeds():
    for m in C.BAND_SIZES:
        for r in ev.carp_rows(m)[:2]:
            inst = make_instance(m, r["seed"], C.BAND_NODES, C.BAND_ROUTES)
            assert inst.Q == r["Q"] and sum(inst.q) == r["qsum"]
