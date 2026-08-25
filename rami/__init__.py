"""Rami-AI: vision-driven Rami player. MIT licensed."""
from .config import RamiConfig
from .cards import Card, Hand, build_deck
from .engine import (is_valid_meld, valid_melds, valid_laydowns,
                     meld_points, deadwood_score, best_meld_partition)
from .game import GameState, new_game, legal_moves, apply_move, Move, score_terminal

__version__ = "0.1.0"
__all__ = [
    "RamiConfig", "Card", "Hand", "build_deck",
    "is_valid_meld", "valid_melds", "valid_laydowns",
    "meld_points", "deadwood_score", "best_meld_partition",
    "GameState", "new_game", "legal_moves", "apply_move", "Move", "score_terminal",
]
