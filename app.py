"""Bogenrouting mit Kapazität: Riesentour über Pflichtkanten - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Stück 12 der Reihe „Tourenbildung“: Was ändert die Kapazität am Postboten, und trägt die Riesentour mit Split auf Bögen? Die Demo zeigt eine Folge von Hand mit Split, was die Richtung der Kanten kostet, den Preis der Kapazität,
die Verfahren im Vergleich und die Dominanz (das Minimum über alle Folgen ist das Optimum), dazu vorberechnete Bänder bis 12 Pflichtkanten.

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import bgs_constants as C
from bgs_evaluation import (
    Settings,
    analyse,
    build_instance,
    capacity_scan,
    carp_stats,
    de,
    dominance_stats,
    enumerate_all,
    evaluate_sequence,
    default_sequence,
    instances_word,
    orientation_view,
    parse_sequence,
    pct,
    routes_word,
    run_methods,
    sequence_text,
    share_stats,
    signed_pct,
    verdict_bands,
    verdict_capacity,
    verdict_dominance,
    verdict_methods,
    verdict_orientation,
    verdict_sequence,
    verdict_share,
)
from bgs_layout import dunkles_design, kopf_css
from bgs_pdf_export import build_pdf
from bgs_presets import (
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)
from bgs_solver import block_cost
from bgs_visualization import build_band_bars, build_histogram, build_map

st.set_page_config(page_title="Bogenrouting mit Kapazität – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return analyse(settings)


@st.cache_data(show_spinner=False)
def _methods(settings):
    return run_methods(analyse(settings))


@st.cache_data(show_spinner=False)
def _scan(settings):
    return capacity_scan(analyse(settings))


@st.cache_data(show_spinner=False)
def _enum(settings):
    return enumerate_all(build_instance(settings))


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in bgs_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("📬 Bogenrouting mit Kapazität")
st.markdown(
    """
**Was ändert die Kapazität am Postboten?** Ohne Kapazität ist die Rundtour über alle Pflichtkanten ein einziges Optimierungsproblem (Stück `arc-routing-demo`). Mit Kapazität teilt sich die Arbeit auf mehrere Routen ab dem Depot (**CARP**).
Das Rückgrat der Linie trägt auch hier, sofern die Richtung im Blockpreis mitentschieden wird (mit zufällig festgelegten Richtungen nicht): eine **Riesentour** ist eine Folge **orientierter Pflichtkanten**, der **Split** zerlegt sie optimal in Routen. Neu gegenüber den Kunden der früheren Stücke: jede Kante hat eine **Richtung**.

Weiter unten: **🔬 Eine Folge von Hand**, **🔬 Die Richtung zählt**, **🔬 Der Preis der Kapazität**, **🔬 Verfahren im Vergleich**, **🔬 Dominanz**, **🚧 Wo die Annahmen enden**,
der Expander **⚠️ Annahmen, Grenzen und bekannte Probleme** und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("So funktioniert es", expanded=True):
    st.markdown(
        """
1. **Bogen:** eine Pflichtkante mit Richtung; Kante 3 in Richtung + wird von ihrem ersten Endknoten zum zweiten bedient, in Richtung − umgekehrt. Dienst kostet die Kantenkosten, **Leerfahrten** laufen auf kürzesten Wegen.
2. **Split:** zerlegt eine Folge orientierter Kanten in zusammenhängende Blöcke; jeder Block ist eine Route ab dem Depot (Last höchstens Kapazität); der kürzeste Weg im Hilfsgraphen liefert die beste Zerlegung.
3. **Blockpreis:** Eine Folge von Kanten **ohne Richtung** wird zerlegt, und jeder Block kostet die beste Route seiner Kantenmenge (beste Reihenfolge und Richtungen). Das ist die Rundreise je Cluster aus Stück 6.
4. **Referenz:** das exakte Optimum (DP über Kantenmenge und letzten Bogen) bis 10 Pflichtkanten live, 12 in den Bändern.
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    family = st.selectbox("Graph", list(range(len(C.FAMILIES))), key="family_select", format_func=lambda i: C.FAMILIES[i],
                          help="„Handinstanz“: ein Raster mit 6 Knoten, 5 Pflichtkanten, Kapazität 6 (von Hand nachrechenbar). „Zufälliger Graph“: jeder Knoten mit seinen zwei nächsten Nachbarn verbunden, dazu drei Kanten.")
    hand = int(family) == C.HAND_FAMILY
    if hand:
        st.caption("Bei der Handinstanz gelten Pflichtkanten, Knoten, Zielroutenzahl und Seed nicht; der Seed legt nur den Zufall der Zufallsverfahren fest.")
    m = st.slider("Pflichtkanten", *bounds("m_slider"), key="m_slider", help=f"Das exakte Optimum rechnet die Seite bis {C.EXACT_LIVE_M} Pflichtkanten. Die Aufzählung aller Folgen bis {C.ENUM_SHARE_M} (Experiment 2) und {C.ENUM_M} (Experiment 5).")
    nodes = st.slider("Knoten", *bounds("nodes_slider"), key="nodes_slider", help="Zahl der Knoten des zufälligen Graphen (mit dem Depot).")
    routes = st.slider("Zielroutenzahl", *bounds("routes_slider"), key="routes_slider", help="Legt die Kapazität fest: aufgerundet Gesamtnachfrage durch Zielroutenzahl plus 2 (mindestens die größte Nachfrage).")
    seed = st.number_input("Zufalls-Seed der Instanz und der Zufallsverfahren", *bounds("seed_input"), key="seed_input", step=1, help="Der Seed legt den Graphen, die Pflichtkanten und ihre Nachfrage fest (außer bei der Handinstanz) und den Zufall der Zufallsverfahren.")
    st.button("🎲 Neue Instanz generieren", width="stretch", on_click=randomize_seed)

sync_query_params({"family_select": int(family), "m_slider": int(m), "nodes_slider": int(nodes), "routes_slider": int(routes), "seed_input": int(seed)})

settings = Settings(int(m), int(family), int(nodes), int(routes), int(seed))
a = _analysis(settings)
inst = a.inst
methods = _methods(settings)

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Ergebnis: Optimum und Preis der Kapazität")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Optimum (exakt)", de(a.opt))
c2.metric("Routen im Optimum", str(len(a.routes)))
c3.metric("Rural-Postman-Weg (ohne Kapazität)", de(a.w_all))
c4.metric("Preis der Kapazität", pct(a.capacity_price))
st.caption(f"{inst.m} Pflichtkanten, {inst.n_nodes} Knoten, Kapazität {inst.Q}, Gesamtnachfrage {sum(inst.q)}. Der Rural-Postman-Weg ist die kürzeste Route über alle Pflichtkanten, wenn die Kapazität nicht zählt (eine Route).")
st.plotly_chart(build_map(inst, a.routes), width="stretch", key="map_opt")
st.caption("Die optimalen Routen: dicke Linien mit Pfeil sind Dienst, gepunktete Linien Leerfahrten; die Zahl an jeder Pflichtkante ist ihre Nummer, q ihre Nachfrage.")
st.download_button("📄 Ergebnis als PDF", data=build_pdf(settings, a, methods), file_name="bogenrouting-mit-kapazitaet.pdf", mime="application/pdf", key="pdf_download")

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Trägt die Riesentour mit Split auf Bögen?")
kind, text = verdict_methods(a, methods)
getattr(st, kind)(text)

st.markdown("---")

# --- Experiment 1 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Eine Folge von Hand")
st.caption("Tragen Sie eine Folge der Pflichtkanten ein: Kantennummer mit + oder − für die Richtung (3+ 1- 2+ …), jede Kante genau einmal. Der Split zerlegt sie optimal in Routen. "
           "Voreingestellt sind die optimalen Routen hintereinander: ihr Split trifft das Optimum.")
sig = (settings.m, settings.family, settings.nodes, settings.routes, settings.seed)
if st.session_state.get("seq_sig") != sig:
    st.session_state["seq_sig"] = sig
    st.session_state["seq_text"] = sequence_text(default_sequence(a))
text_in = st.text_input("Folge", key="seq_text", help="Beispiel für die Handinstanz: 4+ 3+ 1- 5+ 2+")
seq, err = parse_sequence(text_in, inst.m)
if err:
    st.error(err)
    seq = default_sequence(a)
res = evaluate_sequence(a, seq)
x1, x2 = st.columns([1, 1])
with x1:
    st.markdown(f"**Split: {de(res.cost)}** ({routes_word(len(res.blocks))}), Optimum {de(a.opt)}")
    rows = ["| Route | Folge | Last | Länge |", "|---|---|---|---|"]
    for i, blk in enumerate(res.blocks, start=1):
        rows.append(f"| {i} | {sequence_text(blk)} | {sum(inst.q[e] for e, _ in blk)} von {inst.Q} | {de(block_cost(inst, blk))} |")
    st.markdown("\n".join(rows))
with x2:
    st.plotly_chart(build_map(inst, res.blocks, legend=False), width="stretch", key="map_seq")
kind, text = verdict_sequence(a, res)
getattr(st, kind)(text)

st.markdown("---")

# --- Experiment 2 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Die Richtung zählt")
st.caption("Links: dieselbe Kantenfolge aus Experiment 1 mit allen 2^m Richtungswahlen, jeweils mit Split. Darunter bei höchstens "
           f"{C.ENUM_SHARE_M} Pflichtkanten die Aufzählung **aller** Folgen: wie viele orientierte Folgen sind optimal, und wie viele Kantenfolgen mit Blockpreis?")
order = tuple(e for e, _ in seq)
ov = orientation_view(a, order)
st.plotly_chart(build_histogram(ov.costs, a.opt), width="stretch", key="hist_orient")
kind, text = verdict_orientation(a, ov)
getattr(st, kind)(text)
if inst.m <= C.ENUM_SHARE_M:
    enum = _enum(settings)
    kind, text = verdict_share(enum)
    getattr(st, kind)(text)
else:
    st.info(f"Die Aufzählung aller Folgen rechnet die Seite bis {C.ENUM_SHARE_M} Pflichtkanten (bei {inst.m} wären es {inst.m} ! mal 2^{inst.m} orientierte Folgen). Vorberechnet bei 6 Pflichtkanten:")
shares = share_stats()
if shares:
    st.markdown(f"| m = 6, {instances_word(shares['count'])} | orientierte Folgen ({shares['n_oriented']}) | Kantenfolgen mit Blockpreis ({shares['n_sets']}) |\n|---|---|---|\n"
                f"| Anteil optimaler Folgen, Median (kleinster bis größter) | {pct(shares['oriented']['median'], 2)} ({pct(shares['oriented']['min'], 2)} bis {pct(shares['oriented']['max'], 2)}) | {pct(shares['sets']['median'])} ({pct(shares['sets']['min'])} bis {pct(shares['sets']['max'])}) |\n"
                f"| Lücke einer zufälligen Folge, Mittel | {pct(shares['oriented']['gap'])} | {pct(shares['sets']['gap'])} |")

st.markdown("---")

# --- Experiment 3 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Der Preis der Kapazität")
st.caption("Dieselbe Instanz mit jeder Kapazität von der größten Nachfrage bis zur Gesamtnachfrage: das Optimum, die Routenzahl und der Aufschlag gegen den Postboten ohne Kapazität (der Rural-Postman-Weg über alle Pflichtkanten). "
           "Gezeigt werden nur Kapazitäten, bei denen sich Optimum oder Routenzahl ändern, und die der Instanz.")
scan = _scan(settings)
rows = ["| Kapazität | Optimum | Routen | Aufschlag gegen den Postboten |", "|---|---|---|---|"]
for r in scan:
    mark = "**" if r["Q"] == inst.Q else ""
    rows.append(f"| {mark}{r['Q']}{mark} | {mark}{de(r['opt'])}{mark} | {r['routes']} | {pct(r['price'])} |")
st.markdown("\n".join(rows))
kind, text = verdict_capacity(a, scan)
getattr(st, kind)(text)

st.markdown("---")

# --- Experiment 4 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Verfahren im Vergleich")
st.caption("Auf der Instanz der Seitenleiste: Rural-Postman-Weg + Split, nächster Nachbar + Split, Path-Scanning (vereinfacht), eine zufällige orientierte Folge, das beste von 200 orientierten Folgen und das beste von 200 Kantenfolgen "
           "mit Blockpreis. Darunter vorberechnete Bänder über 16 Instanzen mit 10 und 12 Pflichtkanten.")
order_m = sorted(methods.results, key=lambda k: methods.results[k][0])
rows = ["| Verfahren | Gesamtlänge | Lücke zum Optimum | Routen |", "|---|---|---|---|"]
for k in order_m:
    cost, rts = methods.results[k]
    rows.append(f"| {C.METHODS[k][0]} | {de(cost)} | {signed_pct(methods.gap(k))} | {len(rts)} |")
st.markdown("\n".join(rows))
pick = st.selectbox("Plan auf der Karte", order_m, key="method_pick", format_func=lambda k: C.METHODS[k][0])
st.plotly_chart(build_map(inst, methods.results[pick][1], legend=False), width="stretch", key="map_method")
kind, text = verdict_methods(a, methods)
getattr(st, kind)(text)
band_m = int(st.radio("Pflichtkanten (Bänder)", list(C.BAND_SIZES), horizontal=True, key="band_m"))
bs = carp_stats(band_m)
if bs:
    st.plotly_chart(build_band_bars(bs, band_m), width="stretch", key="band_chart")
    rows = ["| Verfahren | Lücke: Mittel | Median | Maximum | Optimum in |", "|---|---|---|---|---|"]
    for k in sorted(C.HEURISTICS, key=lambda k: bs[k]["mean"]):
        rows.append(f"| {C.METHODS[k][0]} | {pct(bs[k]['mean'])} | {pct(bs[k]['median'])} | {pct(bs[k]['max'])} | {bs[k]['optimal']} von {bs['count']} |")
    st.markdown("\n".join(rows))
    st.caption(f"{instances_word(bs['count'])} mit {band_m} Pflichtkanten, 9 Knoten, Zielroutenzahl 3, Zufallsverfahren mit festem Seed. Preis der Kapazität (Optimum gegen Rural-Postman-Weg): Mittel {pct(bs['price']['mean'])}, "
               f"Median {pct(bs['price']['median'])}, Maximum {pct(bs['price']['max'])}.")
kind, text = verdict_bands(band_m)
getattr(st, kind)(text)

st.markdown("---")

# --- Experiment 5 --------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Dominanz: das Minimum über alle Folgen ist das Optimum")
st.caption(f"Zu jeder zulässigen Lösung gibt es eine orientierte Folge, deren Split sie wiederfindet: man hängt die Routen aneinander. Die Seite zählt bei höchstens {C.ENUM_M} Pflichtkanten alle Folgen auf und vergleicht das Minimum mit dem exakten Optimum.")
if inst.m <= C.ENUM_M:
    enum5 = _enum(settings)
    kind, text = verdict_dominance(inst, enum5)
    getattr(st, kind)(text)
else:
    st.info(f"Die Aufzählung rechnet die Seite bis {C.ENUM_M} Pflichtkanten (bei {inst.m} sind es zu viele Folgen). Vorberechnet:")
dom = dominance_stats()
if dom["count"]:
    st.markdown(f"Bei 5 Pflichtkanten ({instances_word(dom['count'])}): das Minimum über alle {dom['n_oriented']} orientierten Folgen ist das Optimum in **{dom['oriented']} von {dom['count']}** Instanzen, "
                f"über alle {dom['n_sets']} Kantenfolgen mit Blockpreis in **{dom['sets']} von {dom['count']}**.")

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Kleine eigene Instanzen** | Bis 12 Pflichtkanten und 9 Knoten; die CARP-Benchmarks (Eglese, Belenguer-Benavent, Golden u. a.) haben Hunderte Kanten | Metaheuristiken, untere Schranken |
| **Blockpreis nur klein exakt** | Er rechnet die beste Route der Kantenmenge exakt (2 hoch Mengengröße Zustände); bei großen Blöcken braucht er eine Heuristik, und die Dominanz gilt dann nicht mehr für den Preis | Heuristik je Block |
| **Ungerichtete Kanten** | Gerichtete Bögen, Wendekosten und gemischte Graphen ändern die Leerfahrten und die Zahl der Richtungswahlen | gemischte Netzwerke |
| **Path-Scanning vereinfacht** | Eine Regel statt der fünf des Originals | Golden, DeArmon, Baker (1983) |
| **Ein Lauf je Instanz** | Die Zufallsverfahren haben Streuung; die Bänder nehmen 16 Instanzen je Größe | mehr Läufe |
| **Keine Zeitfenster, keine Flottengrenze** | Die Zahl der Routen ist frei | Stücke 3, 8, 9 |
"""
)

with st.expander("⚠️ Annahmen, Grenzen und bekannte Probleme"):
    st.markdown(C.ASSUMPTIONS_MARKDOWN)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Lesehilfe.** Ein Graph mit Knoten $V$, Depotknoten $0$, Pflichtkanten $e = \{a_e, b_e\}$ mit Kosten $c_e$ und Nachfrage $q_e$, Kapazität $Q$, kürzeste Wege $d(u, v)$. Ein Bogen ist ein Paar $(e, o)$, $o \in \{+, -\}$: die Kante $e$ von $a_e$ nach $b_e$ ($+$)
oder von $b_e$ nach $a_e$ ($-$).

**Route.** Eine Folge von Bögen $\alpha_1, \dots, \alpha_k$ kostet $d(0, s(\alpha_1)) + \sum_i c_{e(\alpha_i)} + \sum_{i<k} d(t(\alpha_i), s(\alpha_{i+1})) + d(t(\alpha_k), 0)$ mit $s$ dem Start- und $t$ dem Endknoten des Bogens; zulässig, wenn $\sum_i q_{e(\alpha_i)} \le Q$.

**Split.** Für eine Folge $\sigma$ orientierter Kanten ist $\operatorname{Split}(\sigma)$ die Länge des kürzesten Wegs im Hilfsgraphen mit den Bögen $(i, j)$, falls die Nachfrage von $\sigma_{i+1..j}$ höchstens $Q$ ist, und den Kosten der Route $\sigma_{i+1}, \dots, \sigma_j$.

**Blockpreis.** $w(S)$ ist die kürzeste Route, die genau die Kanten in $S$ bedient (beste Reihenfolge und Richtungen); der Split einer Kantenfolge $\pi$ nimmt $w(\{\pi_{i+1}, \dots, \pi_j\})$ als Kosten des Blocks.

**Exakt.** $\mathrm{dp}(S, \alpha)$ sei die kürzeste Länge ab dem Depot, die genau $S$ bedient und mit dem Bogen $\alpha$ endet; $w(S) = \min_\alpha \mathrm{dp}(S, \alpha) + d(t(\alpha), 0)$. Das Optimum mit Kapazität ist die Partition von $E$ mit kleinster Summe $\sum w(S_j)$ bei Nachfrage $\le Q$.

**Dominanz.** Zu jeder zulässigen Lösung (Routen $R_1, \dots, R_k$) gehört die Folge $R_1 R_2 \cdots R_k$; ihr Split ist nicht länger. Das Minimum von Split über alle orientierten Folgen ist das Optimum; ebenso das Minimum über alle Kantenfolgen mit Blockpreis.

**Literatur.** Capacitated Arc Routing: Golden und Wong (1981); Tabu-Suche für CARP: Hertz, Laporte, Mittaz (2000); Route-first, cluster-second: Beasley (1983), Prins (2004); Path-Scanning: Golden, DeArmon, Baker (1983).
Alle wurden nur als Titel oder Abstract gesehen; die Demo übernimmt keine Zahl daraus.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)
