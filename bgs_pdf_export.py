"""PDF-Export der aktuellen Ergebnisse (fpdf2). Kernschriften sind latin-1: Umlaute gehen, Sonderzeichen werden ersetzt."""

from __future__ import annotations

from fpdf import FPDF

import bgs_constants as C
from bgs_evaluation import Analysis, Methods, Settings, de, pct, routes_word, sequence_text
from bgs_solver import block_cost

_REPLACE = {"→": "->", "–": "-", "—": "-", "−": "-", "≤": "<=", "≥": ">=", "·": "*", "×": "x", "„": '"', "“": '"', "²": "2", "‖": "|", "←": "<-"}


def _s(text) -> str:
    out = str(text).replace("**", "").replace("`", "")
    for old, new in _REPLACE.items():
        out = out.replace(old, new)
    return out.encode("latin-1", "replace").decode("latin-1")


def build_pdf(s: Settings, a: Analysis, methods: Methods) -> bytes:
    inst = a.inst
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 15)
    pdf.cell(0, 9, _s("Bogenrouting mit Kapazität"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    where = "Handinstanz (6 Knoten, 5 Pflichtkanten)" if s.family == C.HAND_FAMILY else f"Zufälliger Graph, {inst.n_nodes} Knoten, {inst.m} Pflichtkanten, Zielroutenzahl {s.routes}, Seed {s.seed}"
    pdf.multi_cell(0, 5, _s(f"{where}. Kapazität {inst.Q}, Gesamtnachfrage {sum(inst.q)}. Alles simuliert. Optimum {de(a.opt)} mit {routes_word(len(a.routes))}; Rural-Postman-Weg ohne Kapazität {de(a.w_all)} (Preis der Kapazität {pct(a.capacity_price)})."),
                   new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, _s("Optimale Routen"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    for i, r in enumerate(a.routes, start=1):
        pdf.cell(0, 5, _s(f"Route {i}: {sequence_text(r)} (Last {sum(inst.q[e] for e, _ in r)} von {inst.Q}, Länge {de(block_cost(inst, r))})"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    widths = (90, 30, 40, 20)
    pdf.set_font("Helvetica", "B", 9)
    for w, h in zip(widths, ("Verfahren", "Gesamtlänge", "Lücke zum Optimum", "Routen")):
        pdf.cell(w, 6, _s(h), border=1)
    pdf.ln()
    pdf.set_font("Helvetica", "", 9)
    for k in sorted(methods.results, key=lambda k: methods.results[k][0]):
        cost, routes = methods.results[k]
        for w, v in zip(widths, (C.METHODS[k][0], de(cost), pct(methods.gap(k)), str(len(routes)))):
            pdf.cell(w, 5.5, _s(v), border=1)
        pdf.ln()
    pdf.ln(2)
    pdf.set_font("Helvetica", "I", 8)
    pdf.multi_cell(0, 4, _s("Ein Lauf je Verfahren; Zufallsverfahren mit festem Seed. Path-Scanning vereinfacht (eine Regel). Quelle: bogen-split-demo, Sebastian Hanisch."), new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())
