"""
Unit tests for scrapers._match_name — the exact function behind two real
bugs found in production this session:
  1. Jamie Gittens going unmatched because API-Football lists him under
     his full legal surname ("J. Bynoe-Gittens"), fixed via NAME_OVERRIDES.
  2. The last-name fallback needing to stay conservative (return None on
     ambiguity) rather than guess, since the roster has multiple players
     sharing a surname (the two Fofanas).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scrapers import _match_name, _normalize  # noqa: E402

ROSTER = [
    "Jamie Gittens",
    "Enzo Fernandez",
    "Wesley Fofana",
    "David Datro Fofana",
]
PLAYER_MAP = {_normalize(n): {"name": n} for n in ROSTER}


def test_override_resolves_full_legal_surname():
    # Regression test for the Jamie Gittens bug.
    matched = _match_name("J. Bynoe-Gittens", PLAYER_MAP)
    assert matched is not None
    assert matched["name"] == "Jamie Gittens"


def test_exact_normalized_name_matches():
    matched = _match_name("Enzo Fernandez", PLAYER_MAP)
    assert matched["name"] == "Enzo Fernandez"


def test_exact_match_ignores_accents_and_case():
    matched = _match_name("enzo fernández", PLAYER_MAP)
    assert matched["name"] == "Enzo Fernandez"


def test_ambiguous_last_name_returns_none_instead_of_guessing():
    # Two "Fofana"s in the roster — the fallback must not pick one blindly.
    assert _match_name("Someone Fofana", PLAYER_MAP) is None


def test_unknown_player_returns_none():
    assert _match_name("Random Player", PLAYER_MAP) is None
