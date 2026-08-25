"""Discovery AI — heuristic rules only."""
from __future__ import annotations
from typing import List, Tuple
import random

from .base import AI, ActionContext
from ..cards import Card
from ..engine import valid_melds, is_valid_meld
from ..game import Move
from ..config import RamiConfig


class DiscoveryAI(AI):
    name = "discovery"

    def __init__(self, seed: int = 0):
        self.rng = random.Random(seed)

    def choose_move(self, ctx: ActionContext) -> Move:
        moves = ctx.legal_moves
        cfg = ctx.state.cfg

        # ---- Step 1: prefer drawing from discard if it completes a meld ----
        top = ctx.top_discard
        discard_complete_moves: List[Move] = []
        if top is not None and "discard" in {m.draw_source for m in moves}:
            for m in moves:
                if m.draw_source != "discard":
                    continue
                for meld in m.laydowns:
                    # Is the drawn card part of this meld?
                    if any((c.suit, c.rank) == (top.suit, top.rank) for c in meld):
                        discard_complete_moves.append(m)
                        break

        if discard_complete_moves:
            # Prefer the move that lays the most cards
            best = max(discard_complete_moves, key=lambda m: sum(len(x) for x in m.laydowns))
            return best

        # ---- Step 2: draw from stock ----
        stock_moves = [m for m in moves if m.draw_source == "stock"]
        if not stock_moves:
            # forced to draw from discard
            stock_moves = [m for m in moves if m.draw_source == "discard"]
        if not stock_moves:
            return moves[0]

        # ---- Step 3: lay any melds available (prefer non-joker melds) ----
        def move_score(m: Move) -> Tuple[int, int, int]:
            lay_points = sum(len(x) * 10 + (0 if any(c.is_joker for c in x) else 5)
                             for x in m.laydowns)
            # discard: lower value is better (don't throw face cards)
            discard_value = cfg.card_value(m.discard.rank) if not m.discard.is_joker else cfg.joker_penalty
            return (lay_points, -discard_value, -len(m.laydowns))

        # If we haven't laid first yet, prefer moves that lay enough to clear threshold
        if not ctx.state.current_player.has_laid_first and cfg.first_meld_threshold > 0:
            threshold_moves = [m for m in stock_moves
                               if sum(len(x) for x in m.laydowns) >= 3 and
                               _lay_points(m, cfg) >= cfg.first_meld_threshold]
            if threshold_moves:
                stock_moves = threshold_moves

        best = max(stock_moves, key=move_score)
        return best


def _lay_points(m: Move, cfg: RamiConfig) -> int:
    return sum(cfg.card_value(c.rank) for meld in m.laydowns for c in meld if not c.is_joker)
