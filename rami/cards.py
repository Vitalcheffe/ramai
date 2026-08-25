"""Card, Deck, Hand primitives. Pure data, no AI."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable, List, Optional
import random

from .config import RamiConfig

SUIT_SYMBOLS = ["♠", "♥", "♦", "♣"]
RANK_NAMES = {1: "A", 2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7",
              8: "8", 9: "9", 10: "10", 11: "J", 12: "Q", 13: "K"}


@dataclass(frozen=True, order=True)
class Card:
    """A single physical card. Joker: suit=-1, rank=0."""
    suit: int       # 0..3 or -1 for joker
    rank: int       # 1..13 or 0 for joker
    copy_id: int    # 0..num_decks-1, distinguishes duplicate cards

    @property
    def is_joker(self) -> bool:
        return self.suit == -1 or self.rank == 0

    @property
    def name(self) -> str:
        if self.is_joker:
            return "★"
        return f"{RANK_NAMES[self.rank]}{SUIT_SYMBOLS[self.suit]}"

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"Card({self.name}, copy={self.copy_id})"


def build_deck(cfg: RamiConfig, seed: Optional[int] = None) -> List[Card]:
    cards: List[Card] = []
    for copy_id in range(cfg.num_decks):
        for s in range(cfg.num_suits):
            for r in range(1, cfg.ranks_per_suit + 1):
                cards.append(Card(suit=s, rank=r, copy_id=copy_id))
        for _ in range(cfg.num_jokers_per_deck):
            cards.append(Card(suit=-1, rank=0, copy_id=copy_id))
    if seed is not None:
        random.Random(seed).shuffle(cards)
    return cards


def shuffle(cards: List[Card], rng: Optional[random.Random] = None) -> None:
    (rng or random).shuffle(cards)


@dataclass
class Hand:
    cards: List[Card]

    def __iter__(self):
        return iter(self.cards)

    def __len__(self) -> int:
        return len(self.cards)

    def add(self, card: Card) -> None:
        self.cards.append(card)

    def remove(self, card: Card) -> None:
        # Remove exact card instance (match by value, not identity)
        for i, c in enumerate(self.cards):
            if c == card:
                self.cards.pop(i)
                return
        raise ValueError(f"card {card} not in hand")

    def ranks(self) -> List[int]:
        return sorted(c.rank for c in self.cards if not c.is_joker)

    def by_suit(self) -> dict:
        out: dict = {}
        for c in self.cards:
            if c.is_joker:
                continue
            out.setdefault(c.suit, []).append(c)
        for s in out:
            out[s].sort(key=lambda x: x.rank)
        return out

    def jokers(self) -> List[Card]:
        return [c for c in self.cards if c.is_joker]
