"""Randfälle: kleinste Instanzen, Kapazität an den Grenzen, Pflichtkante am Depot, unzulässige Eingaben, Formate."""

import math

import pytest

import bgs_constants as C
import bgs_evaluation as ev
import bgs_solver as S
from bgs_model import Instance, make_instance


@pytest.mark.parametrize("m", (1, 2))
def test_tiny_instances_run_and_the_split_of_any_order_is_optimal_for_one_edge(m):
    a = ev.analyse(ev.Settings(m, 1, 6, 1, 3))
    assert a.opt <= S.split_cost(a.inst, [(e, 0) for e in range(m)]) + 1e-9
    if m == 1:
        assert a.opt == pytest.approx(min(S.split_cost(a.inst, [(0, o)]) for o in (0, 1)), abs=1e-9)
        assert len(a.routes) == 1 and a.w_all == pytest.approx(a.opt, abs=1e-9)


def test_capacity_equal_to_the_largest_demand_is_feasible_and_a_generous_one_gives_one_route():
    a = ev.analyse(ev.Settings(6, 1, 8, 3, 9))
    q = a.inst.q
    opt, parts = S.partition(a.ex, max(q))
    assert opt < math.inf and len(parts) >= -(-sum(q) // max(q))
    opt, parts = S.partition(a.ex, 10 ** 6)
    assert len(parts) == 1 and opt == pytest.approx(a.w_all, abs=1e-9)


def test_a_required_edge_at_the_depot_needs_no_deadhead():
    inst = Instance(((0.0, 0.0), (3.0, 0.0), (3.0, 4.0)), ((0, 1), (1, 2), (0, 2)), ((0, 1),), (1,), 5)
    ex = S.exact(inst)
    assert S.partition(ex)[0] == pytest.approx(6.0, abs=1e-9)                # 3 hin, 3 zurück: Dienst 3 plus Rückweg 3
    assert S.block_cost(inst, [(0, 0)]) == pytest.approx(6.0)


def test_a_demand_above_the_capacity_has_no_split():
    inst = Instance(((0.0, 0.0), (3.0, 0.0), (3.0, 4.0)), ((0, 1), (1, 2), (0, 2)), ((0, 1), (1, 2)), (4, 2), 3)
    assert S.split_cost(inst, [(0, 0), (1, 0)]) == math.inf and S.split_arcs(inst, [(0, 0), (1, 0)])[0] == math.inf
    assert ev.verdict_sequence(ev.Analysis(ev.Settings(), inst, S.exact(inst), 0.0, [], [], 1.0), ev.SequenceResult(math.inf, [], 0.0))[0] == "warning"


def test_the_generator_keeps_the_capacity_at_least_the_largest_demand():
    for seed in range(30):
        inst = make_instance(2, seed, 6, 4)
        assert inst.Q >= max(inst.q)


def test_live_is_only_for_small_instances_and_enumeration_for_smaller_ones():
    with pytest.raises(ValueError):
        ev.analyse(ev.Settings(C.EXACT_LIVE_M + 1, 1, 9, 3, 1))
    with pytest.raises(ValueError):
        ev.enumerate_all(make_instance(C.ENUM_SHARE_M + 1, 1, 8, 3))


def test_bad_sequences_are_rejected_with_a_message():
    for text in ("", "1 2", "1 2 3 4 5 6", "0 1 2 3 4", "1 1 2 3 4", "a b c d e"):
        seq, err = ev.parse_sequence(text, 5)
        assert seq is None and err


def test_graphs_are_connected_for_every_seed_and_size():
    for nodes in (6, 7, 8, 9):
        for seed in range(15):
            inst = make_instance(3, seed, nodes, 2)
            from bgs_model import connected
            assert connected(inst.n_nodes, inst.edges) and all(math.isfinite(x) for row in __import__("bgs_model").paths(inst)[0] for x in row)


def test_formats():
    assert ev.de(3.14159) == "3,14" and ev.pct(12.345) == "12,3 %" and ev.signed_pct(-0.04) == "0,0 %" and ev.signed_pct(2.5) == "+2,5 %" and ev.signed_pct(-2.5) == "−2,5 %"
    assert ev.routes_word(1) == "1 Route" and ev.routes_word(3) == "3 Routen" and ev.instances_word(1) == "1 Instanz" and ev.instances_word(16) == "16 Instanzen"
    assert ev.gap_percent(10.0, 10.0) == 0.0 and ev.gap_percent(11.0, 10.0) == pytest.approx(10.0)
