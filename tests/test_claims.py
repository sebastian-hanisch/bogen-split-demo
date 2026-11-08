"""Jede Zahl der README und der Preset-Hilfen wird aus den Bändern beziehungsweise der Rechnung nachgerechnet und muss im Text stehen (DEMO-PLAYBOOK §1b). Zeiten gibt es nicht."""

import statistics as st
from pathlib import Path

import bgs_constants as C
import bgs_evaluation as ev
import bgs_solver as S

README = (Path(__file__).resolve().parent.parent / "README.md").read_text(encoding="utf-8")
B = ev.load_bands()


def d(x, digits=1):
    return f"{x:.{digits}f}".replace(".", ",")


def p(x, digits=1):
    return d(x, digits) + " %"


def gap(a, b):
    return 100 * (a / b - 1)


def test_the_method_table():
    for key, field in (("RPP", "rpp"), ("NN", "nn"), ("PS", "ps"), ("R1", "r1"), ("R200", "r200"), ("BLK", "blk")):
        cells = []
        for m in C.BAND_SIZES:
            rows = [r for r in B["carp"] if r["m"] == m]
            v = [gap(r[field], r["opt"]) for r in rows]
            cells.append(f"{p(st.mean(v))} ({sum(1 for x in v if x < 1e-9)})")
        line = f"| {C.METHODS[key][0]} | {cells[0]} | {cells[1]} |"
        assert line in README, line


def test_the_capacity_price_and_routes():
    for m in C.BAND_SIZES:
        price = [gap(r["opt"], r["w_all"]) for r in B["carp"] if r["m"] == m]
        text = f"{p(st.mean(price))} höher bei 10 Pflichtkanten (Median {p(st.median(price))}, höchstens {p(max(price))})" if m == 10 else f"{p(st.mean(price))} bei 12 (Median {p(st.median(price))}, höchstens {p(max(price))})"
        assert text in README, text
    routes = [r["routes"] for r in B["carp"] if r["m"] == 10]
    assert f"im Optimum sind es im Mittel {d(st.mean(routes), 1)} Routen" in README


def test_the_rural_postman_route_rarely_hits_the_optimum():
    for m, label in ((10, "(10 Kanten)"), (12, "(12 Kanten)")):
        rows = [r for r in B["carp"] if r["m"] == m]
        k = sum(1 for r in rows if abs(r["rpp"] - r["opt"]) < 1e-9)
        assert f"{k} von 16 {label}" in README, label


def test_dominance_and_share():
    rows5 = [r for r in B["enum"] if r["m"] == 5]
    ok_o = sum(1 for r in rows5 if abs(r["min_oriented"] - r["opt"]) < 1e-9)
    ok_s = sum(1 for r in rows5 if abs(r["min_sets"] - r["opt"]) < 1e-9)
    assert (len(rows5), ok_o, ok_s) == (20, 20, 20)
    assert f"alle 3840 orientierten Folgen das exakte Optimum in {ok_o} von 20 Instanzen" in README and f"alle 120 Kantenfolgen mit Blockpreis ebenfalls in {ok_s} von 20" in README
    rows6 = [r for r in B["enum"] if r["m"] == 6]
    so = [100 * r["opt_oriented"] / r["n_oriented"] for r in rows6]
    ss = [100 * r["opt_sets"] / r["n_sets"] for r in rows6]
    go = st.mean(gap(r["mean_oriented"], r["opt"]) for r in rows6)
    gs = st.mean(gap(r["mean_sets"], r["opt"]) for r in rows6)
    assert f"| Anteil optimaler Folgen, Median (kleinster bis größter) | {p(st.median(so), 2)} ({p(min(so), 2)} bis {p(max(so), 2)}) | {p(st.median(ss))} ({p(min(ss))} bis {p(max(ss))}) |" in README
    assert f"| Lücke einer zufälligen Folge, Mittel | {p(go)} | {p(gs)} |" in README
    assert (len(rows6), rows6[0]["n_oriented"], rows6[0]["n_sets"]) == (12, 46080, 720)
    assert 90 < st.median(ss) / st.median(so) < 120 and "etwa hundertmal seltener als optimale Kantenfolgen mit Blockpreis" in README


def test_random_orientations_against_the_block_price_factor():
    mean = {m: {k: st.mean(gap(r[f], r["opt"]) for r in B["carp"] if r["m"] == m) for k, f in (("R1", "r1"), ("BLK", "blk"))} for m in C.BAND_SIZES}
    factors = sorted(round(mean[m]["R1"] / mean[m]["BLK"]) for m in C.BAND_SIZES)
    assert factors == [36, 51]
    assert "liegt etwa 36- bis 51-mal so weit über dem Optimum wie das beste von 200 Kantenfolgen mit Blockpreis (76,6 / 91,4 % gegen 1,5 / 2,6 %)" in README


def test_the_hand_instance_numbers():
    a = ev.analyse(ev.Settings())
    inst = a.inst
    seq2, _ = ev.parse_sequence("2- 5+ 3- 4- 1+", 5)
    seq3, _ = ev.parse_sequence("2- 1- 4+ 3+ 5-", 5)
    c2, c3 = S.split_cost(inst, seq2), S.split_cost(inst, seq3)
    assert (a.opt, a.w_all, c2, c3) == (42.0, 26.0, 44.0, 50.0)
    assert f"Optimum 42 mit den Routen (4+ 3+ 1-) und (5+ 2+) (Längen 22 und 20); Rural-Postman-Weg ohne Kapazität 26 (das Optimum liegt {p(gap(42, 26))} darüber)" in README
    assert f"nach dem Split 44 ({p(gap(44, 42))} über dem Optimum), die Folge (2- 1- 4+ 3+ 5-) 50" in README
    for r in ev.capacity_scan(a):
        assert f"| {r['Q']} | {d(r['opt'], 2)} | {r['routes']} | {p(gap(r['opt'], 26.0))} |" in README


# --- Presets -----------------------------------------------------------------------------------------------------------------------------

def _analysis(name):
    q = C.PRESETS[name]
    return ev.analyse(ev.Settings(q["m"], q["family"], q["nodes"], q["routes"], q["seed"]))


def test_hand_preset():
    name = "Handinstanz: eine Folge von Hand"
    a = _analysis(name)
    seq, _ = ev.parse_sequence("2- 5+ 3- 4- 1+", 5)
    c = S.split_cost(a.inst, S.rpp_sequence(a.ex))
    assert (a.opt, a.w_all, p(a.capacity_price), c, p(gap(c, a.opt))) == (42.0, 26.0, "61,5 %", 44.0, "4,8 %")
    for text in ("Kapazität 6", "42 mit zwei Routen (4+ 3+ 1-) und (5+ 2+)", "kostet 26", "61,5 %", "nach dem Split 44 (+4,8 %)"):
        assert text in C.PRESET_HELP[name], text


def test_direction_preset():
    name = "Die Richtung zählt (6 Pflichtkanten)"
    a = _analysis(name)
    e = ev.enumerate_all(a.inst)
    assert (e.opt_oriented, e.n_oriented, e.opt_sets, e.n_sets) == (16, 46080, 144, 720) and d(e.opt, 2) == "533,58"
    assert (p(100 * e.opt_oriented / e.n_oriented, 2), p(100 * e.opt_sets / e.n_sets), p(gap(e.mean_oriented, e.opt)), p(gap(e.mean_sets, e.opt))) == ("0,03 %", "20,0 %", "43,0 %", "16,8 %")
    for text in ("8 Knoten", "6 Pflichtkanten", "Seed 2", "16 optimal (0,03 %)", "144 von 720 Kantenfolgen (20,0 %)", "43,0 %", "533,58", "16,8 %"):
        assert text in C.PRESET_HELP[name], text


def test_capacity_preset():
    name = "Die Kapazität kostet (10 Pflichtkanten)"
    a = _analysis(name)
    m = ev.run_methods(a)
    assert (d(a.opt, 2), len(a.routes), d(a.w_all, 2), p(a.capacity_price), p(m.gap("RPP"))) == ("737,88", 3, "453,69", "62,6 %", "5,5 %")
    for text in ("9 Knoten", "10 Pflichtkanten", "Seed 6", "737,88 mit 3 Routen", "453,69", "62,6 %", "5,5 %"):
        assert text in C.PRESET_HELP[name], text


def test_block_price_preset():
    name = "Blockpreis gegen Konstruktion (10 Pflichtkanten)"
    a = _analysis(name)
    m = ev.run_methods(a)
    assert d(a.opt, 2) == "475,19" and m.gap("BLK") == 0.0
    assert [p(m.gap(k)) for k in ("RPP", "NN", "PS", "R200", "R1")] == ["11,3 %", "16,9 %", "17,8 %", "20,0 %", "78,6 %"]
    for text in ("Seed 3", "475,19", "trifft es", "11,3 %", "16,9 %", "17,8 %", "20,0 %", "78,6 %"):
        assert text in C.PRESET_HELP[name], text
