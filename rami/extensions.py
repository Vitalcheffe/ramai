"""Meld extensions + joker designation.

P2: Allow extending an existing laid meld.
    Example: opponent laid 5♥-6♥-7♥. If I have 4♥ (and I've passed my
    first-meld threshold), I can lay 4♥ on the table next to that meld,
    extending it to 4♥-5♥-6♥-7♥. The card counts as part of the meld
    for end-of-game scoring.

P3: Joker designation.
    When a joker is used in a meld, the rules of Rami require the player
    to declare what card the joker represents. We compute that
    automatically from the surrounding cards: e.g. in meld [5♥, ★, 7♥]
    the joker represents 6♥. The result is exposed so the player knows
    which physical card to play on top of it if they extend the meld later.
"""
from __future__ import annotations
from typing import List, Optional, Tuple, Sequence
from dataclasses import dataclass

from .cards import Card
from .config import RamiConfig
from .engine import is_valid_run, is_valid_group


@dataclass(frozen=True)
class JokerDesignation:
    """What card a joker represents in a meld."""
    joker: Card
    represented_suit: int    # 0..3, or -1 if undefined
    represented_rank: int    # 1..13, or 0 if undefined
    meld_index: int          # which meld in player.laid_melds

    @property
    def name(self) -> str:
        if self.represented_rank == 0:
            return f"{self.joker.name} (unassigned)"
        from .cards import SUIT_SYMBOLS, RANK_NAMES
        return f"{self.joker.name} → {RANK_NAMES[self.represented_rank]}{SUIT_SYMBOLS[self.represented_suit]}"


def designate_jokers(meld: Sequence[Card], cfg: RamiConfig) -> List[JokerDesignation]:
    """For each joker in `meld`, compute the card it represents.

    Returns one JokerDesignation per joker in the meld. If the joker's
    position can't be uniquely determined (e.g. pure joker meld or
    ambiguous), represented_rank=0 (unassigned).

    Examples:
      [5♥, ★, 7♥]           → joker represents 6♥
      [★, 5♥, 6♥, 7♥]       → joker represents 4♥ (run extension low)
      [5♥, 6♥, 7♥, ★]       → joker represents 8♥ (run extension high)
      [7♠, 7♥, ★]           → joker represents 7♦ or 7♣ (ambiguous → pick 7♦)
      [7♠, ★, ★]            → jokers represent 7♥, 7♦ (in order)
    """
    designations: List[JokerDesignation] = []
    non_jokers = [c for c in meld if not c.is_joker]
    jokers = [c for c in meld if c.is_joker]
    if not jokers:
        return []

    # Determine meld type: group or run?
    if non_jokers and all(c.rank == non_jokers[0].rank for c in non_jokers):
        # GROUP: joker represents same rank, different suit
        rank = non_jokers[0].rank
        used_suits = {c.suit for c in non_jokers}
        available_suits = [s for s in range(cfg.num_suits) if s not in used_suits]
        for i, jk in enumerate(jokers):
            suit = available_suits[i] if i < len(available_suits) else -1
            if suit == -1:
                designations.append(JokerDesignation(joker=jk, represented_suit=-1,
                                                     represented_rank=0,
                                                     meld_index=0))
            else:
                designations.append(JokerDesignation(joker=jk, represented_suit=suit,
                                                     represented_rank=rank,
                                                     meld_index=0))
        return designations

    # RUN: same suit, consecutive ranks
    if non_jokers and all(c.suit == non_jokers[0].suit for c in non_jokers):
        suit = non_jokers[0].suit
        # Sort the non-jokers by rank
        sorted_nj = sorted(non_jokers, key=lambda c: c.rank)
        # Try ace_low first
        if cfg.aces_low:
            devals = _designate_jokers_in_run(sorted_nj, jokers, suit, cfg,
                                                ace_high=False,
                                                original_meld=meld)
            if devals is not None:
                return devals
        if cfg.aces_high:
            devals = _designate_jokers_in_run(sorted_nj, jokers, suit, cfg,
                                                ace_high=True,
                                                original_meld=meld)
            if devals is not None:
                return devals
        # Fall back: unassigned
        return [JokerDesignation(joker=jk, represented_suit=-1, represented_rank=0,
                                 meld_index=0) for jk in jokers]

    # Mixed or pure joker — unassigned
    return [JokerDesignation(joker=jk, represented_suit=-1, represented_rank=0,
                             meld_index=0) for jk in jokers]


def _designate_jokers_in_run(sorted_nj: List[Card], jokers: List[Card],
                              suit: int, cfg: RamiConfig,
                              ace_high: bool,
                              original_meld: Sequence[Card] = None) -> Optional[List[JokerDesignation]]:
    """Assign ranks to jokers in a run.

    Uses the joker's POSITION in the original meld to decide:
      - Joker BEFORE all non-jokers  → extends LOW (rank = min-1, min-2, ...)
      - Joker AFTER all non-jokers   → extends HIGH (rank = max+1, max+2, ...)
      - Joker BETWEEN non-jokers     → fills the internal gap
    """
    def conv(r):
        if ace_high and r == 1:
            return 14
        return r

    vals = sorted(conv(c.rank) for c in sorted_nj)
    if len(set(vals)) != len(vals):
        return None

    span_min = vals[0]
    span_max = vals[-1]
    expected = list(range(span_min, span_max + 1))
    internal_missing = [r for r in expected if r not in vals]
    if len(internal_missing) > len(jokers):
        return None

    # Classify each joker by its position in the original meld
    designations: List[JokerDesignation] = []
    # We need to track which joker gets which assignment. Build a list of
    # (joker_card, position_in_meld) so we can sort by position.
    if original_meld is None:
        # Fallback: assume order is [jokers..., non_jokers...] (all jokers first)
        # then split internal/external arbitrarily. Not great but safe default.
        original_meld = list(jokers) + list(sorted_nj)

    # For each joker, find its position in original_meld
    joker_positions = []
    nj_positions = []
    for i, card in enumerate(original_meld):
        if card.is_joker:
            joker_positions.append((i, card))
        else:
            nj_positions.append((i, card))
    nj_positions.sort(key=lambda x: x[0])
    if not nj_positions:
        return None
    first_nj_pos = nj_positions[0][0]
    last_nj_pos = nj_positions[-1][0]

    # Assign each joker based on position
    # We need to determine, for each joker, whether it's:
    #   - "before" (position < first_nj_pos) → extend low
    #   - "after"  (position > last_nj_pos)  → extend high
    #   - "between" (first_nj_pos < pos < last_nj_pos) → fill internal gap
    jokers_before = [jk for pos, jk in joker_positions if pos < first_nj_pos]
    jokers_between = [jk for pos, jk in joker_positions
                      if first_nj_pos < pos < last_nj_pos]
    jokers_after = [jk for pos, jk in joker_positions if pos > last_nj_pos]

    # Internal gaps (must be filled by jokers_between first, then by others if any)
    if len(jokers_between) < len(internal_missing):
        # Need to dip into before/after jokers to fill gaps.
        # Take from "before" first (arbitrary choice).
        shortfall = len(internal_missing) - len(jokers_between)
        borrowed_from_before = jokers_before[:shortfall]
        jokers_before = jokers_before[shortfall:]
        jokers_between = jokers_between + borrowed_from_before

    # Fill internal gaps
    for i, missing_rank in enumerate(internal_missing):
        if i >= len(jokers_between):
            return None
        actual_rank = 1 if (ace_high and missing_rank == 14) else missing_rank
        if not (1 <= actual_rank <= cfg.ranks_per_suit):
            return None
        designations.append(JokerDesignation(
            joker=jokers_between[i],
            represented_suit=suit,
            represented_rank=actual_rank,
            meld_index=0,
        ))

    # Extend low (jokers_before)
    # The leftmost joker in the meld gets the lowest rank.
    # Sort jokers_before by position descending (rightmost first = closest to meld)
    jokers_before_sorted = sorted(
        [(pos, jk) for pos, jk in joker_positions if pos < first_nj_pos],
        key=lambda x: -x[0])  # rightmost first
    cur_rank = span_min - 1
    for pos, jk in jokers_before_sorted:
        actual_rank = 1 if (ace_high and cur_rank == 14) else cur_rank
        if actual_rank < 1:
            return None
        designations.append(JokerDesignation(
            joker=jk, represented_suit=suit,
            represented_rank=actual_rank, meld_index=0))
        cur_rank -= 1

    # Extend high (jokers_after)
    jokers_after_sorted = sorted(
        [(pos, jk) for pos, jk in joker_positions if pos > last_nj_pos],
        key=lambda x: x[0])  # leftmost first
    cur_rank = span_max + 1
    for pos, jk in jokers_after_sorted:
        if cur_rank == 14 and ace_high:
            actual_rank = 1
        elif cur_rank > cfg.ranks_per_suit and not (ace_high and cur_rank == 14):
            return None
        else:
            actual_rank = cur_rank
            if actual_rank > cfg.ranks_per_suit:
                return None
        designations.append(JokerDesignation(
            joker=jk, represented_suit=suit,
            represented_rank=actual_rank, meld_index=0))
        cur_rank += 1

    return designations


# ---------- P2: Meld extensions ----------

@dataclass
class MeldExtension:
    """A card that extends an existing laid meld."""
    card: Card                  # the card being added
    meld_owner: int             # which player owns the meld being extended
    meld_index: int             # index into player.laid_melds
    extends_at: str             # "start" | "end" | "interior" (joker replacement)


def find_meld_extensions(card: Card,
                         all_laid_melds: List[Tuple[int, int, Tuple[Card, ...]]],
                         cfg: RamiConfig) -> List[MeldExtension]:
    """Find every laid meld that `card` can extend.

    `all_laid_melds` is a list of (player_idx, meld_idx, meld_cards).

    A card can extend a meld if:
      - It's not a joker
      - The meld is a group of the same rank, and the card's suit isn't already
        in the meld (or duplicates are allowed)
      - The meld is a run of the same suit, and the card is one rank below the
        min or one rank above the max (or fills a joker slot)
    """
    if card.is_joker or not cfg.allow_meld_extensions:
        return []

    extensions: List[MeldExtension] = []
    for (p_idx, m_idx, meld) in all_laid_melds:
        non_jokers = [c for c in meld if not c.is_joker]
        if not non_jokers:
            continue
        # GROUP
        if all(c.rank == non_jokers[0].rank for c in non_jokers):
            if card.rank != non_jokers[0].rank:
                continue
            if not cfg.allow_duplicate_suits_in_groups:
                if card.suit in {c.suit for c in non_jokers}:
                    continue
            # Check we won't exceed num_suits + jokers
            existing_jokers = sum(1 for c in meld if c.is_joker)
            if len(non_jokers) + existing_jokers >= cfg.num_suits + cfg.max_jokers_per_meld:
                continue
            extensions.append(MeldExtension(card=card, meld_owner=p_idx,
                                             meld_index=m_idx,
                                             extends_at="end"))
            continue
        # RUN
        if all(c.suit == non_jokers[0].suit for c in non_jokers):
            if card.suit != non_jokers[0].suit:
                continue
            ranks = sorted(c.rank for c in non_jokers)
            # Try ace-low
            if cfg.aces_low and (card.rank == ranks[0] - 1 and card.rank >= 1):
                extensions.append(MeldExtension(card=card, meld_owner=p_idx,
                                                 meld_index=m_idx,
                                                 extends_at="start"))
                continue
            if cfg.aces_high and card.rank == 1 and ranks[-1] == 13:
                # Ace extends K-x high
                extensions.append(MeldExtension(card=card, meld_owner=p_idx,
                                                 meld_index=m_idx,
                                                 extends_at="end"))
                continue
            if card.rank == ranks[-1] + 1 and card.rank <= cfg.ranks_per_suit:
                extensions.append(MeldExtension(card=card, meld_owner=p_idx,
                                                 meld_index=m_idx,
                                                 extends_at="end"))
                continue
            # Check if there's a joker we can replace
            designations = designate_jokers(meld, cfg)
            for jd in designations:
                if jd.represented_rank == card.rank and jd.represented_suit == card.suit:
                    extensions.append(MeldExtension(card=card, meld_owner=p_idx,
                                                     meld_index=m_idx,
                                                     extends_at="interior"))
                    break
    return extensions


def all_laid_melds(state) -> List[Tuple[int, int, Tuple[Card, ...]]]:
    """Flatten all players' laid melds into a list."""
    out = []
    for p_idx, p in enumerate(state.players):
        for m_idx, meld in enumerate(p.laid_melds):
            out.append((p_idx, m_idx, meld))
    return out
