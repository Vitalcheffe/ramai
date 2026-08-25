"""Test the Strategy AI: card counting + probability-aware."""
import pytest
from rami.config import RamiConfig
from rami.game import new_game, legal_moves, apply_move
from rami.ai.strategy import StrategyAI
from rami.cards import Card


def test_strategy_returns_legal_move():
    cfg = RamiConfig()
    g = new_game(cfg, seed=1)
    ai = StrategyAI(seed=0)
    m = ai.decide(g)
    assert m in legal_moves(g)


def test_strategy_takes_discard_when_useful():
    """If the discard card fits the hand, Strategy should often take it."""
    cfg = RamiConfig(first_meld_threshold=0)
    g = new_game(cfg, seed=1)
    p = g.players[0]
    p.hand.cards = [
        Card(0, 13, 0), Card(1, 13, 0), Card(2, 5, 0), Card(3, 7, 0),
        Card(0, 9, 0), Card(1, 4, 0), Card(2, 8, 0), Card(3, 2, 0),
        Card(0, 11, 0), Card(1, 3, 0), Card(2, 6, 0), Card(3, 12, 0),
        Card(0, 4, 0), Card(1, 9, 0),
    ]
    g.discard = [Card(2, 13, 0)]   # 3rd king — completes meld
    ai = StrategyAI(seed=0)
    m = ai.decide(g)
    assert m.draw_source == "discard"


def test_strategy_avoids_throwing_joker():
    """Strategy should never choose to discard a joker if it has alternatives."""
    cfg = RamiConfig(can_discard_joker=True)  # allow it explicitly, see if AI avoids
    g = new_game(cfg, seed=42)
    p = g.players[0]
    p.hand.cards = [
        Card(0, 5, 0), Card(1, 9, 0), Card(2, 3, 0), Card(3, 11, 0),
        Card(0, 8, 0), Card(1, 2, 0), Card(2, 7, 0), Card(3, 12, 0),
        Card(0, 4, 0), Card(1, 6, 0), Card(2, 10, 0), Card(3, 1, 0),
        Card(-1, 0, 0),  # Joker
        Card(0, 9, 1),
    ]
    ai = StrategyAI(seed=0)
    m = ai.decide(g)
    assert not m.discard.is_joker


def test_strategy_full_game_terminates():
    cfg = RamiConfig()
    g = new_game(cfg, seed=7)
    ai = StrategyAI(seed=0)
    n = 0
    while not g.terminal and n < 500:
        apply_move(g, ai.decide(g))
        n += 1
    assert g.terminal


def test_strategy_counting_tracks_unseen_correctly():
    """Strategy should never 'know' about cards it can't see.
    Verify by checking it doesn't crash on edge cases."""
    cfg = RamiConfig()
    g = new_game(cfg, seed=7)
    ai = StrategyAI(seed=0)
    # play 20 turns
    for _ in range(20):
        if g.terminal:
            break
        apply_move(g, ai.decide(g))
    # Should still produce legal moves
    if not g.terminal:
        m = ai.decide(g)
        assert m in legal_moves(g)


def test_strategy_never_plays_illegal():
    cfg = RamiConfig()
    ai = StrategyAI(seed=0)
    for seed in range(5):
        g = new_game(cfg, seed=seed)
        n = 0
        while not g.terminal and n < 300:
            moves = legal_moves(g)
            assert moves
            m = ai.decide(g)
            assert m in moves
            apply_move(g, m)
            n += 1
