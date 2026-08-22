"""Test the Champion AI: feature extraction + greedy value play."""
import pytest
import os
import json
from rami.config import RamiConfig
from rami.game import new_game, legal_moves, apply_move
from rami.ai.champion import ChampionAI, extract_features, NUM_FEATURES, value
from rami.cards import Card


def test_extract_features_shape():
    cfg = RamiConfig()
    g = new_game(cfg, seed=1)
    feats = extract_features(g, perspective=0)
    assert len(feats) == NUM_FEATURES


def test_extract_features_normalised_range():
    """All features should be roughly in [0, 1] or close to it."""
    cfg = RamiConfig()
    g = new_game(cfg, seed=1)
    feats = extract_features(g, perspective=0)
    for f in feats:
        assert -1.0 <= f <= 1.5, f"feature out of expected range: {f}"


def test_value_with_zero_weights_is_zero():
    cfg = RamiConfig()
    g = new_game(cfg, seed=1)
    v = value(g, perspective=0, weights=[0.0] * NUM_FEATURES)
    assert v == 0.0


def test_value_changes_with_weights():
    cfg = RamiConfig()
    g = new_game(cfg, seed=1)
    v0 = value(g, 0, [0.0] * NUM_FEATURES)
    v1 = value(g, 0, [1.0] * NUM_FEATURES)
    assert v0 != v1


def test_champion_untrained_returns_legal_move():
    """Untrained champion = zero weights, still picks something legal."""
    cfg = RamiConfig()
    g = new_game(cfg, seed=1)
    ai = ChampionAI(weights=[0.0] * NUM_FEATURES, seed=0)
    m = ai.decide(g)
    assert m in legal_moves(g)


def test_champion_with_loaded_weights():
    """Champion should be loadable from a weights file."""
    weights_path = "/tmp/test_champion_weights.json"
    weights = [0.1 * i for i in range(NUM_FEATURES)]
    with open(weights_path, "w") as f:
        json.dump({"weights": weights}, f)
    ai = ChampionAI(weights_path=weights_path, seed=0)
    assert len(ai.weights) == NUM_FEATURES
    cfg = RamiConfig()
    g = new_game(cfg, seed=1)
    m = ai.decide(g)
    assert m in legal_moves(g)


def test_champion_full_game_terminates():
    cfg = RamiConfig()
    g = new_game(cfg, seed=7)
    # Slight positive bias: like melds, prefer hand_size small, prefer low deadwood
    weights = [-1.0] + [0.0] * 5 + [1.0] * 10
    assert len(weights) == NUM_FEATURES
    ai = ChampionAI(weights=weights, seed=0)
    n = 0
    while not g.terminal and n < 500:
        apply_move(g, ai.decide(g))
        n += 1
    assert g.terminal


def test_champion_never_plays_illegal():
    cfg = RamiConfig()
    weights = [-1.0, -0.5] + [1.0] * (NUM_FEATURES - 2)
    ai = ChampionAI(weights=weights, seed=0)
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
