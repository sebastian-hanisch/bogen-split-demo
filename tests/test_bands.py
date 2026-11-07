"""Die Bänder: Aufbau, Vollständigkeit, Plausibilität und Stichproben gegen eine frische Rechnung mit den Kernen dieser Demo."""

import random

import pytest

import bgs_constants as C
import bgs_evaluation as ev
import bgs_solver as S
from bgs_model import make_instance

B = ev.load_bands()


def test_counts_and_keys():
    assert {m: len(ev.carp_rows(m)) for m in C.BAND_SIZES} == {10: 16, 12: 16}
    assert len(ev.enum_rows(5)) == C.ENUM5_COUNT and len(ev.enum_rows(6)) == C.ENUM6_COUNT
    for r in B["carp"]:
        assert set(r) == {"m", "i", "seed", "Q", "qsum", "opt", "routes", "w_all", "rpp", "nn", "ps", "r1", "r200", "blk"}
    assert B["meta"]["random_k"] == C.RANDOM_K and B["meta"]["nodes"] == C.BAND_NODES and B["meta"]["routes"] == C.BAND_ROUTES


def test_every_method_is_at_or_above_the_optimum_and_the_optimum_at_or_above_the_postman():
    for r in B["carp"]:
        for k in ("rpp", "nn", "ps", "r1", "r200", "blk"):
            assert r[k] >= r["opt"] - 1e-9, (r["m"], r["i"], k)
        assert r["opt"] >= r["w_all"] - 1e-9 and r["r200"] <= r["r1"] + 1e-9 and r["routes"] >= -(-r["qsum"] // r["Q"])


def test_enumerations_are_complete_and_consistent():
    for r in B["enum"]:
        assert r["n_oriented"] == (720 if r["m"] == 6 else 120) * 2 ** r["m"] and r["n_sets"] == (720 if r["m"] == 6 else 120)
        assert r["min_oriented"] >= r["opt"] - 1e-9 and r["min_sets"] >= r["opt"] - 1e-9 and r["opt_oriented"] >= 1 and r["opt_sets"] >= 1
        assert r["mean_oriented"] >= r["min_oriented"] and r["mean_sets"] >= r["min_sets"]
        assert r["opt_sets"] / r["n_sets"] >= r["opt_oriented"] / r["n_oriented"]          # mit Blockpreis ist ein größerer Anteil der Folgen optimal


def test_dominance_holds_in_every_enumerated_instance_of_five_edges():
    for r in ev.enum_rows(5):
        assert r["min_oriented"] == pytest.approx(r["opt"], abs=1e-9) and r["min_sets"] == pytest.approx(r["opt"], abs=1e-9)


@pytest.mark.parametrize("m,i", [(10, 0), (10, 9), (12, 1)])
def test_carp_rows_are_reproduced_from_the_seeds(m, i):
    row = next(r for r in ev.carp_rows(m) if r["i"] == i)
    inst = make_instance(m, row["seed"], C.BAND_NODES, C.BAND_ROUTES)
    ex = S.exact(inst)
    opt, parts = S.partition(ex)
    rnd = random.Random(i)
    wl = S.limited(ex, inst.Q)
    rands = [S.split_cost(inst, S.random_oriented(rnd, m)) for _ in range(C.RANDOM_K)]
    sets = [S.split_sets_cost(wl, m, rnd.sample(range(m), m)) for _ in range(C.RANDOM_K)]
    fresh = {"opt": opt, "routes": len(parts), "w_all": ex.w[(1 << m) - 1], "rpp": S.split_cost(inst, S.rpp_sequence(ex)), "nn": S.split_cost(inst, S.nn_sequence(inst)),
             "ps": S.path_scanning(inst)[0], "r1": rands[0], "r200": min(rands), "blk": min(sets)}
    assert all(fresh[k] == pytest.approx(row[k], abs=1e-7) for k in fresh)


@pytest.mark.parametrize("seed", (101, 107))
def test_an_enumeration_of_six_edges_is_reproduced(seed):
    row = next(r for r in ev.enum_rows(6) if r["seed"] == seed)
    e = ev.enumerate_all(make_instance(6, seed, 8, 3))
    assert (e.opt_oriented, e.opt_sets, e.n_oriented, e.n_sets) == (row["opt_oriented"], row["opt_sets"], row["n_oriented"], row["n_sets"])
    assert e.opt == pytest.approx(row["opt"], abs=1e-9) and e.mean_oriented == pytest.approx(row["mean_oriented"], abs=1e-7)


def test_stats_are_consistent_with_the_rows():
    s10 = ev.carp_stats(10)
    assert s10["count"] == 16 and all(s10[k]["optimal"] <= 16 and s10[k]["mean"] >= 0 and s10[k]["max"] >= s10[k]["median"] for k in C.HEURISTICS)
    assert ev.dominance_stats()["oriented"] == 20 and ev.dominance_stats()["sets"] == 20
