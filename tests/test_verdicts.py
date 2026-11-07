"""Verdikte sind reine Funktionen: jede Zahl im Text stammt aus der Rechnung, Art und Wortlaut folgen den Schwellen."""

import itertools

import bgs_constants as C
import bgs_evaluation as ev
import bgs_solver as S
from bgs_model import make_instance

HAND = ev.Settings()


def test_sequence_verdict_optimal_and_not():
    a = ev.analyse(HAND)
    kind, text = ev.verdict_sequence(a, ev.evaluate_sequence(a, ev.default_sequence(a)))
    assert kind == "success" and "trifft das Optimum: 42,00 mit 2 Routen" in text
    seq, _ = ev.parse_sequence("2- 5+ 3- 4- 1+", 5)
    kind, text = ev.verdict_sequence(a, ev.evaluate_sequence(a, seq))
    assert kind == "info" and "liefert 44,00 mit 2 Routen, 4,8 % über dem Optimum 42,00" in text and "kostet 26,00" in text and "um 61,5 %" in text


def test_orientation_verdict_for_the_hand_instance():
    a = ev.analyse(HAND)
    seq, _ = ev.parse_sequence("4+ 3+ 1- 5+ 2+", 5)
    v = ev.orientation_view(a, tuple(e for e, _ in seq))
    assert len(v.costs) == 32 and v.best == 42.0 and v.optimal >= 1
    kind, text = ev.verdict_orientation(a, v)
    assert kind == "info" and "allen 32 Richtungswahlen" in text and f"{v.optimal} von 32" in text and ev.de(v.worst) in text and ev.de(v.set_price) in text
    assert v.set_price >= 42.0 - 1e-9


def test_share_verdict_matches_the_enumeration():
    inst = make_instance(5, 3, 8, 2)
    e = ev.enumerate_all(inst)
    kind, text = ev.verdict_share(e)
    assert kind == "info" and f"{e.opt_oriented} von {e.n_oriented} orientierten Folgen" in text and f"{e.opt_sets} von {e.n_sets} Kantenfolgen" in text
    assert ev.pct(ev.gap_percent(e.mean_oriented, e.opt)) in text and ev.pct(ev.gap_percent(e.mean_sets, e.opt)) in text


def test_capacity_verdict():
    a = ev.analyse(HAND)
    scan = ev.capacity_scan(a)
    kind, text = ev.verdict_capacity(a, scan)
    assert kind == "info" and "Bei der Kapazität 6 kostet das Optimum 42,00 mit 2 Routen, 61,5 % mehr" in text and "kleinsten möglichen Kapazität 3 sind es 200,0 % (5 Routen)" in text and "ab Kapazität 12 genügt eine Route (0,0 %)" in text


def test_methods_verdict_levels():
    a = ev.analyse(ev.Settings(10, 1, 9, 3, 6))
    m = ev.run_methods(a)
    kind, text = ev.verdict_methods(a, m)
    best = min(C.HEURISTICS, key=lambda k: m.results[k][0])
    assert kind == ("success" if m.gap(best) == 0.0 else "info") and C.METHODS[best][0] in text and ev.pct(m.gap("R1")) in text and ev.de(a.opt) in text
    assert best == "BLK" and kind == "success"                      # Seed 6: der Blockpreis trifft das Optimum


def test_dominance_verdict_for_the_hand_instance():
    inst = ev.build_instance(HAND)
    e = ev.enumerate_all(inst)
    kind, text = ev.verdict_dominance(inst, e)
    assert kind == "success" and "Über alle 3840 orientierten Folgen von 5 Pflichtkanten ist der beste Split 42,00 (Optimum 42,00): gleich" in text and "über alle 120 Kantenfolgen mit Blockpreis 42,00: gleich" in text
    broken = ev.Enumeration(5, 42.0, 3840, 1, 43.0, 90.0, 120, 1, 42.0, 80.0)
    assert ev.verdict_dominance(inst, broken)[0] == "warning" and "nicht gleich" in ev.verdict_dominance(inst, broken)[1]


def test_band_verdict_and_missing_bands():
    for m in C.BAND_SIZES:
        kind, text = ev.verdict_bands(m)
        s = ev.carp_stats(m)
        best = min(C.HEURISTICS, key=lambda k: s[k]["mean"])
        assert kind == "info" and f"Bei {m} Pflichtkanten (16 Instanzen)" in text and C.METHODS[best][0] in text and ev.pct(s["price"]["mean"]) in text and "bis 12 Pflichtkanten" in text
    assert ev.verdict_bands(99)[0] == "warning"


def test_capacity_scan_always_contains_the_instance_capacity_and_is_sorted():
    for seed in range(5):
        a = ev.analyse(ev.Settings(6, 1, 8, 3, seed))
        scan = ev.capacity_scan(a)
        assert any(r["Q"] == a.inst.Q for r in scan) and [r["Q"] for r in scan] == sorted(r["Q"] for r in scan)
        assert all(x["opt"] >= y["opt"] - 1e-9 for x, y in zip(scan, scan[1:]))
