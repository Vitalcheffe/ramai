"""Strategy AI — card counting + probability scoring."""
from __future__ import annotations
from typing import List, Set, Tuple, Optional
from collections import Counter
import random

from .base import AI, ActionContext
from ..cards import Card
from ..config import RamiConfig
from ..engine import (
    valid_melds, is_valid_meld, valid_laydowns, meld_points,
    best_meld_partition, deadwood_score
)
from ..game import Move, GameState


class StrategyAI(AI):
    name = "strategy"

    def __init__(self, seed: int = 0, risk_aversion: float = 1.0):
        self.rng = random.Random(seed)
    # TODO: opponent_want_probability is a rough heuristic, not calibrated
        self.risk_aversion = risk_aversion

    def choose_move(self, ctx: ActionContext) -> Move:
        cfg = ctx.state.cfg
        moves = ctx.legal_moves

        # Compute unseen cards
        visible = self._visible_cards(ctx.state)
        full_deck = self._full_deck_keys(cfg)
        unseen_keys = full_deck - visible

        # Count useful unseen cards
        hand_keys = set((c.suit, c.rank, c.copy_id) for c in ctx.my_hand)

        # Probability of drawing a useful card from stock
        useful_keys = self._useful_card_keys(ctx.my_hand, cfg)
        p_useful_stock = (sum(1 for k in unseen_keys if (k[0], k[1]) in useful_keys)
                          / max(1, len(unseen_keys)))

        # Score every move
        def move_score(m: Move) -> float:
            score = 0.0

            # lay melds aggressively — reduces deadwood
            for meld in m.laydowns:
                score += meld_points(meld, cfg) * 1.5

            # Compute resulting hand after move
            remaining = self._hand_after(ctx.my_hand, m, ctx.state)
            new_deadwood = deadwood_score(remaining, cfg)
            old_deadwood = deadwood_score(ctx.my_hand, cfg)
            score += (old_deadwood - new_deadwood) * 0.5  # deadwood reduction worth ~half a point

            # Discard quality: prefer throwing low-value cold cards
            discard = m.discard
            if discard.is_joker:
                score -= 100  # never throw a joker unless forced
            else:
                score -= cfg.card_value(discard.rank) * 0.3
                # Penalise throwing cards the opponent likely wants
                opp_want_prob = self._opponent_want_probability(discard, ctx)
                score -= opp_want_prob * 5 * self.risk_aversion

            # Drawing from discard gives a known card, stock gives random
            if m.draw_source == "stock":
                # Expected gain: probability of useful card × avg usefulness
                score += p_useful_stock * 3.0
            else:
                # Drawing from discard gives a known card — useful iff it
                # completes a meld or reduces deadwood
                if (discard.suit, discard.rank) in useful_keys or discard.is_joker:
                    score += 4.0

            # Going out bonus
            if len(remaining) == 0:
                score += 1000

            return score

        best = max(moves, key=lambda m: (move_score(m), -self.rng.random()))
        return best

    # ---------- Helpers ----------

    def _visible_cards(self, state: GameState) -> Set[Tuple[int, int, int]]:
        out: Set[Tuple[int, int, int]] = set()
        # My hand
        for c in state.current_player.hand.cards:
            out.add((c.suit, c.rank, c.copy_id))
        # Discard pile
        for c in state.discard:
            out.add((c.suit, c.rank, c.copy_id))
        # All laid melds
        for p in state.players:
            for meld in p.laid_melds:
                for c in meld:
                    out.add((c.suit, c.rank, c.copy_id))
        return out

    def _full_deck_keys(self, cfg: RamiConfig) -> Set[Tuple[int, int, int]]:
        out: Set[Tuple[int, int, int]] = set()
        for copy_id in range(cfg.num_decks):
            for s in range(cfg.num_suits):
                for r in range(1, cfg.ranks_per_suit + 1):
                    out.add((s, r, copy_id))
            for _ in range(cfg.num_jokers_per_deck):
                # Jokers have suit=-1, rank=0
                # They're distinguished by copy_id only — represent each as (−1, 0, joker_idx)
                pass
        # Add joker keys (suit=-1, rank=0). Multiple jokers per deck — use a separate index space.
        joker_idx = 0
        for copy_id in range(cfg.num_decks):
            for _ in range(cfg.num_jokers_per_deck):
                out.add((-1, 0, 1000 + joker_idx))
                joker_idx += 1
        return out

    def _useful_card_keys(self, hand: List[Card], cfg: RamiConfig) -> Set[Tuple[int, int]]:
        useful: Set[Tuple[int, int]] = set()
        # Cards that extend an existing 2-card partial meld
        for c in hand:
            if c.is_joker:
                continue
            # Try pairing with another card in hand to form a 2-card partial
            for c2 in hand:
                if c2.is_joker or c2 == c:
                    continue
                # Same rank → group potential (need 3rd)
                if c.rank == c2.rank:
                    for s in range(cfg.num_suits):
                        if s != c.suit and s != c2.suit:
                            useful.add((s, c.rank))
                # Same suit, adjacent rank → run potential
                if c.suit == c2.suit:
                    for delta in (-2, -1, 1, 2):
                        target = c.rank + delta
                        if 1 <= target <= cfg.ranks_per_suit and target != c2.rank:
                            useful.add((c.suit, target))
        # Jokers are always useful
        useful.add((-1, 0))
        return useful

    def _hand_after(self, hand: List[Card], move: Move, state: GameState) -> List[Card]:
        # Add drawn card
        if move.draw_source == "stock":
            drawn = state.stock[-1] if state.stock else None
        else:
            drawn = state.discard[-1] if state.discard else None
        new_hand = list(hand)
        if drawn is not None:
            new_hand.append(drawn)
        # Remove meld cards
        used = set()
        for meld in move.laydowns:
            for c in meld:
                # Remove by key
                key = (c.suit, c.rank, c.copy_id)
                if key in used:
                    continue
                used.add(key)
                # Remove first matching card
                for i, hc in enumerate(new_hand):
                    if (hc.suit, hc.rank, hc.copy_id) == key:
                        new_hand.pop(i)
                        break
        # Remove discard
        dkey = (move.discard.suit, move.discard.rank, move.discard.copy_id)
        for i, hc in enumerate(new_hand):
            if (hc.suit, hc.rank, hc.copy_id) == dkey:
                new_hand.pop(i)
                break
        return new_hand

    def _opponent_want_probability(self, card: Card, ctx: ActionContext) -> float:
        """Rough estimate: how likely is the opponent to want this card?

        Uses the count of cards in opponent's laid melds of the same rank/suit.
        Heuristic — not perfect, but better than nothing.
        """
        if card.is_joker:
            return 1.0  # jokers are always wanted
        # Look at opponent's melds
        match_count = 0
        for i, p in enumerate(ctx.state.players):
            if i == ctx.state.current:
                continue
            for meld in p.laid_melds:
                for c in meld:
                    if c.rank == card.rank:
                        match_count += 1
                    if c.suit == card.suit and abs(c.rank - card.rank) <= 2:
                        match_count += 0.5
        # Fewer cards in opponent hand = more likely they're fishing
        # for specific cards. More cards = more options.
        opp_hand_size = sum(ctx.opponent_hand_sizes)
        if opp_hand_size == 0:
            return 1.0
        base = min(1.0, match_count / 4.0)
        # If opponent has very few cards, scale up
        if opp_hand_size <= 3:
            base = min(1.0, base + 0.3)
        return base
