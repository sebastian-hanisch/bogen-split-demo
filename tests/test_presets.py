"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen; die Zahlen in den Hilfetexten stehen in test_claims.py."""

import bgs_constants as C
import bgs_evaluation as ev
import bgs_presets as P


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_control_bounds():
    for name, preset in C.PRESETS.items():
        for key, state_key in P.PRESET_KEYS.items():
            spec = P.SETTING_SPECS[state_key]
            assert spec.lo <= preset[key] <= spec.hi, (name, key)


def test_default_preset_equals_the_default_settings():
    first = next(iter(C.PRESETS.values()))
    assert ev.Settings(first["m"], first["family"], first["nodes"], first["routes"], first["seed"]) == ev.Settings()


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)


def test_every_preset_has_a_distinct_configuration():
    assert len({tuple(sorted(p.items())) for p in C.PRESETS.values()}) == len(C.PRESETS)


def test_constants_are_consistent():
    assert C.M_MIN <= C.DEFAULT_M <= C.M_MAX == C.EXACT_LIVE_M and C.ENUM_M <= C.ENUM_SHARE_M <= C.EXACT_LIVE_M and C.BAND_SIZES[-1] > C.EXACT_LIVE_M
    assert set(C.METHODS) == {"OPT", *C.HEURISTICS} and all(len(v) == 2 for v in C.METHODS.values())
    assert C.NODES_MIN <= C.DEFAULT_NODES <= C.NODES_MAX and C.ROUTES_MIN <= C.DEFAULT_ROUTES <= C.ROUTES_MAX and C.DEFAULT_FAMILY == C.HAND_FAMILY
    assert len(C.HAND_REQ) == len(C.HAND_Q_DEMAND) == C.DEFAULT_M
