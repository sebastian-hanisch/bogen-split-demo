"""Erzeugt bgs_bands.json: die Bänder des Bogenroutings mit Kapazität (Stück 12 der Linie Tourenbildung).

Inhalt: (1) CARP-Zeilen für m = 10 und 12 Pflichtkanten (je 16 Instanzen, 9 Knoten, Zielroutenzahl 3, Seeds 500 + 40 m + i): Optimum, Rural-Postman-Optimum ohne Kapazität, Rural-Postman-Weg + Split,
nächster Nachbar + Split, Path-Scanning, eine zufällige orientierte Folge, bestes von 200 orientierten Folgen, bestes von 200 Kantenfolgen mit Blockpreis; (2) Aufzählung aller orientierten Folgen und aller
Kantenfolgen mit Blockpreis bei m = 5 (20 Instanzen, Dominanz) und m = 6 (12 Instanzen, Seltenheit). Die Zeilen sind aus den Seeds reproduzierbar; keine Zeiten gespeichert.

Aufruf:
    python generate_precomputed.py            # rechnet alles (bis zu 12 Prozesse) und schreibt bgs_bands.json"""

import itertools
import json
import random
import statistics as st
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import bgs_constants as C
import bgs_solver as S
from bgs_model import make_instance

TARGET = Path(__file__).with_name(C.BAND_FILE)


def carp_row(args):
    m, i = args
    seed = 500 + 40 * m + i
    inst = make_instance(m, seed, C.BAND_NODES, C.BAND_ROUTES)
    ex = S.exact(inst)
    opt, parts = S.partition(ex)
    rnd = random.Random(i)
    wl = S.limited(ex, inst.Q)
    rands = [S.split_cost(inst, S.random_oriented(rnd, m)) for _ in range(C.RANDOM_K)]
    sets = [S.split_sets_cost(wl, m, rnd.sample(range(m), m)) for _ in range(C.RANDOM_K)]
    ps, _ = S.path_scanning(inst)
    print("carp", m, i, flush=True)
    return {"m": m, "i": i, "seed": seed, "Q": inst.Q, "qsum": sum(inst.q), "opt": opt, "routes": len(parts), "w_all": ex.w[(1 << m) - 1], "rpp": S.split_cost(inst, S.rpp_sequence(ex)),
            "nn": S.split_cost(inst, S.nn_sequence(inst)), "ps": ps, "r1": rands[0], "r200": min(rands), "blk": min(sets)}


def enum_row(args):
    m, seed, nodes, routes = args
    inst = make_instance(m, seed, nodes, routes)
    ex = S.exact(inst)
    opt, _ = S.partition(ex)
    wl = S.limited(ex, inst.Q)
    perms = list(itertools.permutations(range(m)))
    orients = list(itertools.product((0, 1), repeat=m))
    ov = [S.split_cost(inst, list(zip(p, o))) for p in perms for o in orients]
    sv = [S.split_sets_cost(wl, m, p) for p in perms]
    print("enum", m, seed, flush=True)
    return {"m": m, "seed": seed, "opt": opt, "n_oriented": len(ov), "opt_oriented": sum(1 for v in ov if abs(v - opt) < 1e-9), "min_oriented": min(ov), "mean_oriented": st.mean(ov),
            "n_sets": len(sv), "opt_sets": sum(1 for v in sv if abs(v - opt) < 1e-9), "min_sets": min(sv), "mean_sets": st.mean(sv)}


def main():
    carp_jobs = [(m, i) for m in C.BAND_SIZES for i in range(C.BAND_COUNT)]
    enum_jobs = [(5, i, 8, 2) for i in range(C.ENUM5_COUNT)] + [(6, 100 + i, 8, 3) for i in range(C.ENUM6_COUNT)]
    with ProcessPoolExecutor(max_workers=12) as pool:
        carp = list(pool.map(carp_row, carp_jobs))
        enum = list(pool.map(enum_row, enum_jobs))
    meta = {"nodes": C.BAND_NODES, "routes": C.BAND_ROUTES, "count": C.BAND_COUNT, "random_k": C.RANDOM_K, "enum5": [C.ENUM5_COUNT, 8, 2], "enum6": [C.ENUM6_COUNT, 8, 3]}
    TARGET.write_text(json.dumps({"meta": meta, "carp": carp, "enum": enum}, ensure_ascii=False), encoding="utf-8")
    print("geschrieben:", TARGET.name, len(carp), "CARP-Zeilen,", len(enum), "Aufzählungen")


if __name__ == "__main__":
    main()
