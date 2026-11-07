"""Modell: zusammenhängender Graph mit Knoten in der Ebene, Depotknoten 0, Pflichtkanten mit Nachfrage, Kapazität, kürzeste Wege als Leerfahrten. Alles simuliert.

Eine Pflichtkante wird in einer Richtung bedient (Kosten = Kantenkosten, euklidisch); ein Bogen ist (Kantennummer, Richtung): Richtung 0 bedient a -> b, Richtung 1 bedient b -> a.
Die Instanz ist hashbar (Tupel), damit Streamlit sie cachen kann."""

import math
import random
from dataclasses import dataclass
from functools import lru_cache

import bgs_constants as C

INF = math.inf


@dataclass(frozen=True)
class Instance:
    pts: tuple[tuple[float, float], ...]      # pts[0] = Depotknoten
    edges: tuple[tuple[int, int], ...]        # alle Kanten des Graphen (a < b)
    req: tuple[tuple[int, int], ...]          # Pflichtkanten (a, b)
    q: tuple[int, ...]                        # Nachfrage der Pflichtkanten
    Q: int                                    # Kapazität

    @property
    def m(self) -> int:
        return len(self.req)

    @property
    def n_nodes(self) -> int:
        return len(self.pts)

    def edge_cost(self, a: int, b: int) -> float:
        return math.dist(self.pts[a], self.pts[b])

    @property
    def cost(self) -> tuple[float, ...]:
        return tuple(self.edge_cost(a, b) for a, b in self.req)

    @property
    def min_routes(self) -> int:
        return math.ceil(sum(self.q) / self.Q)


@lru_cache(maxsize=256)
def paths(inst: Instance):
    """Kürzeste Wege (Floyd-Warshall): Entfernungsmatrix D und Nachfolgermatrix NXT (nächster Knoten auf dem kürzesten Weg von i nach j)."""
    n = inst.n_nodes
    D = [[INF] * n for _ in range(n)]
    nxt = [[-1] * n for _ in range(n)]
    for i in range(n):
        D[i][i] = 0.0
        nxt[i][i] = i
    for a, b in inst.edges:
        c = inst.edge_cost(a, b)
        D[a][b] = D[b][a] = c
        nxt[a][b], nxt[b][a] = b, a
    for k in range(n):
        for i in range(n):
            for j in range(n):
                if D[i][k] + D[k][j] < D[i][j] - 1e-12:
                    D[i][j] = D[i][k] + D[k][j]
                    nxt[i][j] = nxt[i][k]
    return D, nxt


def shortest_path(inst: Instance, a: int, b: int) -> list[int]:
    """Knotenfolge des kürzesten Wegs von a nach b (einschließlich beider Enden)."""
    _, nxt = paths(inst)
    out = [a]
    while out[-1] != b:
        out.append(nxt[out[-1]][b])
    return out


def connected(n: int, edges) -> bool:
    adj = {i: set() for i in range(n)}
    for a, b in edges:
        adj[a].add(b)
        adj[b].add(a)
    seen, todo = {0}, [0]
    while todo:
        for j in adj[todo.pop()]:
            if j not in seen:
                seen.add(j)
                todo.append(j)
    return len(seen) == n


def hand_instance() -> Instance:
    return Instance(C.HAND_PTS, tuple((min(a, b), max(a, b)) for a, b in C.HAND_EDGES), C.HAND_REQ, C.HAND_Q_DEMAND, C.HAND_CAPACITY)


def make_instance(m: int, seed: int, nodes: int = 9, routes: int = 3) -> Instance:
    """Deterministisch aus (Pflichtkanten, Seed, Knoten, Zielroutenzahl): jeder Knoten mit seinen zwei nächsten Nachbarn verbunden, dazu drei weitere Kanten; wird der Graph nicht zusammenhängend
    oder hat er weniger als m Kanten, wird der Seed um 1000 erhöht. m Pflichtkanten zufällig, Nachfrage 1 bis 5, Kapazität = aufgerundet Gesamtnachfrage durch Zielroutenzahl plus 2 (mindestens die größte Nachfrage)."""
    rnd = random.Random(seed)
    while True:
        pts = [(float(rnd.randint(0, 100)), float(rnd.randint(0, 100))) for _ in range(nodes)]
        edges = set()
        for i in range(nodes):
            near = sorted(range(nodes), key=lambda j: math.dist(pts[i], pts[j]))[1:3]
            for j in near:
                edges.add((min(i, j), max(i, j)))
        extra = [(i, j) for i in range(nodes) for j in range(i + 1, nodes) if (i, j) not in edges]
        rnd.shuffle(extra)
        edges |= set(extra[:3])
        edges = sorted(edges)
        if connected(nodes, edges) and len(edges) >= m:
            break
        seed += 1000
        rnd = random.Random(seed)
    req = rnd.sample(edges, m)
    q = [rnd.randint(1, 5) for _ in range(m)]
    return Instance(tuple(pts), tuple(edges), tuple(req), tuple(q), max(math.ceil(sum(q) / routes) + 2, max(q)))


def ends(inst: Instance, arc) -> tuple[int, int]:
    """(Startknoten, Endknoten) eines Bogens (Kantennummer, Richtung)."""
    e, o = arc
    a, b = inst.req[e]
    return (a, b) if o == 0 else (b, a)
