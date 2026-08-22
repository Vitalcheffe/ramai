"""AI interface shared by all 3 levels."""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional

from ..cards import Card
from ..game import GameState, Move, legal_moves
from ..config import RamiConfig


@dataclass
class ActionContext:
    """Everything the AI is allowed to see at decision time."""
    state: GameState
    legal_moves: List[Move]

    # What the AI can observe (no cheating):
    #   - its own hand
    #   - the discard pile (all of it, face up)
    #   - how many cards opponents hold (count only, not faces)
    #   - melds opponents have laid face up
    #   - the size of the stock
    @property
    def my_hand(self) -> List[Card]:
        return self.state.current_player.hand.cards

    @property
    def discard_pile(self) -> List[Card]:
        return list(self.state.discard)

    @property
    def opponent_hand_sizes(self) -> List[int]:
        return [len(p.hand) for i, p in enumerate(self.state.players)
                if i != self.state.current]

    @property
    def stock_size(self) -> int:
        return len(self.state.stock)

    @property
    def top_discard(self) -> Optional[Card]:
        return self.state.top_discard


class AI(ABC):
    """Base class for all Rami AIs. Subclasses implement choose_move."""

    name: str = "base"

    @abstractmethod
    def choose_move(self, ctx: ActionContext) -> Move:
        ...

    def decide(self, state: GameState) -> Move:
        """Public entry point: takes a game state, returns a legal Move."""
        moves = legal_moves(state)
        if not moves:
            raise RuntimeError("no legal moves")
        ctx = ActionContext(state=state, legal_moves=moves)
        move = self.choose_move(ctx)
        assert move in moves, f"AI returned illegal move: {move}"
        return move
