"""Die fünf Experimente der App per AppTest: Folge von Hand, Richtung, Kapazität, Verfahren und Bänder, Dominanz; dazu das PDF."""

import os
from pathlib import Path

from streamlit.testing.v1 import AppTest

import bgs_constants as C
import bgs_evaluation as ev
from bgs_pdf_export import build_pdf

APP = str(Path(__file__).resolve().parent.parent / "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))
SETTING_KEYS = {"family": "family_select", "m": "m_slider", "nodes": "nodes_slider", "routes": "routes_slider", "seed": "seed_input"}
HAND = "Handinstanz: eine Folge von Hand"


def _app(preset=None) -> AppTest:
    at = AppTest.from_file(APP, default_timeout=TIMEOUT)
    if preset:
        at.session_state["permalink_loaded"] = True
        for key, state_key in SETTING_KEYS.items():
            at.session_state[state_key] = C.PRESETS[preset][key]
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _texts(at):
    return " ".join([x.value for x in at.success] + [x.value for x in at.info] + [x.value for x in at.warning] + [x.value for x in at.error])


def test_the_default_shows_the_hand_instance_and_the_optimal_sequence():
    at = _app()
    assert at.text_input(key="seq_text").value == "4+ 3+ 1- 5+ 2+"                                  # die optimalen Routen hintereinander
    text = _texts(at)
    assert "trifft das Optimum: 42,00 mit 2 Routen" in text and "Über alle 3840 orientierten Folgen von 5 Pflichtkanten" in text


def test_a_typed_sequence_is_evaluated_and_a_bad_one_is_reported():
    at = _app()
    at.text_input(key="seq_text").set_value("2- 5+ 3- 4- 1+").run()
    assert not at.exception and "liefert 44,00 mit 2 Routen" in _texts(at)
    at.text_input(key="seq_text").set_value("1 2 3").run()
    assert not at.exception and any("genau einmal" in e.value for e in at.error)
    at.text_input(key="seq_text").set_value("9+ 1 2 3 4").run()
    assert not at.exception and any("keine Kantennummer" in e.value for e in at.error)


def test_every_instance_control_runs_and_large_ones_skip_the_enumeration():
    at = _app()
    at.selectbox(key="family_select").set_value(1).run()
    assert not at.exception
    for m in (2, 6, 7, 10):
        at.slider(key="m_slider").set_value(m).run()
        assert not at.exception, m
        assert f"{m} Pflichtkanten" in " ".join(c.value for c in at.caption)
    at.slider(key="nodes_slider").set_value(6).run()
    at.slider(key="routes_slider").set_value(4).run()
    assert not at.exception
    at.slider(key="m_slider").set_value(8).run()
    assert any("Die Aufzählung aller Folgen rechnet die Seite bis" in i.value for i in at.info)


def test_method_pick_and_band_selection():
    at = _app()
    for k in C.METHODS:
        at.selectbox(key="method_pick").set_value(k).run()
        assert not at.exception, k
    for m in C.BAND_SIZES:
        at.radio(key="band_m").set_value(m).run()
        assert not at.exception and f"Bei {m} Pflichtkanten (16 Instanzen)" in _texts(at)


def test_every_preset_runs_and_shows_its_numbers():
    expected = {"Die Richtung zählt (6 Pflichtkanten)": "16 von 46080 orientierten Folgen", "Die Kapazität kostet (10 Pflichtkanten)": "Preis der Kapazität",
                "Blockpreis gegen Konstruktion (10 Pflichtkanten)": "Am besten ist Bestes von 200 Kantenfolgen + Blockpreis"}
    for name, snippet in expected.items():
        at = _app(name)
        assert snippet in _texts(at) + " ".join(m.label for m in at.metric), name


def test_pdf_download_button_exists_and_the_pdf_is_built_for_every_preset():
    assert len(_app().get("download_button")) == 1
    for preset in C.PRESETS.values():
        s = ev.Settings(preset["m"], preset["family"], preset["nodes"], preset["routes"], preset["seed"])
        a = ev.analyse(s)
        data = build_pdf(s, a, ev.run_methods(a, 20))
        assert data[:5] == b"%PDF-" and len(data) > 1500
