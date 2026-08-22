"""Test the Discovery AI: never blunders, plays valid moves."""
import pytest
from rami.config import RamiConfig
from rami.game import new_game, legal_moves, apply_move
from rami.ai.discovery import DiscoveryAI


def test_discovery_returns_legal_move():
    cfg = RamiConfig()
    g = new_game(cfg, seed=1)
    ai = DiscoveryAI(seed=0)
    m = ai.decide(g)
    assert m in legal_moves(g)


def test_discovery_takes_discard_when_completes_meld():
    """Construct a state where the discard completes a meld and verify
    Discovery prefers to take it."""
    cfg = RamiConfig(first_meld_threshold=0)
    g = new_game(cfg, seed=1)
    # Force a hand that contains two kings of different suits
    p = g.players[0]
    p.hand.cards = [
        Card(0, 13, 0), Card(1, 13, 0),  # 2 kings, need a 3rd
        Card(2, 5, 0), Card(3, 7, 0),
        Card(0, 9, 0), Card(1, 4, 0),
        Card(2, 8, 0), Card(3, 2, 0),
        Card(0, 11, 0), Card(1, 3, 0),
        Card(2, 6, 0), Card(3, 12, 0),
        Card(0, 4, 0), Card(1, 9, 0),
    ]
    # Top discard is a 3rd king
    g.discard = [Card(2, 13, 0)]
    ai = DiscoveryAI(seed=0)
    m = ai.decide(g)
    assert m.draw_source == "discard"
    # Should lay the king meld
    assert any(any(c.rank == 13 for c in meld) for meld in m.laydowns)


def test_discovery_full_game_terminates():
    cfg = RamiConfig()
    g = new_game(cfg, seed=99)
    ai = DiscoveryAI(seed=0)
    n = 0
    while not g.terminal and n < 500:
        apply_move(g, ai.decide(g))
        n += 1
    assert g.terminal


def test_discovery_never_plays_illegal():
    """Run 5 games, verify every move is in legal_moves at the time."""
    cfg = RamiConfig()
    ai = DiscoveryAI(seed=0)
    for seed in range(5):
        g = new_game(cfg, seed=seed)
        n = 0
        while not g.terminal and n < 300:
            moves = legal_moves(g)
            assert moves  # always at least one
            m = ai.decide(g)
            assert m in moves
            apply_move(g, m)
            n += 1


# Import Card here so test file is self-contained
from rami.cards import Card
