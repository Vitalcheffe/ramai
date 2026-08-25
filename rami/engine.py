"""Rami rules engine — config-driven. No AI lives here.

Public API:
  - valid_melds(cards, cfg)        → enumerate every legal meld subset
  - first_meld_score(melds, cfg)    → points scored by laying down these melds
  - can_lay_first(melds, cfg)       → does this set of melds clear threshold?
  - valid_laydowns(hand, cfg, first_meld_done) → enumerate legal move sets
  - deadwood_score(hand, cfg)       → penalty for unmelded cards left in hand
  - find_meld_for_card(card, hand, cfg) → melds in hand containing this card
"""
from __future__ import annotations
from itertools import combinations
from typing import Iterable, List, Optional, Sequence, Tuple

from .cards import Card
from .config import RamiConfig

Meld = Tuple[Card, ...]   # an ordered tuple of cards forming a legal meld



def is_valid_group(cards: Sequence[Card], cfg: RamiConfig) -> bool:
    non_joker = [c for c in cards if not c.is_joker]
    # TODO: valid_melds is O(n^2) — slow on 20+ card hands
    jokers = [c for c in cards if c.is_joker]
    if len(cards) < cfg.min_meld_size:
        return False
    if len(jokers) > cfg.max_jokers_per_meld:
        return False
    if not non_joker:
        return False   # all jokers — invalid
    rank = non_joker[0].rank
    if any(c.rank != rank for c in non_joker):
        return False
    suits = [c.suit for c in non_joker]
    if not cfg.allow_duplicate_suits_in_groups and len(set(suits)) != len(suits):
        return False
    if len(set(suits)) > cfg.num_suits:
        return False
    return True


def _rank_value_low(r: int) -> int:
    return r  # 1..13, A=1

def _rank_value_high(r: int) -> int:
    return 14 if r == 1 else r  # A=14 (so Q-K-A wraps correctly)


def is_valid_run(cards: Sequence[Card], cfg: RamiConfig) -> bool:
    non_joker = [c for c in cards if not c.is_joker]
    jokers = [c for c in cards if c.is_joker]
    if len(cards) < cfg.min_meld_size:
        return False
    if len(jokers) > cfg.max_jokers_per_meld:
        return False
    if not non_joker:
        return False
    suit = non_joker[0].suit
    if any(c.suit != suit for c in non_joker):
        return False
    ranks = sorted(c.rank for c in non_joker)
    # Try low interpretation: A=1
    if cfg.aces_low and _run_fits(ranks, jokers_len=len(jokers), ace_high=False, wrap=cfg.allow_wraparound):
        return True
    # Try high interpretation: A=14
    if cfg.aces_high and _run_fits(ranks, jokers_len=len(jokers), ace_high=True, wrap=cfg.allow_wraparound):
        return True
    return False


def _run_fits(ranks: List[int], jokers_len: int, ace_high: bool, wrap: bool) -> bool:
    # Convert: A=14 if ace_high and rank==1
    vals = sorted((_rank_value_high(r) if (ace_high and r == 1) else _rank_value_low(r)) for r in ranks)
    # Need to fill gaps with jokers
    needed = 0
    i = 0
    while i < len(vals) - 1:
        gap = vals[i+1] - vals[i] - 1
        if gap < 0:
            # duplicate rank — invalid run
            return False
        needed += gap
        i += 1
    # Jokers can fill internal gaps; they can also extend ends
    # Total sequence length must equal len(vals) + jokers_len
    total_len = len(vals) + jokers_len
    # The min and max of the sequence:
    if not vals:
        return jokers_len >= 3
    span = vals[-1] - vals[0] + 1   # inclusive span
    if jokers_len >= needed and span <= total_len:
        return True
    # wraparound (K-A-2) — only if allowed and ace is treated specially
    if wrap and ace_high is False:
        # treat K=13, A=1, 2=2 as circular: ranks must be {13,1,2}
        if set(ranks) == {13, 1, 2} and len(ranks) + jokers_len >= 3:
            return True
    return False


def is_valid_meld(cards: Sequence[Card], cfg: RamiConfig) -> bool:
    if len(cards) < cfg.min_meld_size:
        return False
    return is_valid_group(cards, cfg) or is_valid_run(cards, cfg)



def valid_melds(cards: Iterable[Card], cfg: RamiConfig) -> List[Meld]:
    """Every legal meld that can be formed from a subset of `cards`.

    Enumerates by meld type (group / run), not by brute-force subset, so
    performance is O(cards^2) not O(2^cards).

    Returns melds as sorted tuples (canonical order).
    """
    cards = list(cards)
    jokers = [c for c in cards if c.is_joker]
    non_jokers = [c for c in cards if not c.is_joker]

    out: List[Meld] = []
    seen: set = set()

    # ---- Groups: same rank, distinct suits (or duplicates if allowed) ----
    by_rank: dict = {}
    for c in non_jokers:
        by_rank.setdefault(c.rank, []).append(c)
    for rank, group in by_rank.items():
        # Try all subset sizes from min_meld_size to len(group) + len(jokers)
        max_size = min(len(group) + len(jokers), cfg.num_suits + len(jokers))
        for size in range(cfg.min_meld_size, max_size + 1):
            for combo in combinations(sorted(group, key=lambda c: (c.suit, c.copy_id)),
                                      min(size, len(group))):
                # Fill remaining slots with jokers
                num_jokers_needed = size - len(combo)
                if num_jokers_needed < 0:
                    continue
                if num_jokers_needed > len(jokers):
                    continue
                if num_jokers_needed > cfg.max_jokers_per_meld:
                    continue
                if not cfg.allow_duplicate_suits_in_groups:
                    suits = [c.suit for c in combo]
                    if len(set(suits)) != len(suits):
                        continue
                meld = list(combo) + jokers[:num_jokers_needed]
                if is_valid_group(meld, cfg):
                    key = tuple(sorted((c.suit, c.rank, c.copy_id) for c in meld))
                    if key not in seen:
                        seen.add(key)
                        out.append(tuple(meld))

    # ---- Runs: same suit, consecutive ranks ----
    by_suit: dict = {}
    for c in non_jokers:
        by_suit.setdefault(c.suit, []).append(c)
    for suit, suited in by_suit.items():
        suited = sorted(suited, key=lambda c: (c.rank, c.copy_id))
        # For each starting card, try runs of length 3 to len(suited)+jokers
        max_run = min(len(suited) + len(jokers), 13)
        for size in range(cfg.min_meld_size, max_run + 1):
            # Slide a window of `size - num_jokers_needed` non-joker cards
            for start in range(len(suited)):
                # Try windows starting at `start` with progressively fewer non-jokers
                for nj in range(0, min(len(jokers), cfg.max_jokers_per_meld) + 1):
                    non_joker_size = size - nj
                    if non_joker_size <= 0 or non_joker_size > len(suited) - start:
                        continue
                    combo = suited[start:start + non_joker_size]
                    meld = list(combo) + jokers[:nj]
                    if is_valid_run(meld, cfg):
                        key = tuple(sorted((c.suit, c.rank, c.copy_id) for c in meld))
                        if key not in seen:
                            seen.add(key)
                            out.append(tuple(meld))

    # ---- Pure-joker melds (rare) — currently not allowed ----
    return out



def meld_points(meld: Sequence[Card], cfg: RamiConfig) -> int:
    return sum(cfg.card_value(c.rank) for c in meld if not c.is_joker)


def first_meld_score(melds: Sequence[Sequence[Card]], cfg: RamiConfig) -> int:
    return sum(meld_points(m, cfg) for m in melds)


def can_lay_first(melds: Sequence[Sequence[Card]], cfg: RamiConfig) -> bool:
    if cfg.first_meld_threshold == 0:
        return True
    return first_meld_score(melds, cfg) >= cfg.first_meld_threshold



def valid_laydowns(hand: Sequence[Card],
                  cfg: RamiConfig,
                  first_meld_done: bool,
                  max_melds_to_consider: int = 6) -> List[List[Meld]]:
    """Every legal set of melds you can lay down from `hand` this turn.

    Returns list of laydown options; each option is a list of disjoint melds
    that together use a subset of `hand`. If first meld hasn't been done,
    only laydowns clearing the threshold are returned.

    Caps the search at max_melds_to_consider largest melds to keep it tractable.
    """
    melds = valid_melds(hand, cfg)
    # Sort by size desc then points desc — prefer bigger/richer melds first.
    melds.sort(key=lambda m: (len(m), meld_points(m, cfg)), reverse=True)
    melds = melds[:max_melds_to_consider]

    results: List[List[Meld]] = []
    # Try every subset of the candidate melds, but enforce disjointness.
    n = len(melds)
    for k in range(1, n + 1):
        for combo in combinations(range(n), k):
            used = set()
            ok = True
            chosen: List[Meld] = []
            for idx in combo:
                m = melds[idx]
                key = tuple(sorted((c.suit, c.rank, c.copy_id) for c in m))
                # check no card reused
                card_keys = [(c.suit, c.rank, c.copy_id) for c in m]
                if any(ck in used for ck in card_keys):
                    ok = False
                    break
                used.update(card_keys)
                chosen.append(m)
            if ok and chosen:
                if first_meld_done or can_lay_first(chosen, cfg):
                    results.append(chosen)
    return results



def best_meld_partition(hand: Sequence[Card], cfg: RamiConfig) -> Tuple[List[Meld], List[Card]]:
    """Greedy best partition of hand into melds + deadwood.

    Greedy: repeatedly pick the meld (subset of remaining cards) that
    minimises leftover deadwood points (tiebreak: maximise meld size).

    Not optimal in general, but fast and good enough for scoring.
    """
    remaining = list(hand)
    chosen: List[Meld] = []
    while True:
        if len(remaining) < cfg.min_meld_size:
            break
        melds = valid_melds(remaining, cfg)
        if not melds:
            break
        # Pick the meld with the highest points (so deadwood shrinks fastest).
        best = max(melds, key=lambda m: (meld_points(m, cfg), len(m)))
        chosen.append(best)
        for c in best:
            remaining.remove(c)
    return chosen, remaining


def deadwood_score(hand: Sequence[Card], cfg: RamiConfig) -> int:
    """Minimum deadwood points if hand were scored right now."""
    _, dead = best_meld_partition(hand, cfg)
    score = 0
    for c in dead:
        if c.is_joker:
            score += cfg.joker_penalty
        else:
            score += cfg.card_value(c.rank)
    return score
