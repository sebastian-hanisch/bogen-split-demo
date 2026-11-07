"""Kennzahlen, Aufzählungen, Bänder und Verdikt-Logik. Verdikte sind reine Funktionen (Art, Text): die App ruft st.<Art>(Text), die Tests prüfen jede Zahl im Text."""

import itertools
import json
import random
import statistics as st
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import bgs_constants as C
import bgs_solver as S
from bgs_model import INF, Instance, hand_instance, make_instance


@dataclass(frozen=True)
class Settings:
    m: int = C.DEFAULT_M
    family: int = C.DEFAULT_FAMILY
    nodes: int = C.DEFAULT_NODES
    routes: int = C.DEFAULT_ROUTES
    seed: int = C.DEFAULT_SEED


# ----------------------------------------------------------------------------------------------------------------------------------- Formate

def de(x: float, digits: int = 2) -> str:
    return f"{x:.{digits}f}".replace(".", ",")


def pct(x: float, digits: int = 1) -> str:
    return f"{de(x, digits)} %"


def signed_pct(x: float, digits: int = 1) -> str:
    """Mit Vorzeichen (echtes Minus); -0,0 wird zu 0,0."""
    text = de(abs(x), digits)
    if float(text.replace(",", ".")) == 0.0:
        return f"{text} %"
    return f"{'+' if x > 0 else '−'}{text} %"


def routes_word(k: int) -> str:
    return f"{k} Route" if k == 1 else f"{k} Routen"


def instances_word(k: int) -> str:
    return f"{k} Instanz" if k == 1 else f"{k} Instanzen"


def gap_percent(cost: float, reference: float) -> float:
    """Abstand zur Referenz in Prozent der Referenz; innerhalb der Toleranz 0."""
    if reference <= 0 or abs(cost - reference) <= C.TOL:
        return 0.0
    return 100.0 * (cost - reference) / reference


# ----------------------------------------------------------------------------------------------------------------------------------- Instanz und Analyse

def build_instance(s: Settings) -> Instance:
    if s.family == C.HAND_FAMILY:
        return hand_instance()
    return make_instance(s.m, s.seed, s.nodes, s.routes)


@dataclass(frozen=True, eq=False)
class Analysis:
    settings: Settings
    inst: Instance
    ex: S.Exact
    opt: float
    parts: list                    # Bitmasken der optimalen Zerlegung
    routes: list                   # die optimalen Routen als Bögen
    w_all: float                   # Rural-Postman-Optimum (eine Route, Kapazität ignoriert)

    @property
    def capacity_price(self) -> float:
        """Aufschlag des Optimums mit Kapazität gegen das Rural-Postman-Optimum in Prozent."""
        return gap_percent(self.opt, self.w_all)


@lru_cache(maxsize=64)
def _exact(inst: Instance) -> S.Exact:
    return S.exact(inst)


def analyse(s: Settings) -> Analysis:
    inst = build_instance(s)
    if inst.m > C.EXACT_LIVE_M:
        raise ValueError(f"live nur bis {C.EXACT_LIVE_M} Pflichtkanten")
    ex = _exact(inst)
    opt, parts = S.partition(ex)
    return Analysis(s, inst, ex, opt, parts, [ex.route_of(p) for p in parts], ex.w[(1 << inst.m) - 1])


def sequence_text(seq) -> str:
    """Folge als Text: Kantennummer (ab 1) mit Richtung + oder -."""
    return " ".join(f"{e + 1}{'+' if o == 0 else '-'}" for e, o in seq)


def parse_sequence(text: str, m: int):
    """Liest eine Folge wie „3+ 1- 2“ (Kantennummern ab 1, + oder − (auch -) für die Richtung, ohne Zeichen: +). Rückgabe (Bögen, None) oder (None, Fehlertext)."""
    tokens = text.replace(",", " ").replace("−", "-").split()
    arcs = []
    for t in tokens:
        sign = 0
        body = t
        if t[-1] in "+-":
            sign = 1 if t[-1] == "-" else 0
            body = t[:-1]
        if not body.isdigit() or not 1 <= int(body) <= m:
            return None, f"„{t}“ ist keine Kantennummer von 1 bis {m} (mit + oder − für die Richtung)."
        arcs.append((int(body) - 1, sign))
    if sorted(e for e, _ in arcs) != list(range(m)):
        return None, f"Die Folge muss jede der {m} Kanten genau einmal enthalten (jetzt {len(arcs)} Einträge)."
    return arcs, None


def default_sequence(a: Analysis) -> list:
    """Die optimalen Routen hintereinander: ihr Split liefert das Optimum."""
    return [arc for r in a.routes for arc in r]


@dataclass(frozen=True, eq=False)
class SequenceResult:
    cost: float
    blocks: list
    gap: float


def evaluate_sequence(a: Analysis, seq) -> SequenceResult:
    cost, blocks = S.split_arcs(a.inst, seq)
    return SequenceResult(cost, blocks, gap_percent(cost, a.opt))


# ----------------------------------------------------------------------------------------------------------------------------------- Experiment 2: Richtung zählt

@dataclass(frozen=True, eq=False)
class OrientationView:
    order: tuple
    costs: list              # Kosten aller 2^m Richtungswahlen
    best: float
    worst: float
    optimal: int             # Zahl der Richtungswahlen mit Optimum
    set_price: float         # Blockpreis derselben Kantenfolge (Richtung und Reihenfolge im Block frei)


def orientation_view(a: Analysis, order) -> OrientationView:
    """Dieselbe Kantenfolge mit allen 2^m Richtungswahlen, jeweils mit Split."""
    m = a.inst.m
    costs = [S.split_cost(a.inst, list(zip(order, o))) for o in itertools.product((0, 1), repeat=m)]
    fin = [c for c in costs if c < INF]
    sp, _ = S.split_sets(a.ex, list(order))
    return OrientationView(tuple(order), costs, min(fin), max(fin), sum(1 for c in costs if abs(c - a.opt) < 1e-9), sp)


@dataclass(frozen=True, eq=False)
class Enumeration:
    m: int
    opt: float
    n_oriented: int
    opt_oriented: int
    min_oriented: float
    mean_oriented: float
    n_sets: int
    opt_sets: int
    min_sets: float
    mean_sets: float


@lru_cache(maxsize=16)
def enumerate_all(inst: Instance) -> Enumeration:
    """Alle Folgen (m ≤ ENUM_SHARE_M): alle orientierten Folgen mit Split und alle Kantenfolgen mit Blockpreis."""
    m = inst.m
    if m > C.ENUM_SHARE_M:
        raise ValueError(f"Aufzählung nur bis {C.ENUM_SHARE_M} Pflichtkanten")
    ex = _exact(inst)
    opt, _ = S.partition(ex)
    wl = S.limited(ex, inst.Q)
    perms = list(itertools.permutations(range(m)))
    ov = [S.split_cost(inst, list(zip(p, o))) for p in perms for o in itertools.product((0, 1), repeat=m)]
    sv = [S.split_sets_cost(wl, m, p) for p in perms]
    return Enumeration(m, opt, len(ov), sum(1 for v in ov if abs(v - opt) < 1e-9), min(ov), st.mean(ov), len(sv), sum(1 for v in sv if abs(v - opt) < 1e-9), min(sv), st.mean(sv))


# ----------------------------------------------------------------------------------------------------------------------------------- Experiment 3: Preis der Kapazität

def capacity_scan(a: Analysis) -> list[dict]:
    """Je Kapazität von der größten Nachfrage bis zur Gesamtnachfrage: Optimum, Routenzahl, Aufschlag gegen das Rural-Postman-Optimum."""
    q = a.inst.q
    out, seen = [], set()
    for Q in range(max(q), sum(q) + 1):
        opt, parts = S.partition(a.ex, Q)
        key = (round(opt, 9), len(parts))
        if key in seen and Q != a.inst.Q:
            continue
        seen.add(key)
        out.append({"Q": Q, "opt": opt, "routes": len(parts), "price": gap_percent(opt, a.w_all)})
    return out


# ----------------------------------------------------------------------------------------------------------------------------------- Experiment 4: Verfahren

@dataclass(frozen=True, eq=False)
class Methods:
    results: dict            # Schlüssel -> (Kosten, Routen als Bögen)
    opt: float

    def gap(self, key: str) -> float:
        return gap_percent(self.results[key][0], self.opt)


def run_methods(a: Analysis, k: int = C.RANDOM_K) -> Methods:
    """Alle Verfahren auf der Instanz; die Zufallsverfahren mit Random(Seed der Einstellungen), k Folgen."""
    inst, m = a.inst, a.inst.m
    rnd = random.Random(a.settings.seed)
    res = {"OPT": (a.opt, a.routes)}
    c, b = S.split_arcs(inst, S.rpp_sequence(a.ex))
    res["RPP"] = (c, b)
    c, b = S.split_arcs(inst, S.nn_sequence(inst))
    res["NN"] = (c, b)
    res["PS"] = S.path_scanning(inst)
    best = None
    first = None
    for i in range(k):
        seq = S.random_oriented(rnd, m)
        cost = S.split_cost(inst, seq)
        if i == 0:
            first = seq
        if best is None or cost < best[0] - 1e-12:
            best = (cost, seq)
    res["R1"] = S.split_arcs(inst, first)
    res["R200"] = S.split_arcs(inst, best[1])
    wl = S.limited(a.ex, inst.Q)
    bestset = None
    for _ in range(k):
        order = rnd.sample(range(m), m)
        cost = S.split_sets_cost(wl, m, order)
        if bestset is None or cost < bestset[0] - 1e-12:
            bestset = (cost, order)
    c, masks = S.split_sets(a.ex, bestset[1])
    res["BLK"] = (c, [a.ex.route_of(mk) for mk in masks])
    return Methods(res, a.opt)


# ----------------------------------------------------------------------------------------------------------------------------------- Bänder

@lru_cache(maxsize=1)
def load_bands() -> dict:
    path = Path(__file__).with_name(C.BAND_FILE)
    if not path.exists():
        return {"meta": {}, "carp": [], "enum": []}
    return json.loads(path.read_text(encoding="utf-8"))


def carp_rows(m: int) -> list[dict]:
    return [r for r in load_bands()["carp"] if r["m"] == m]


def enum_rows(m: int) -> list[dict]:
    return [r for r in load_bands()["enum"] if r["m"] == m]


BAND_KEYS = {"RPP": "rpp", "NN": "nn", "PS": "ps", "R1": "r1", "R200": "r200", "BLK": "blk"}


def carp_stats(m: int) -> dict:
    """Je Verfahren: Mittel, Median, Maximum der Lücke zum Optimum in Prozent und die Zahl der Instanzen mit dem Optimum; dazu der Preis der Kapazität."""
    rows = carp_rows(m)
    if not rows:
        return {}
    out = {"count": len(rows)}
    for key, field in BAND_KEYS.items():
        v = [gap_percent(r[field], r["opt"]) for r in rows]
        out[key] = {"mean": st.mean(v), "median": st.median(v), "max": max(v), "optimal": sum(1 for x in v if x <= C.TOL)}
    price = [gap_percent(r["opt"], r["w_all"]) for r in rows]
    out["price"] = {"mean": st.mean(price), "median": st.median(price), "max": max(price)}
    out["routes"] = {"mean": st.mean(r["routes"] for r in rows)}
    return out


def dominance_stats() -> dict:
    """m = 5: in wie vielen Instanzen ist das Minimum über alle orientierten Folgen (und alle Kantenfolgen mit Blockpreis) das exakte Optimum?"""
    rows = enum_rows(5)
    return {"count": len(rows), "oriented": sum(1 for r in rows if abs(r["min_oriented"] - r["opt"]) < 1e-9), "sets": sum(1 for r in rows if abs(r["min_sets"] - r["opt"]) < 1e-9),
            "n_oriented": rows[0]["n_oriented"] if rows else 0, "n_sets": rows[0]["n_sets"] if rows else 0}


def share_stats() -> dict:
    """m = 6: Anteil optimaler Folgen (Median, kleinster, größter) und Lücke zufälliger Folgen (Mittel), orientiert gegen Blockpreis."""
    rows = enum_rows(6)
    if not rows:
        return {}
    so = [r["opt_oriented"] / r["n_oriented"] for r in rows]
    ss = [r["opt_sets"] / r["n_sets"] for r in rows]
    return {"count": len(rows), "n_oriented": rows[0]["n_oriented"], "n_sets": rows[0]["n_sets"],
            "oriented": {"median": 100 * st.median(so), "min": 100 * min(so), "max": 100 * max(so), "gap": st.mean(gap_percent(r["mean_oriented"], r["opt"]) for r in rows)},
            "sets": {"median": 100 * st.median(ss), "min": 100 * min(ss), "max": 100 * max(ss), "gap": st.mean(gap_percent(r["mean_sets"], r["opt"]) for r in rows)}}


# ----------------------------------------------------------------------------------------------------------------------------------- Verdikte

def verdict_sequence(a: Analysis, res: SequenceResult) -> tuple[str, str]:
    if res.cost == INF:
        return "warning", "Keine zulässige Zerlegung: eine Kante hat mehr Nachfrage als die Kapazität."
    k = len(res.blocks)
    if abs(res.cost - a.opt) <= C.TOL:
        return "success", f"Der Split dieser Folge trifft das Optimum: {de(res.cost)} mit {routes_word(k)} (Optimum {de(a.opt)} mit {routes_word(len(a.routes))})."
    return "info", (f"Der Split dieser Folge liefert {de(res.cost)} mit {routes_word(k)}, {pct(res.gap)} über dem Optimum {de(a.opt)} ({routes_word(len(a.routes))}). "
                    f"Der Rural-Postman-Weg ohne Kapazität kostet {de(a.w_all)}: die Kapazität verteuert das Optimum um {pct(a.capacity_price)}.")


def verdict_orientation(a: Analysis, v: OrientationView) -> tuple[str, str]:
    n = len(v.costs)
    text = (f"Dieselbe Kantenfolge mit allen {n} Richtungswahlen: der beste Split kostet {de(v.best)}, der schlechteste {de(v.worst)} ({pct(gap_percent(v.worst, v.best))} mehr); "
            f"{v.optimal} von {n} Richtungswahlen treffen das Optimum {de(a.opt)}. Mit dem Blockpreis (Richtung und Reihenfolge im Block frei) kostet dieselbe Kantenfolge {de(v.set_price)}.")
    return "info", text


def verdict_share(e: Enumeration) -> tuple[str, str]:
    return "info", (f"Bei {e.m} Pflichtkanten sind {e.opt_oriented} von {e.n_oriented} orientierten Folgen optimal ({pct(100 * e.opt_oriented / e.n_oriented, 2)}), aber {e.opt_sets} von {e.n_sets} Kantenfolgen mit Blockpreis "
                    f"({pct(100 * e.opt_sets / e.n_sets)}). Eine zufällige orientierte Folge liegt im Mittel {pct(gap_percent(e.mean_oriented, e.opt))} über dem Optimum, eine zufällige Kantenfolge mit Blockpreis {pct(gap_percent(e.mean_sets, e.opt))}.")


def verdict_capacity(a: Analysis, scan: list[dict]) -> tuple[str, str]:
    cur = next(r for r in scan if r["Q"] == a.inst.Q)
    lo, hi = scan[0], scan[-1]
    return "info", (f"Bei der Kapazität {cur['Q']} kostet das Optimum {de(cur['opt'])} mit {routes_word(cur['routes'])}, {pct(cur['price'])} mehr als der Rural-Postman-Weg ({de(a.w_all)}). "
                    f"Bei der kleinsten möglichen Kapazität {lo['Q']} sind es {pct(lo['price'])} ({routes_word(lo['routes'])}), ab Kapazität {hi['Q']} genügt eine Route ({pct(hi['price'])}).")


def verdict_methods(a: Analysis, m: Methods) -> tuple[str, str]:
    order = sorted(C.HEURISTICS, key=lambda k: m.results[k][0])
    best = order[0]
    runner = order[1]
    kind = "success" if m.gap(best) <= C.TOL else "info"
    return kind, (f"Am besten ist {C.METHODS[best][0]} ({de(m.results[best][0])}, {pct(m.gap(best))} über dem Optimum {de(m.opt)}), danach {C.METHODS[runner][0]} ({pct(m.gap(runner))}). "
                  f"Eine zufällige orientierte Folge allein liegt {pct(m.gap('R1'))} über dem Optimum.")


def verdict_dominance(inst: Instance, e: Enumeration) -> tuple[str, str]:
    ok_o, ok_s = abs(e.min_oriented - e.opt) < 1e-9, abs(e.min_sets - e.opt) < 1e-9
    kind = "success" if ok_o and ok_s else "warning"
    return kind, (f"Über alle {e.n_oriented} orientierten Folgen von {e.m} Pflichtkanten ist der beste Split {de(e.min_oriented)} (Optimum {de(e.opt)}): {'gleich' if ok_o else 'nicht gleich'}; "
                  f"über alle {e.n_sets} Kantenfolgen mit Blockpreis {de(e.min_sets)}: {'gleich' if ok_s else 'nicht gleich'}.")


def verdict_bands(m: int) -> tuple[str, str]:
    s = carp_stats(m)
    if not s:
        return "warning", "Keine vorberechneten Bänder gefunden (generate_precomputed.py ausführen)."
    order = sorted(C.HEURISTICS, key=lambda k: s[k]["mean"])
    best = order[0]
    return "info", (f"Bei {m} Pflichtkanten ({instances_word(s['count'])}): am besten {C.METHODS[best][0]} mit im Mittel {pct(s[best]['mean'])} über dem Optimum (Optimum in {s[best]['optimal']} von {s['count']}), "
                    f"der Rural-Postman-Weg + Split {pct(s['RPP']['mean'])}, Path-Scanning {pct(s['PS']['mean'])}. Preis der Kapazität gegen den Postboten: im Mittel {pct(s['price']['mean'])}. "
                    f"Das Optimum gilt nur bis {C.BAND_SIZES[-1]} Pflichtkanten; ein Lauf je Instanz und Verfahren.")
