# Bogenrouting mit Kapazität – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-bogen-split-demo.streamlit.app/)** -->

Zwölftes Stück der **Tourenbildung**-Linie in der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“ (Verfahren: **Riesentour und Split**, ein Verfahren mit wachsendem Beispiel; gelbes Stück). Die Stücke 1 bis 3 ([riesentour-split-demo](https://github.com/sebastian-hanisch/riesentour-split-demo), [riesentouren-erzeugen-demo](https://github.com/sebastian-hanisch/riesentouren-erzeugen-demo), [split-gegen-fuellen-demo](https://github.com/sebastian-hanisch/split-gegen-fuellen-demo)) zeigen, dass eine Reihenfolge aller Kunden genügt, weil der **Split** sie optimal in Routen zerlegt; Stück 6 ([sweep-cluster-first-demo](https://github.com/sebastian-hanisch/sweep-cluster-first-demo)) rechnet die beste Route je Gruppe. Hier wechseln die Kunden zu **Kanten**: ein Postbote oder Winterdienst muss jede Pflichtkante bedienen, aber die Fahrzeuge haben eine **Kapazität**. Ohne Kapazität ist das ein Problem für sich ([arc-routing-demo](https://github.com/sebastian-hanisch/arc-routing-demo)); mit Kapazität ist es das **CARP**.

## Kernfrage

Was ändert die Kapazität am Postboten, und trägt die Riesentour mit Split auf Bögen? Die Demo zeigt eine Folge orientierter Pflichtkanten von Hand mit Split, was die **Richtung** der Kanten kostet (Aufzählung aller Folgen), den **Preis der Kapazität** gegen den Postboten ohne Kapazität, sechs Verfahren im Vergleich (live bis 10 Pflichtkanten, Bänder bis 12) und die **Dominanz** (das Minimum über alle Folgen ist das Optimum).

## Modell

Ein zusammenhängender Graph mit Knoten in der Ebene (euklidische Kantenkosten), ein Depotknoten, m Pflichtkanten mit Nachfrage 1 bis 5, Fahrzeuge der Kapazität Q ohne Flottengrenze, Leerfahrten auf kürzesten Wegen; die Kapazität folgt aus der Zielroutenzahl (aufgerundet Gesamtnachfrage durch Zielroutenzahl plus 2). Eine Pflichtkante wird in **einer** Richtung bedient (Kosten = Kantenkosten); ein **Bogen** ist (Kante, Richtung). Eine **Riesentour** ist eine Folge orientierter Pflichtkanten; der **Split** zerlegt sie in zusammenhängende Blöcke (je eine Route ab dem Depot, Last höchstens Q) auf dem kürzesten Weg im Hilfsgraphen. Der **Blockpreis** zerlegt eine Kantenfolge **ohne Richtung** und bewertet jeden Block mit der besten Route seiner Kantenmenge (beste Reihenfolge und Richtungen, exakt über ein DP): die Rundreise je Cluster aus Stück 6. **Exakt:** ein DP über (Menge bedienter Kanten, letzter Bogen) liefert für jede Kantenmenge die kürzeste Route, eine Partitions-DP darüber das Optimum mit Kapazität; ohne Kapazität ist es der **Rural-Postman-Weg** (eine Route über alle Pflichtkanten).

## Methodik

- **Verfahren (6 und das Optimum):** Rural-Postman-Weg + Split (die kürzeste Gesamtfolge, dann zerlegt), nächster Nachbar auf Bögen + Split, Path-Scanning (vereinfacht auf eine Regel), eine zufällige orientierte Folge + Split, das beste von 200 orientierten Folgen + Split, das beste von 200 Kantenfolgen (ohne Richtung) mit Blockpreis.
- **Bänder:** je 16 Instanzen mit 10 und 12 Pflichtkanten (9 Knoten, Zielroutenzahl 3, Seeds 500 + 40 m + i), Lücke zum Optimum in Prozent; dazu die **Aufzählung** aller Folgen bei 5 Pflichtkanten (20 Instanzen, Dominanz) und 6 Pflichtkanten (12 Instanzen, Seltenheit). Zufallsverfahren mit festem Seed, ein Lauf je Instanz.
- **Live:** das exakte Verfahren und alle Verfahren der Instanz bis 10 Pflichtkanten; die Aufzählung aller Folgen bis 6 (Seltenheit) und 5 (Dominanz).

## Befunde (gemessen, keine Behauptungen)

**1. Die Dominanz gilt auf Bögen, in beiden Fassungen.** Bei 5 Pflichtkanten ist das Minimum über alle 3840 orientierten Folgen das exakte Optimum in 20 von 20 Instanzen, und das Minimum über alle 120 Kantenfolgen mit Blockpreis ebenfalls in 20 von 20. Aus jeder zulässigen Lösung entsteht durch Aneinanderhängen der Routen eine Folge, deren Split sie wiederfindet.

**2. Die Richtung zerstört die Seltenheit.** Bei 6 Pflichtkanten (12 Instanzen; 46080 orientierte Folgen, 720 Kantenfolgen):

| | orientierte Folgen | Kantenfolgen mit Blockpreis |
|---|---|---|
| Anteil optimaler Folgen, Median (kleinster bis größter) | 0,19 % (0,02 % bis 2,64 %) | 20,0 % (6,7 % bis 64,4 %) |
| Lücke einer zufälligen Folge, Mittel | 36,9 % | 13,2 % |

**3. Verfahren, Lücke zum Optimum** (Mittel über 16 Instanzen, in Klammern die Zahl der Instanzen mit dem Optimum):

| Verfahren | 10 Pflichtkanten | 12 Pflichtkanten |
|---|---|---|
| Rural-Postman-Weg + Split | 11,0 % (2) | 12,2 % (1) |
| Nächster Nachbar auf Bögen + Split | 13,1 % (1) | 12,6 % (0) |
| Path-Scanning (vereinfacht) | 18,6 % (1) | 22,7 % (0) |
| Eine zufällige orientierte Folge + Split | 76,6 % (0) | 91,4 % (0) |
| Bestes von 200 orientierten Folgen + Split | 28,7 % (0) | 40,0 % (0) |
| Bestes von 200 Kantenfolgen + Blockpreis | 1,5 % (9) | 2,6 % (6) |

Mit dem Blockpreis schlägt die zufällige Folge im Mittel jede Konstruktion (Path-Scanning, nächster Nachbar, der Rural-Postman-Weg + Split); die Zufallsfolge mit festen Richtungen verliert um Größenordnungen. Der Rural-Postman-Weg als Riesentour trifft das Optimum nur in 2 von 16 (10 Kanten) und 1 von 16 (12 Kanten) Instanzen: wie in Stück 1 ist die kürzeste Gesamtfolge nicht die beste Folge.

**4. Der Preis der Kapazität.** Das Optimum mit Kapazität liegt gegen den Rural-Postman-Weg (eine Route, Kapazität ignoriert) im Mittel 32,0 % höher bei 10 Pflichtkanten (Median 35,9 %, höchstens 55,3 %) und 20,0 % bei 12 (Median 17,0 %, höchstens 69,2 %); im Optimum sind es im Mittel 3,0 Routen.

**Handinstanz** (Raster mit 6 Knoten und 5 Pflichtkanten, Kapazität 6; ganzzahlige Kosten, von Hand nachrechenbar): Optimum 42 mit den Routen (4+ 3+ 1-) und (5+ 2+) (Längen 22 und 20); Rural-Postman-Weg ohne Kapazität 26 (das Optimum liegt 61,5 % darüber). Die Folge (2- 5+ 3- 4- 1+) liefert nach dem Split 44 (4,8 % über dem Optimum), die Folge (2- 1- 4+ 3+ 5-) 50. Optimum je Kapazität:

| Kapazität | Optimum | Routen | Aufschlag gegen den Postboten |
|---|---|---|---|
| 3 | 78,00 | 5 | 200,0 % |
| 4 | 62,00 | 4 | 138,5 % |
| 5 | 50,00 | 3 | 92,3 % |
| 6 | 42,00 | 2 | 61,5 % |
| 7 | 34,00 | 2 | 30,8 % |
| 12 | 26,00 | 1 | 0,0 % |

## Ehrliche Grenzen

- **Eigene kleine Instanzen:** Graphen mit 6 bis 9 Knoten (jeder Knoten mit seinen zwei nächsten Nachbarn verbunden, dazu drei weitere Kanten), euklidische Kosten, 2 bis 12 Pflichtkanten mit Nachfrage 1 bis 5; keine CARP-Benchmarks (Eglese, Belenguer-Benavent, Golden u. a.).
- **Exaktes Optimum nur klein:** ein DP über (Kantenmenge, letzter Bogen) bis 12 Pflichtkanten (live bis 10); darüber ist nichts gerechnet. Der Blockpreis ist nur bei kleinen Blöcken exakt.
- **Ungerichtete Kanten, ein Depotknoten:** jede Pflichtkante wird in einer Richtung zu ihren Kantenkosten bedient; keine gerichteten Bögen, keine Wendekosten, keine Zeitfenster, keine Flottengrenze.
- **Path-Scanning vereinfacht:** nur eine Regel (nächste passende Kante, bei Gleichstand das größere Verhältnis Nachfrage zu Kosten), nicht die fünf des Originals; die Zahlen gelten für diese Fassung.
- **Rural-Postman-Weg exakt, nicht konstruiert:** die Vergleichsfolge ist die kürzeste Route über alle Pflichtkanten aus dem DP (kein Euler-Verfahren, keine Eulerisierung per Paarung).
- **Zufallsverfahren:** bestes von 200 Folgen mit festem Seed; ein Lauf je Instanz und Verfahren; 16 Instanzen je Größe, bei der Aufzählung 20 (5 Kanten) und 12 (6 Kanten).
- **Aussagen:** Mittelwerte, Mediane und Zählungen über wenige Instanzen; keine Aussage über Metaheuristiken für CARP (Hertz u. a.), die nicht nachgemessen sind.

## Befunde und Korrekturen gegenüber dem Plan

- **Wie geplant gebaut:** Z95 bis Z102 wie empfohlen; die Zahlen der Phase 0 (`tb12_carp.py`) sind aus den Seeds identisch reproduziert (die Bänder stimmen mit der Messung der Planung überein).
- **Handinstanz mit ganzzahligen Kosten:** Der Plan sprach von einer Handinstanz „mit Wurzeln“; ein Raster mit Diagonalkante (3-4-5) liefert ganzzahlige Kosten und lässt sich ohne Wurzeln nachrechnen.
- **Kapazität mindestens die größte Nachfrage:** Der Generator der Planung konnte bei sehr kleinen Instanzen eine Kapazität unter der größten Nachfrage erzeugen (keine zulässige Lösung); `make_instance` hebt sie auf die größte Nachfrage an. Die Band-Instanzen sind davon nicht betroffen.
- **Nur Rural-Postman-Weg exakt:** Die Vergleichsfolge „Rural-Postman-Weg + Split“ stammt aus dem DP, nicht aus einem Euler-Verfahren; ein Euler-basierter Weg (Ulusoy) kann schlechter sein.

## Verifikation

- **Handwerte:** die Handinstanz mit Routen und Postbote von Hand (ganzzahlig), der Split zweier Folgen, die Kapazitätsreihe, Distanzen des Rasters (`tests/test_hand.py`).
- **Orakel:** das exakte Optimum und der Rural-Postman-Weg gegen die Aufzählung aller Zerlegungen mit allen Reihenfolgen und Richtungen (eigene kürzeste Wege in der Testdatei, m ≤ 5); der Split gegen die Aufzählung aller Schnitte; jedes Verfahren liefert Pläne, die jede Pflichtkante genau einmal bedienen, die Kapazität einhalten, mit gemessener Länge gleich den Kosten und nie unter dem Optimum; Dominanz über alle orientierten Folgen der Handinstanz (`tests/test_oracle.py`).
- **Eigenschaften:** Kapazität unendlich gibt den Rural-Postman-Weg mit einer Route; größere Kapazität nie teurer; Richtungsumkehr einer Route ändert die Länge nicht; Umnummerieren der Kanten ändert das Optimum nicht; der Blockpreis nie über jeder Orientierung derselben Folge; Zufallsverfahren reproduzierbar (`tests/test_properties.py`).
- **Randfälle:** 1 und 2 Pflichtkanten, Kapazität gleich der größten Nachfrage und sehr groß, Pflichtkante am Depot, Nachfrage über der Kapazität, schlechte Folgen im Eingabefeld, Zusammenhang der Graphen (`tests/test_edge_cases.py`).
- **Verdikte:** jede Verzweigung und jede Zahl im Text (`tests/test_verdicts.py`).
- **Zahlen der README und der Preset-Hilfen:** `tests/test_claims.py`; die vorberechneten Bänder auf Aufbau, Plausibilität und gegen eine frische Rechnung von Stichproben (`tests/test_bands.py`). Zeiten werden nirgends gemessen oder gespeichert.
- **Oberfläche:** AppTest-Rauchtest (jeder Button, jeder Regler am Minimum und Maximum), alle Experimente, Presets, PDF (`tests/test_app.py`, `tests/test_experiments.py`), Footer, Layout, Laufzeit-Importe.

## Tests

124 Tests. Laufzeit lokal etwa eine Minute.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Zwischenstände der Rechnung |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App |
| `bgs_bands.json` | vorberechnete Bänder (32 CARP-Zeilen mit 10 und 12 Pflichtkanten, 32 Aufzählungen mit 5 und 6 Pflichtkanten) |
| `bgs_constants.py` | Regler-Grenzen, Verfahren, Handinstanz, Presets, Annahmentext |
| `bgs_evaluation.py` | Analyse, Folge von Hand, Aufzählungen, Kapazitätsreihe, Verfahren, Bänder, Verdikt-Logik |
| `bgs_layout.py` | Fester Kopf und Tabellenregel (Stylesheet) |
| `bgs_model.py` | Graph, Pflichtkanten, kürzeste Wege, Instanzgenerator, Handinstanz |
| `bgs_pdf_export.py` | PDF-Export des Ergebnisses |
| `bgs_presets.py` | Permalink, Presets (Schnellstart in der Seitenleiste), Zufalls-Seed-Button |
| `bgs_solver.py` | exaktes DP, Split auf Bögen, Blockpreis, Konstruktionen |
| `bgs_visualization.py` | Plotly-Abbildungen (Karte, Histogramm, Balken; Achsen gesperrt) |
| `generate_precomputed.py` | erzeugt `bgs_bands.json` (bis zu 12 Prozesse) |
| `requirements-dev.txt` | Laufzeit plus pytest |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `tests/` | Handinstanz, Orakel, Eigenschaften, Randfälle, Verdikte, Claims, Bänder, Presets, Layout, AppTest, Footer, Laufzeit-Importe |

## Bewusst nicht umgesetzt

- **CARP-Benchmarks und untere Schranken:** keine Sätze geladen; Eglese, Belenguer-Benavent, Golden u. a. sind nicht gemessen.
- **Metaheuristiken für CARP** (Tabu-Suche, memetische Suche): nur die Folge mit Split als Zufallsverfahren, keine Suche.
- **Gerichtete Bögen, gemischte Graphen, Wendekosten, Zeitfenster, Flottengrenze:** Stücke 3, 8, 9 und spätere Erweiterungen.
- **Instanzen über 12 Pflichtkanten:** das exakte Verfahren und der Blockpreis wären zu teuer.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly, NumPy und fpdf2.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).
