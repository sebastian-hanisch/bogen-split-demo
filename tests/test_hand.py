"""Handwerte (DEMO-PLAYBOOK §1b): die Handinstanz mit den Routen von Hand (ganzzahlige Kosten), dem Postboten, dem Split einer Folge und der Kapazitätsreihe."""

import pytest

import bgs_evaluation as ev
import bgs_solver as S
from bgs_model import paths


def arcs(text):
    return [(int(t[:-1]) - 1, 0 if t[-1] == "+" else 1) for t in text.split()]


def test_distances_of_the_grid(hand):
    D, _ = paths(hand)
    assert D[0][1] == 4 and D[0][2] == 5 and D[0][3] == 3 and D[0][4] == 8 and D[0][5] == 9 and D[5][3] == 8 and D[4][2] == 7


def test_the_optimal_routes_by_hand(hand):
    assert S.block_cost(hand, arcs("4+ 3+ 1-")) == 22.0          # 4 + 4 + 3 + 4 (Leerfahrt 5 -> 2) + 3 + 4 (zurück)
    assert S.block_cost(hand, arcs("5+ 2+")) == 20.0             # 5 + 4 + 4 (Leerfahrt 5 -> 2) + 4 + 3
    a = ev.analyse(ev.Settings())
    assert a.opt == 42.0 and len(a.routes) == 2 and sorted(S.block_cost(hand, r) for r in a.routes) == [20.0, 22.0]
    assert sum(hand.q[e] for e, _ in arcs("4+ 3+ 1-")) == 6 and sum(hand.q[e] for e, _ in arcs("5+ 2+")) == 6


def test_the_rural_postman_route_by_hand(hand):
    assert S.block_cost(hand, arcs("2- 1- 4+ 3+ 5-")) == 26.0    # 3 + 4 + 3 + 4 + 3 + 4 + 5
    a = ev.analyse(ev.Settings())
    assert a.w_all == 26.0 and a.capacity_price == pytest.approx(100 * 16 / 26)


def test_the_split_of_two_sequences_by_hand(hand):
    assert S.split_arcs(hand, arcs("2- 1- 4+ 3+ 5-"))[0] == 50.0          # (2- 1-) 14, (4+) 16, (3+ 5-) 20
    cost, blocks = S.split_arcs(hand, arcs("2- 5+ 3- 4- 1+"))             # (2- 5+) 20, (3- 4- 1+) 24
    assert cost == 44.0 and [len(b) for b in blocks] == [2, 3]
    assert ev.evaluate_sequence(ev.analyse(ev.Settings()), arcs("2- 5+ 3- 4- 1+")).gap == pytest.approx(100 * 2 / 42)


def test_the_capacity_series_by_hand(hand):
    a = ev.analyse(ev.Settings())
    scan = ev.capacity_scan(a)
    assert [(r["Q"], r["opt"], r["routes"]) for r in scan] == [(3, 78.0, 5), (4, 62.0, 4), (5, 50.0, 3), (6, 42.0, 2), (7, 34.0, 2), (12, 26.0, 1)]


def test_sequence_text_and_parsing(hand):
    assert ev.sequence_text(arcs("4+ 3+ 1-")) == "4+ 3+ 1-"
    assert ev.parse_sequence("2- 1- 4 3+ 5−", 5) == ([(1, 1), (0, 1), (3, 0), (2, 0), (4, 1)], None)
    assert ev.parse_sequence("1 2 3", 5)[0] is None and ev.parse_sequence("1 2 3 4 6", 5)[0] is None and ev.parse_sequence("1 1 2 3 4", 5)[0] is None and ev.parse_sequence("1+ 2+ x 4 5", 5)[0] is None
