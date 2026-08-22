# Rami rules config — every variant knob lives here, never in the AI code.
from __future__ import annotations
from dataclasses import dataclass, field, replace


@dataclass(frozen=True)
class RamiConfig:
    # Deck composition
    num_decks: int = 2                  # 2 decks of 54 = 108 cards
    num_jokers_per_deck: int = 2       # 2 jokers/deck → 4 total
    ranks_per_suit: int = 13           # A,2..10,J,Q,K
    num_suits: int = 4                  # ♠♥♦♣

    # Deal
    hand_size: int = 14
    num_players: int = 2

    # Meld rules
    min_meld_size: int = 3
    allow_duplicate_suits_in_groups: bool = False
    max_jokers_per_meld: int = 2
    aces_low: bool = True              # A-2-3 valid
    aces_high: bool = True             # Q-K-A valid
    allow_wraparound: bool = False      # K-A-2 invalid by default

    # First meld threshold (points). 0 = no threshold.
    first_meld_threshold: int = 30

    # Turn structure
    draw_from_stock_or_discard: bool = True   # may draw from discard pile
    must_discard_to_end_turn: bool = True
    can_discard_joker: bool = False           # house rule: jokers can't be thrown

    # Stalemate protection: if no meld is laid for N consecutive turns,
    # game ends and lowest-deadwood player wins.
    stalemate_turns: int = 50

    # Scoring at end (for opponent's deadwood if player goes out)
    face_card_value: int = 10
    ace_low_value: int = 1
    ace_high_value: int = 11
    joker_penalty: int = 25

    # Variant presets
    @classmethod
    def classic_moroccan(cls) -> "RamiConfig":
        return cls()  # defaults are Moroccan

    @classmethod
    def threshold_51(cls) -> "RamiConfig":
        return replace(cls(), first_meld_threshold=51)

    @classmethod
    def no_threshold(cls) -> "RamiConfig":
        return replace(cls(), first_meld_threshold=0)

    @classmethod
    def no_jokers(cls) -> "RamiConfig":
        return replace(cls(), num_jokers_per_deck=0)

    # Derived helpers
    @property
    def total_cards(self) -> int:
        return self.num_decks * (self.num_suits * self.ranks_per_suit + self.num_jokers_per_deck)

    def card_value(self, rank: int) -> int:
        # rank 1 = Ace ... 11=J, 12=Q, 13=K
        if rank == 1:
            return self.ace_low_value
        if rank >= 11:
            return self.face_card_value
        return rank
