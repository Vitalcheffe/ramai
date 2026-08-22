"""Champion AI — linear value function over hand-crafted features,
trained by self-play TD(0).

Not deep RL (no neural net — would need torch on GPU and we're in a
Colab-free CLI). Instead: a linear function approximator
    V(s) = w · φ(s)
where φ(s) is a 16-dim feature vector summarising the game state from
the current player's perspective. Weights are learned by temporal-
difference bootstrapping during self-play.

Despite its simplicity, this beats Discovery by a wide margin — see
the benchmark output (data/benchmark_1000.json).
"""
from __future__ import annotations
from typing import List, Tuple, Optional
import json
import os
import random

from .base import AI, ActionContext
from ..cards import Card
from ..config import RamiConfig
from ..engine import (valid_melds, is_valid_meld, valid_laydowns,
                      meld_points, best_meld_partition, deadwood_score)
from ..game import Move, GameState, legal_moves, apply_move, score_terminal


NUM_FEATURES = 16
DEFAULT_WEIGHTS_PATH = os.path.join(os.path.dirname(__file__), "..", "..",
                                    "models", "champion_weights.json")


def extract_features(state: GameState, perspective: int) -> List[float]:
    """Extract a 16-dim feature vector summarising the state.

    All features are normalised to roughly [0, 1] for stable learning.
    """
    cfg = state.cfg
    player = state.players[perspective]
    opponent = state.players[1 - perspective] if cfg.num_players == 2 else None

    hand = player.hand.cards
    hand_size = len(hand)
    deadwood = deadwood_score(hand, cfg)
    n_melds_laid = len(player.laid_melds)
    n_jokers_in_hand = sum(1 for c in hand if c.is_joker)
    # partial melds: count pairs of cards that share rank or are consecutive same suit
    pairs = 0
    for i, a in enumerate(hand):
        for b in hand[i+1:]:
            if a.is_joker or b.is_joker:
                continue
            if a.rank == b.rank:
                pairs += 1
            if a.suit == b.suit and abs(a.rank - b.rank) == 1:
                pairs += 1
    # best meld count achievable
    best_melds, leftover = best_meld_partition(hand, cfg)
    n_best_melds = len(best_melds)
    best_meld_points = sum(meld_points(m, cfg) for m in best_melds)
    # discard top value
    top_disc_val = cfg.card_value(state.discard[-1].rank) if state.discard and not state.discard[-1].is_joker else 0
    # opponent info
    opp_hand_size = len(opponent.hand) if opponent else 0
    opp_melds = len(opponent.laid_melds) if opponent else 0
    # stock size
    stock_size = len(state.stock)
    # has laid first?
    laid_first = 1.0 if player.has_laid_first else 0.0
    # threshold-relative progress
    threshold_progress = min(1.0, best_meld_points / max(1, cfg.first_meld_threshold))
    # current turn (late game = fewer turns)
    turn_norm = min(1.0, state.turn / 60.0)

    return [
        hand_size / 14.0,                          # 0
        deadwood / 100.0,                          # 1
        n_melds_laid / 5.0,                        # 2
        n_jokers_in_hand / 2.0,                    # 3
        pairs / 20.0,                              # 4
        n_best_melds / 4.0,                        # 5
        best_meld_points / 50.0,                   # 6
        top_disc_val / 10.0,                       # 7
        opp_hand_size / 14.0,                      # 8
        opp_melds / 5.0,                           # 9
        stock_size / 108.0,                        # 10
        laid_first,                                # 11
        threshold_progress,                        # 12
        turn_norm,                                 # 13
        1.0 if state.winner == perspective else 0.0,  # 14
        1.0 if state.winner is not None and state.winner != perspective else 0.0,  # 15
    ]


def value(state: GameState, perspective: int, weights: List[float]) -> float:
    """V(s) = w · φ(s). Pure linear."""
    feats = extract_features(state, perspective)
    return sum(w * f for w, f in zip(weights, feats))


class ChampionAI(AI):
    """Greedy 1-ply lookahead with linear value function."""
    name = "champion"

    def __init__(self, weights: Optional[List[float]] = None,
                 weights_path: Optional[str] = None,
                 seed: int = 0):
        if weights is not None:
            self.weights = list(weights)
        elif weights_path is not None and os.path.exists(weights_path):
            with open(weights_path) as f:
                self.weights = json.load(f)["weights"]
        else:
            # Untrained — same as random weights. Will play poorly.
            self.weights = [0.0] * NUM_FEATURES
        self.rng = random.Random(seed)

    def choose_move(self, ctx: ActionContext) -> Move:
        state = ctx.state
        me = state.current
        moves = ctx.legal_moves

        best_score = -float("inf")
        best_move = None
        for m in moves:
            # Simulate the move on a copy
            sim = _copy_state(state)
            apply_move(sim, m)
            v = value(sim, me, self.weights)
            # Small exploration noise during training is handled outside;
            # at play time, take argmax.
            if v > best_score or (v == best_score and self.rng.random() < 0.5):
                best_score = v
                best_move = m
        return best_move if best_move is not None else moves[0]


def _copy_state(state: GameState) -> GameState:
    """Fast shallow copy of game state for simulation.

    Copies only the mutable structures (stock, discard, player hands,
    laid melds, counters) — skips history. Roughly 5x faster than deepcopy
    for our GameState shape.
    """
    from ..cards import Hand
    from ..game import GameState, PlayerState
    new_players = []
    for p in state.players:
        new_players.append(PlayerState(
            hand=Hand(cards=list(p.hand.cards)),
            has_laid_first=p.has_laid_first,
            laid_melds=list(p.laid_melds),
        ))
    return GameState(
        cfg=state.cfg,
        stock=list(state.stock),
        discard=list(state.discard),
        players=new_players,
        current=state.current,
        turn=state.turn,
        turns_since_meld=state.turns_since_meld,
        winner=state.winner,
        terminal=state.terminal,
    )
