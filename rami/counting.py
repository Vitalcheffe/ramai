"""Card counting — track opponent hand by arithmetic."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional

from .cards import Card
from .config import RamiConfig


@dataclass
class CardCountingState:
    """Tracks the opponent's hand size and unseen-card set, updated each move."""
    cfg: RamiConfig
    # Initial hand size
    initial_hand_size: int = 14

    # Per-player accounting
    drawn_from_stock: Dict[int, int] = field(default_factory=dict)
    drawn_from_discard: Dict[int, int] = field(default_factory=dict)
    discards_by_player: Dict[int, List[Card]] = field(default_factory=dict)
    laid_melds_count: Dict[int, int] = field(default_factory=dict)

    # The set of all cards the AI has ever seen (visible at any point)
    visible_cards: Set[Tuple[int, int, int]] = field(default_factory=set)

    @classmethod
    def fresh(cls, cfg: RamiConfig, ai_player_idx: int, ai_hand: List[Card],
              initial_discard: Optional[List[Card]] = None) -> "CardCountingState":
        """Initialise at game start. AI knows its own hand + the initial
        discard pile (which is face up from the start)."""
        s = cls(cfg=cfg, initial_hand_size=cfg.hand_size)
        for p in range(cfg.num_players):
            s.drawn_from_stock[p] = 0
            s.drawn_from_discard[p] = 0
            s.discards_by_player[p] = []
            s.laid_melds_count[p] = 0
        # AI's own hand is visible
        for c in ai_hand:
            s.visible_cards.add((c.suit, c.rank, c.copy_id))
        # Initial discard pile (if any) is visible
        if initial_discard:
            for c in initial_discard:
                s.visible_cards.add((c.suit, c.rank, c.copy_id))
        return s

    def record_draw(self, player: int, source: str, card: Optional[Card],
                    ai_player_idx: int) -> None:
        """Record a draw event.

        For AI's own draws, the card is visible.
        For opponent's draws from stock, the card is NOT visible.
        For opponent's draws from discard, the card IS visible (it was face-up).
        """
        if source == "stock":
            self.drawn_from_stock[player] += 1
            if player == ai_player_idx and card is not None:
                self.visible_cards.add((card.suit, card.rank, card.copy_id))
        else:  # discard
            self.drawn_from_discard[player] += 1
            # Discard pile is always visible
            if card is not None:
                self.visible_cards.add((card.suit, card.rank, card.copy_id))

    def record_discard(self, player: int, card: Card) -> None:
        """Record a discard event. Discards are always visible."""
        self.discards_by_player[player].append(card)
        self.visible_cards.add((card.suit, card.rank, card.copy_id))

    def record_meld(self, player: int, meld: Tuple[Card, ...]) -> None:
        """Record a laid meld. Melds are always visible."""
        self.laid_melds_count[player] += len(meld)
        for c in meld:
            self.visible_cards.add((c.suit, c.rank, c.copy_id))

    def hand_count(self, player: int) -> int:
        """Compute the current hand size for a player by arithmetic.

        hand = initial_hand_size
             + drawn_from_stock
             + drawn_from_discard
             - discards
             - laid_meld_cards
        """
        return (self.initial_hand_size
                + self.drawn_from_stock.get(player, 0)
                + self.drawn_from_discard.get(player, 0)
                - len(self.discards_by_player.get(player, []))
                - self.laid_melds_count.get(player, 0))

    def is_opponent_empty(self, opponent_idx: int) -> bool:
        """Detect that the opponent has gone out (hand size = 0)."""
        return self.hand_count(opponent_idx) == 0

    def unseen_cards(self, cfg: RamiConfig) -> Set[Tuple[int, int, int]]:
        """Compute the set of unseen cards.

        Unseen = (full deck keys) - (visible cards).

        Unseen cards are either:
          - in the unrevealed stock, OR
          - in the opponent's hidden hand.
        """
        full = set()
        for copy_id in range(cfg.num_decks):
            for s in range(cfg.num_suits):
                for r in range(1, cfg.ranks_per_suit + 1):
                    full.add((s, r, copy_id))
            # Jokers: distinguished by index
            for j in range(cfg.num_jokers_per_deck):
                full.add((-1, 0, 1000 + copy_id * cfg.num_jokers_per_deck + j))
        return full - self.visible_cards

    def unseen_count(self, cfg: RamiConfig) -> int:
        return len(self.unseen_cards(cfg))

    def opponent_hand_estimate(self, cfg: RamiConfig, opponent_idx: int,
                                stock_size: int) -> dict:
        """Estimate opponent's hand composition.

        Returns:
          - hand_count: exact number of cards in opponent's hand (by arithmetic)
          - unseen_count: total unseen cards
          - stock_estimate: estimated cards in stock (= stock_size, known)
          - opponent_hidden_estimate: estimated cards in opponent's hand
                                       = unseen_count - stock_size
        """
        unseen = self.unseen_count(cfg)
        hand = self.hand_count(opponent_idx)
        return {
            "hand_count": hand,
            "unseen_count": unseen,
            "stock_size": stock_size,
            "opponent_hidden_estimate": unseen - stock_size,
            "arithmetic_consistent": (unseen - stock_size) == hand,
        }

    def probability_of_drawing(self, target_rank: int, target_suit: int,
                                cfg: RamiConfig, stock_size: int,
                                opponent_idx: int) -> float:
        """Probability that the next stock draw is the target card.

        P(target in stock | unseen) = count(target in unseen) / |unseen|
        P(target drawn next) = P(target in stock) × (1 / stock_size)
        """
        if stock_size == 0:
            return 0.0
        unseen = self.unseen_cards(cfg)
        # How many copies of (target_suit, target_rank) are unseen?
        matching = sum(1 for (s, r, _) in unseen
                       if s == target_suit and r == target_rank)
        # Probability the next card in stock is the target
        # = (matching / |unseen|) × (stock_size / stock_size)
        # Simplified: matching / |unseen| (since stock draws uniformly from unseen
        # except for opponent's hand)
        if not unseen:
            return 0.0
        # Probability the target is in stock (not opponent's hand):
        p_in_stock = stock_size / len(unseen)
        # Conditional probability of drawing it if in stock: matching / stock_size
        # But matching includes copies that could be in either pile.
        # Simplified: probability of drawing it next =
        #   (matching / |unseen|) × (stock_size / |unseen|) ... no, simpler:
        # = (matching / |unseen|) × (1 / stock_size)  ... if we knew it was in stock
        # Actually the cleanest:
        # P(draw target next) = (# copies in stock) / stock_size
        # But we don't know # copies in stock. Use:
        # E[# copies in stock] = matching × (stock_size / |unseen|)
        # So P = matching × stock_size / |unseen| / stock_size = matching / |unseen|
        return matching / len(unseen)
