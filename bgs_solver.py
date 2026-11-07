"""Löser: exakte Dynamische Programmierung, Riesentour auf Bögen mit Split, Blockpreis, Konstruktionen.

Exakt: ein DP über (Menge bedienter Kanten, letzter Bogen) liefert für jede Kantenmenge S die kürzeste Route w[S] (ohne Kapazitätsgrenze; sie hängt nicht von der Kapazität ab); eine Partitions-DP
darüber liefert das Optimum mit Kapazität. Ohne Kapazität ist w[alle] das Rural-Postman-Optimum (Pflichtkanten, Depot, Leerfahrten).

Riesentour auf Bögen: eine Folge orientierter Pflichtkanten; Split: zusammenhängende Blöcke, Kosten Depot -> erster Bogen + Dienst + Leerfahrten + letzter Bogen -> Depot, Last <= Q.
Blockpreis: eine Folge von Kanten ohne Richtung, jeder Block kostet w[Menge seiner Kanten] (beste Reihenfolge und Richtungen im Block)."""

import math
from dataclasses import dataclass

import bgs_constants as C
from bgs_model import INF, Instance, ends, paths


def arcs_of(m: int) -> list[tuple[int, int]]:
    return [(e, o) for e in range(m) for o in (0, 1)]


@dataclass(frozen=True, eq=False)
class Exact:
    inst: Instance
    w: list                    # w[Maske]: kürzeste Route der Kantenmenge (ohne Kapazität)
    dp: dict                   # (Maske, Bogenindex) -> (Kosten, Vorgänger)
    last: dict                 # Maske -> Bogenindex des letzten Bogens der kürzesten Route

    def route_of(self, mask: int) -> list[tuple[int, int]]:
        """Die kürzeste Route der Kantenmenge als Folge von Bögen."""
        arcs = arcs_of(self.inst.m)
        seq, key = [], (mask, self.last[mask])
        while key is not None:
            seq.append(arcs[key[1]])
            key = self.dp[key][1]
        return seq[::-1]


def exact(inst: Instance) -> Exact:
    m, c = inst.m, inst.cost
    D, _ = paths(inst)
    arcs = arcs_of(m)
    st_, en = [ends(inst, a)[0] for a in arcs], [ends(inst, a)[1] for a in arcs]
    full = (1 << m) - 1
    dp: dict = {}
    for ai, (e, o) in enumerate(arcs):
        dp[(1 << e, ai)] = (D[0][st_[ai]] + c[e], None)
    for mask in range(1, full + 1):
        for ai, (e, o) in enumerate(arcs):
            if not mask >> e & 1 or (mask, ai) not in dp:
                continue
            base = dp[(mask, ai)][0]
            for bi, (f, p) in enumerate(arcs):
                if mask >> f & 1:
                    continue
                key = (mask | 1 << f, bi)
                v = base + D[en[ai]][st_[bi]] + c[f]
                if key not in dp or v < dp[key][0]:
                    dp[key] = (v, (mask, ai))
    w, last = [INF] * (full + 1), {}
    w[0] = 0.0
    for mask in range(1, full + 1):
        best = INF
        for ai in range(2 * m):
            if (mask, ai) in dp:
                v = dp[(mask, ai)][0] + D[en[ai]][0]
                if v < best:
                    best, last[mask] = v, ai
        w[mask] = best
    return Exact(inst, w, dp, last)


def demand_of(inst: Instance) -> list[int]:
    return [sum(inst.q[e] for e in range(inst.m) if mask >> e & 1) for mask in range(1 << inst.m)]


def limited(ex: Exact, Q: int) -> list:
    """Kosten der Mengen mit Kapazität Q: w[S], wenn die Nachfrage von S höchstens Q ist, sonst unendlich."""
    dem = demand_of(ex.inst)
    return [ex.w[mask] if dem[mask] <= Q else INF for mask in range(len(ex.w))]


def partition(ex: Exact, Q: int | None = None) -> tuple[float, list[int]]:
    """Optimum mit Kapazität Q (Voreinstellung: die der Instanz) und seine Zerlegung in Kantenmengen (Bitmasken, Reihenfolge nach dem kleinsten Element)."""
    inst = ex.inst
    wl = limited(ex, inst.Q if Q is None else Q)
    full = (1 << inst.m) - 1
    f = [INF] * (full + 1)
    choice = [0] * (full + 1)
    f[0] = 0.0
    for mask in range(1, full + 1):
        low = mask & -mask
        sub = mask
        while sub:
            if sub & low and wl[sub] < INF and f[mask ^ sub] + wl[sub] < f[mask] - 1e-12:
                f[mask] = f[mask ^ sub] + wl[sub]
                choice[mask] = sub
            sub = (sub - 1) & mask
    parts, mask = [], full
    while mask:
        parts.append(choice[mask])
        mask ^= choice[mask]
    return f[full], sorted(parts, key=lambda x: x & -x)


def rpp_sequence(ex: Exact) -> list[tuple[int, int]]:
    """Der Rural-Postman-Weg: die kürzeste Route über alle Pflichtkanten (Kapazität ignoriert) als orientierte Folge."""
    return ex.route_of((1 << ex.inst.m) - 1)


# ----------------------------------------------------------------------------------------------------------------------------------------- Split

def block_cost(inst: Instance, arcs) -> float:
    """Kosten einer Route aus Bögen in dieser Reihenfolge: Depot -> erster Bogen, Dienst, Leerfahrten, letzter Bogen -> Depot."""
    D, _ = paths(inst)
    c = inst.cost
    a0, _ = ends(inst, arcs[0])
    total = D[0][a0] + c[arcs[0][0]]
    for x, y in zip(arcs, arcs[1:]):
        total += D[ends(inst, x)[1]][ends(inst, y)[0]] + c[y[0]]
    return total + D[ends(inst, arcs[-1])[1]][0]


def split_arcs(inst: Instance, seq) -> tuple[float, list[list[tuple[int, int]]]]:
    """Zerlegung einer Folge orientierter Pflichtkanten: kürzester Weg, Block (i..j) = Route ab Depot (Last <= Q). Rückgabe (Kosten, Blöcke); ohne zulässige Zerlegung (Nachfrage über Q) unendlich."""
    D, _ = paths(inst)
    c, q, Q = inst.cost, inst.q, inst.Q
    L = len(seq)
    best = [INF] * (L + 1)
    pred = [0] * (L + 1)
    best[0] = 0.0
    for i in range(L):
        load, cost = 0, 0.0
        for j in range(i, L):
            e = seq[j][0]
            load += q[e]
            if load > Q:
                break
            a, b = ends(inst, seq[j])
            if j == i:
                cost = D[0][a] + c[e]
            else:
                cost += D[ends(inst, seq[j - 1])[1]][a] + c[e]
            v = best[i] + cost + D[b][0]
            if v < best[j + 1] - 1e-12:
                best[j + 1] = v
                pred[j + 1] = i
    blocks, node = [], L
    if best[L] == INF:
        return INF, []
    while node > 0:
        blocks.append(list(seq[pred[node]:node]))
        node = pred[node]
    return best[L], blocks[::-1]


def split_cost(inst: Instance, seq) -> float:
    """Wie split_arcs, nur die Kosten (schneller: ohne Rückverfolgung)."""
    D, _ = paths(inst)
    c, q, Q = inst.cost, inst.q, inst.Q
    L = len(seq)
    best = [INF] * (L + 1)
    best[0] = 0.0
    st_ = [ends(inst, s) for s in seq]
    for i in range(L):
        load, cost = 0, 0.0
        for j in range(i, L):
            e = seq[j][0]
            load += q[e]
            if load > Q:
                break
            a, b = st_[j]
            cost = D[0][a] + c[e] if j == i else cost + D[st_[j - 1][1]][a] + c[e]
            v = best[i] + cost + D[b][0]
            if v < best[j + 1]:
                best[j + 1] = v
    return best[L]


def split_sets(ex: Exact, order, Q: int | None = None) -> tuple[float, list[int]]:
    """Zerlegung einer Kantenfolge (ohne Richtung) mit dem Blockpreis w[Menge]; Rückgabe (Kosten, Bitmasken der Blöcke)."""
    inst = ex.inst
    m = inst.m
    wl = limited(ex, inst.Q if Q is None else Q)
    best = [INF] * (m + 1)
    pred = [0] * (m + 1)
    best[0] = 0.0
    for i in range(m):
        if best[i] == INF:
            continue
        mask = 0
        for j in range(i, m):
            mask |= 1 << order[j]
            if wl[mask] < INF and best[i] + wl[mask] < best[j + 1] - 1e-12:
                best[j + 1] = best[i] + wl[mask]
                pred[j + 1] = i
    blocks, node = [], m
    if best[m] == INF:
        return INF, []
    while node > 0:
        mask = 0
        for k in order[pred[node]:node]:
            mask |= 1 << k
        blocks.append(mask)
        node = pred[node]
    return best[m], blocks[::-1]


def split_sets_cost(wl, m: int, order) -> float:
    """Kosten der Zerlegung einer Kantenfolge mit dem Blockpreis (wl = limited(...) vorab berechnet)."""
    best = [INF] * (m + 1)
    best[0] = 0.0
    for i in range(m):
        if best[i] == INF:
            continue
        mask = 0
        for j in range(i, m):
            mask |= 1 << order[j]
            if wl[mask] < INF and best[i] + wl[mask] < best[j + 1]:
                best[j + 1] = best[i] + wl[mask]
    return best[m]


# ----------------------------------------------------------------------------------------------------------------------------------------- Konstruktionen

def nn_sequence(inst: Instance) -> list[tuple[int, int]]:
    """Nächster Nachbar auf Bögen: ab dem Depot immer die nächste unbediente Kante (Richtung: näheres Ende zuerst; Gleichstand: kleinere Kantennummer, dann Richtung 0)."""
    D, _ = paths(inst)
    left, pos, seq = set(range(inst.m)), 0, []
    while left:
        best = None
        for e in sorted(left):
            for o in (0, 1):
                a, b = ends(inst, (e, o))
                v = D[pos][a]
                if best is None or v < best[0] - 1e-12:
                    best = (v, (e, o), b)
        seq.append(best[1])
        left.remove(best[1][0])
        pos = best[2]
    return seq


def path_scanning(inst: Instance) -> tuple[float, list[list[tuple[int, int]]]]:
    """Path-Scanning (Golden, DeArmon, Baker 1983, nach der Idee, vereinfacht auf eine Regel): Routen nacheinander füllen; von der aktuellen Position die nächste Kante, die noch passt
    (Gleichstand: das größere Verhältnis Nachfrage zu Kosten). Rückgabe (Kosten, Routen als Bögen)."""
    D, _ = paths(inst)
    c, q, Q = inst.cost, inst.q, inst.Q
    left, total, routes = set(range(inst.m)), 0.0, []
    while left:
        pos, load, route = 0, 0, []
        while True:
            cands = [(D[pos][ends(inst, (e, o))[0]], -q[e] / c[e], e, o) for e in sorted(left) for o in (0, 1) if load + q[e] <= Q]
            if not cands:
                break
            d, _r, e, o = min(cands)
            a, b = ends(inst, (e, o))
            total += d + c[e]
            load += q[e]
            pos = b
            left.remove(e)
            route.append((e, o))
        total += D[pos][0]
        routes.append(route)
    return total, routes


def random_oriented(rnd, m: int) -> list[tuple[int, int]]:
    """Eine zufällige orientierte Folge: erst die Reihenfolge (Zufallsstichprobe), dann je Kante eine Richtung (in dieser Reihenfolge gezogen)."""
    return [(e, rnd.randint(0, 1)) for e in rnd.sample(range(m), m)]


def route_segments(inst: Instance, arcs) -> list[tuple[str, list[int]]]:
    """Für die Karte: die Route als Abschnitte ('dienst', [a, b]) und ('leer', Knotenfolge) ab dem Depot bis zurück zum Depot."""
    from bgs_model import shortest_path
    out, pos = [], 0
    for arc in arcs:
        a, b = ends(inst, arc)
        if pos != a:
            out.append(("leer", shortest_path(inst, pos, a)))
        out.append(("dienst", [a, b]))
        pos = b
    if pos != 0:
        out.append(("leer", shortest_path(inst, pos, 0)))
    return out


def plan_cost(inst: Instance, routes) -> float:
    return sum(block_cost(inst, r) for r in routes)


def is_valid_plan(inst: Instance, routes) -> bool:
    """Unabhängiger Prüfer: jede Pflichtkante genau einmal, keine Route über der Kapazität."""
    seen = sorted(e for r in routes for e, _ in r)
    return seen == list(range(inst.m)) and all(sum(inst.q[e] for e, _ in r) <= inst.Q for r in routes if r)


def finite(x: float) -> bool:
    return not math.isinf(x)
