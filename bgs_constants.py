"""Konstanten: Regler-Grenzen, Verfahren, Bänder, Farben und Presets."""

M_MIN, M_MAX, DEFAULT_M = 2, 10, 5                # Pflichtkanten (live exakt bis 10)
NODES_MIN, NODES_MAX, DEFAULT_NODES = 6, 9, 8
ROUTES_MIN, ROUTES_MAX, DEFAULT_ROUTES = 1, 4, 2  # Zielroutenzahl: legt die Kapazität fest
SEED_MAX, DEFAULT_SEED = 999999, 0
FAMILIES = ("Handinstanz (5 Pflichtkanten)", "Zufälliger Graph")
HAND_FAMILY = 0
DEFAULT_FAMILY = HAND_FAMILY
TOL = 1e-9                                         # Gleichstände und Gleichheit von Kosten: absolut
LEVEL_PP = 0.5                                     # „gleichauf“: Unterschied unter einem halben Prozentpunkt
ENUM_M = 5                                         # Aufzählung aller orientierten Folgen live bis zu dieser Größe (Experiment 5)
ENUM_SHARE_M = 6                                   # Aufzählung zur Seltenheit live bis zu dieser Größe (Experiment 2)
EXACT_LIVE_M = 10                                  # exaktes Verfahren live bis zu dieser Größe

# Handinstanz (Raster, ganzzahlige Kosten): Knoten 0 (Depot) bis 5, Kanten mit euklidischen Kosten, fünf Pflichtkanten
HAND_PTS = ((0.0, 0.0), (4.0, 0.0), (4.0, 3.0), (0.0, 3.0), (8.0, 0.0), (8.0, 3.0))
HAND_EDGES = ((0, 1), (1, 2), (2, 3), (0, 3), (1, 4), (4, 5), (2, 5), (0, 2))
HAND_REQ = ((1, 2), (2, 3), (4, 5), (1, 4), (2, 5))
HAND_Q_DEMAND = (2, 3, 2, 2, 3)
HAND_CAPACITY = 6

# Verfahren: Schlüssel, Namen, Farben
METHODS = {
    "OPT": ("Optimum (exakt)", "#222222"),
    "BLK": ("Bestes von 200 Kantenfolgen + Blockpreis", "#2F6B65"),
    "RPP": ("Rural-Postman-Weg + Split", "#4c78a8"),
    "NN": ("Nächster Nachbar auf Bögen + Split", "#d8a13a"),
    "PS": ("Path-Scanning (vereinfacht)", "#b5651d"),
    "R200": ("Bestes von 200 orientierten Folgen + Split", "#c0504d"),
    "R1": ("Eine zufällige orientierte Folge + Split", "#c9b6e4"),
}
HEURISTICS = tuple(k for k in METHODS if k != "OPT")
RANDOM_K = 200
BAND_SIZES = (10, 12)
BAND_COUNT = 16
BAND_NODES, BAND_ROUTES = 9, 3
BAND_FILE = "bgs_bands.json"
ENUM5_COUNT, ENUM6_COUNT = 20, 12

ROUTE_COLORS = ("#2F6B65", "#c0504d", "#4c78a8", "#d8a13a", "#7b5ea7", "#8c564b", "#17becf", "#e377c2")
COLOR_REQ_OFF = "rgba(150,150,150,0.5)"

# Presets (die Zahlen in den Hilfetexten prüft tests/test_claims.py); das erste ist die Voreinstellung
PRESETS = {
    "Handinstanz: eine Folge von Hand": {"m": 5, "family": 0, "nodes": 8, "routes": 2, "seed": 0},
    "Die Richtung zählt (6 Pflichtkanten)": {"m": 6, "family": 1, "nodes": 8, "routes": 3, "seed": 2},
    "Die Kapazität kostet (10 Pflichtkanten)": {"m": 10, "family": 1, "nodes": 9, "routes": 3, "seed": 6},
    "Blockpreis gegen Konstruktion (10 Pflichtkanten)": {"m": 10, "family": 1, "nodes": 9, "routes": 3, "seed": 3},
}
PRESET_HELP = {
    "Handinstanz: eine Folge von Hand": "Graph mit 6 Knoten und 5 Pflichtkanten, Kapazität 6. Das Optimum kostet 42 mit zwei Routen (4+ 3+ 1-) und (5+ 2+); der Rural-Postman-Weg ohne Kapazität kostet 26 (das Optimum liegt 61,5 % darüber). "
                                        "Seine Folge liefert nach dem Split 44 (+4,8 %): die kürzeste Gesamtfolge ist nicht die beste Folge.",
    "Die Richtung zählt (6 Pflichtkanten)": "Zufälliger Graph, 8 Knoten, 6 Pflichtkanten, Seed 2. Von 46080 orientierten Folgen sind 16 optimal (0,03 %); mit dem Blockpreis (beste Reihenfolge und Richtung im Block) sind es 144 von 720 Kantenfolgen (20,0 %). "
                                            "Eine zufällige orientierte Folge liegt im Mittel 43,0 % über dem Optimum 533,58, eine zufällige Kantenfolge mit Blockpreis 16,8 %.",
    "Die Kapazität kostet (10 Pflichtkanten)": "Zufälliger Graph, 9 Knoten, 10 Pflichtkanten, Zielroutenzahl 3, Seed 6. Das Optimum kostet 737,88 mit 3 Routen, der Rural-Postman-Weg ohne Kapazität 453,69: die Kapazität verteuert den Postboten um 62,6 %. "
                                              "Der Rural-Postman-Weg + Split liegt 5,5 % über dem Optimum.",
    "Blockpreis gegen Konstruktion (10 Pflichtkanten)": "Zufälliger Graph, 9 Knoten, 10 Pflichtkanten, Zielroutenzahl 3, Seed 3. Das Optimum kostet 475,19. Das beste von 200 Kantenfolgen mit Blockpreis trifft es; der Rural-Postman-Weg + Split liegt 11,3 % darüber, "
                                                        "der nächste Nachbar 16,9 %, Path-Scanning 17,8 %, das beste von 200 orientierten Folgen 20,0 %, eine zufällige orientierte Folge 78,6 %.",
}
ASSUMPTIONS_MARKDOWN = """- **Eigene kleine Instanzen:** Graphen mit 6 bis 9 Knoten (jeder Knoten mit seinen zwei nächsten Nachbarn verbunden, dazu drei weitere Kanten), euklidische Kosten, 2 bis 12 Pflichtkanten mit Nachfrage 1 bis 5; keine CARP-Benchmarks (Eglese, Belenguer-Benavent, Golden u. a.).
- **Exaktes Optimum nur klein:** ein DP über (Kantenmenge, letzter Bogen) bis 12 Pflichtkanten (live bis 10); darüber ist nichts gerechnet. Der Blockpreis ist nur bei kleinen Blöcken exakt.
- **Ungerichtete Kanten, ein Depotknoten:** jede Pflichtkante wird in einer Richtung zu ihren Kantenkosten bedient; keine gerichteten Bögen, keine Wendekosten, keine Zeitfenster, keine Flottengrenze.
- **Path-Scanning vereinfacht:** nur eine Regel (nächste passende Kante, bei Gleichstand das größere Verhältnis Nachfrage zu Kosten), nicht die fünf des Originals; die Zahlen gelten für diese Fassung.
- **Rural-Postman-Weg exakt, nicht konstruiert:** die Vergleichsfolge ist die kürzeste Route über alle Pflichtkanten aus dem DP (kein Euler-Verfahren, keine Eulerisierung per Paarung).
- **Zufallsverfahren:** bestes von 200 Folgen mit festem Seed; ein Lauf je Instanz und Verfahren; 16 Instanzen je Größe, bei der Aufzählung 20 (5 Kanten) und 12 (6 Kanten).
- **Aussagen:** Mittelwerte, Mediane und Zählungen über wenige Instanzen; keine Aussage über Metaheuristiken für CARP (Hertz u. a.), die nicht nachgemessen sind.
"""
