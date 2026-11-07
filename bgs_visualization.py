"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import math

import plotly.graph_objects as go

import bgs_constants as C
import bgs_solver as S


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=380):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.2), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def build_map(inst, routes=None, legend=True):
    """Karte des Graphen: alle Kanten hellgrau, Pflichtkanten mit Nummer (grau, solange keine Routen gegeben sind), Depot als Quadrat. Je Route eine Farbe: Dienst als dicke Linie mit Pfeil in Dienstrichtung,
    Leerfahrten auf kürzesten Wegen gestrichelt. Gleicher Maßstab in x und y; der Rand kommt von zwei unsichtbaren Eckmarken."""
    xs = [p[0] for p in inst.pts]
    ys = [p[1] for p in inst.pts]
    pad = 0.1 * max(max(xs) - min(xs), max(ys) - min(ys), 1.0)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[min(xs) - pad, max(xs) + pad], y=[min(ys) - pad, max(ys) + pad], mode="markers", marker=dict(opacity=0), hoverinfo="skip", showlegend=False))
    req = {tuple(sorted(e)) for e in inst.req}
    for a, b in inst.edges:
        if (a, b) in req:
            continue
        fig.add_trace(go.Scatter(x=[inst.pts[a][0], inst.pts[b][0]], y=[inst.pts[a][1], inst.pts[b][1]], mode="lines", line=dict(color="rgba(150,150,150,0.35)", width=1.5), hoverinfo="skip", showlegend=False))
    if routes:
        for r, route in enumerate(routes):
            color = C.ROUTE_COLORS[r % len(C.ROUTE_COLORS)]
            load = sum(inst.q[e] for e, _ in route)
            first = True
            for kind, nodes in S.route_segments(inst, route):
                px, py = [inst.pts[v][0] for v in nodes], [inst.pts[v][1] for v in nodes]
                if kind == "dienst":
                    fig.add_trace(go.Scatter(x=px, y=py, mode="lines", line=dict(color=color, width=5), hoverinfo="skip", showlegend=first,
                                             name=f"Route {r + 1} (Last {load} von {inst.Q}, Länge {S.block_cost(inst, route):.1f})"))
                    first = False
                    mx, my = (px[0] + px[1]) / 2, (py[0] + py[1]) / 2
                    ang = math.degrees(math.atan2(py[1] - py[0], px[1] - px[0]))
                    fig.add_trace(go.Scatter(x=[mx], y=[my], mode="markers", marker=dict(symbol="triangle-right", size=11, color=color, angle=-ang), hoverinfo="skip", showlegend=False))
                else:
                    fig.add_trace(go.Scatter(x=px, y=py, mode="lines", line=dict(color=color, width=2, dash="dot"), hoverinfo="skip", showlegend=False))
    else:
        for a, b in inst.req:
            fig.add_trace(go.Scatter(x=[inst.pts[a][0], inst.pts[b][0]], y=[inst.pts[a][1], inst.pts[b][1]], mode="lines", line=dict(color="#555", width=4), hoverinfo="skip", showlegend=False))
    for k, (a, b) in enumerate(inst.req):
        mx, my = (inst.pts[a][0] + inst.pts[b][0]) / 2, (inst.pts[a][1] + inst.pts[b][1]) / 2
        fig.add_trace(go.Scatter(x=[mx], y=[my], mode="text", text=[f"<b>{k + 1}</b> (q {inst.q[k]})"], textposition="top center", textfont=dict(size=11), hoverinfo="skip", showlegend=False))
    nodes = list(range(1, inst.n_nodes))
    fig.add_trace(go.Scatter(x=[inst.pts[v][0] for v in nodes], y=[inst.pts[v][1] for v in nodes], mode="markers", marker=dict(size=8, color="#888", line=dict(color="#555", width=1)), hoverinfo="skip", name="Knoten", showlegend=False))
    fig.add_trace(go.Scatter(x=[inst.pts[0][0]], y=[inst.pts[0][1]], mode="markers", marker=dict(symbol="square", size=15, color="#222"), name="Depot", hoverinfo="skip"))
    fig.update_yaxes(scaleanchor="x", scaleratio=1, showgrid=False, zeroline=False, showticklabels=False)
    fig.update_xaxes(showgrid=False, zeroline=False, showticklabels=False)
    fig = _base(fig, 480 if legend else 380)
    if not legend:
        fig.update_layout(showlegend=False)
    return fig


def build_histogram(costs, opt, title="Kosten des Splits"):
    """Verteilung der Splitkosten aller Richtungswahlen; senkrechte Linie: das Optimum."""
    fig = go.Figure()
    fig.add_trace(go.Histogram(x=[c for c in costs if c < float("inf")], marker=dict(color="#2F6B65"), nbinsx=24, hovertemplate="%{x}: %{y} Richtungswahlen<extra></extra>"))
    fig.add_vline(x=opt, line=dict(color=C.COLOR_REQ_OFF, width=2), line_color="#c0504d", line_dash="dot", annotation_text=f"Optimum {opt:.1f}", annotation_position="top")
    fig.update_xaxes(title_text=title)
    fig.update_yaxes(title_text="Zahl der Richtungswahlen")
    fig = _base(fig, 300)
    fig.update_layout(showlegend=False, margin=dict(l=10, r=10, t=30, b=40))
    return fig


def build_band_bars(stats, m):
    """Mittlere Lücke zum Optimum je Verfahren (Balken), dazu das Maximum als Strich; Reihenfolge nach dem Mittel."""
    keys = sorted(C.HEURISTICS, key=lambda k: stats[k]["mean"])
    fig = go.Figure()
    fig.add_trace(go.Bar(x=[C.METHODS[k][0] for k in keys], y=[stats[k]["mean"] for k in keys], marker=dict(color=[C.METHODS[k][1] for k in keys]),
                         hovertemplate="%{x}: %{y:.1f} % im Mittel<extra></extra>", name="Mittel"))
    fig.add_trace(go.Scatter(x=[C.METHODS[k][0] for k in keys], y=[stats[k]["max"] for k in keys], mode="markers", marker=dict(symbol="line-ew", size=22, color="#333", line=dict(width=2, color="#333")),
                             hovertemplate="%{x}: Maximum %{y:.1f} %<extra></extra>", name="Maximum"))
    fig.update_yaxes(title_text=f"Lücke zum Optimum in % ({m} Pflichtkanten)")
    fig.update_xaxes(tickangle=-25)
    fig = _base(fig, 420)
    fig.update_layout(margin=dict(l=10, r=10, t=10, b=120), legend=dict(orientation="h", y=-0.6))
    return fig
