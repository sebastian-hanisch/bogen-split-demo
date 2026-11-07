"""Gemeinsame Fixtures: die Handinstanz (Raster mit ganzzahligen Kosten), an der jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bgs_model import hand_instance  # noqa: E402


@pytest.fixture
def hand():
    """Handinstanz: Knoten 0 (0,0) Depot, 1 (4,0), 2 (4,3), 3 (0,3), 4 (8,0), 5 (8,3); Kanten 0-1 (4), 1-2 (3), 2-3 (4), 0-3 (3), 1-4 (4), 4-5 (3), 2-5 (4), 0-2 (5).
    Pflichtkanten (Nummern ab 1): 1 = {1,2} (3, q 2), 2 = {2,3} (4, q 3), 3 = {4,5} (3, q 2), 4 = {1,4} (4, q 2), 5 = {2,5} (4, q 3); Kapazität 6.

    Von Hand: Route (4+ 3+ 1-) = 4 + 4 + 3 + 4 + 3 + 4 = 22, Route (5+ 2+) = 5 + 4 + 4 + 4 + 3 = 20; Optimum 42. Rural-Postman-Weg (2- 1- 4+ 3+ 5-): 3 + 4 + 3 + 4 + 3 + 4 + 5 = 26."""
    return hand_instance()
