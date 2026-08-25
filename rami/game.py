"""Game state + turn loop. Pure simulation — no I/O, no vision."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from .cards import Card, build_deck, Hand
from .config import RamiConfig
from .engine import (
    valid_laydowns, can_lay_first, meld_points, best_meld_partition, deadwood_score
)


@dataclass
class PlayerState:
    hand: Hand
    has_laid_first: bool = False
    laid_melds: List[Tuple[Card, ...]] = field(default_factory=list)


@dataclass
class GameState:
    cfg: RamiConfig
    stock: List[Card]
    discard: List[Card]            # top is discard[-1]
    players: List[PlayerState]
    current: int = 0               # whose turn (index into players)
    turn: int = 0
    turns_since_meld: int = 0
    history: List[dict] = field(default_factory=list)
    winner: Optional[int] = None
    terminal: bool = False

    @property
    def current_player(self) -> PlayerState:
        return self.players[self.current]
    # TODO: stalemate detection is turn-based, not state-based

    @property
    def top_discard(self) -> Optional[Card]:
        return self.discard[-1] if self.discard else None


def new_game(cfg: RamiConfig, seed: Optional[int] = None) -> GameState:
    deck = build_deck(cfg, seed=seed)
    hands = [Hand(cards=[]) for _ in range(cfg.num_players)]
    for _ in range(cfg.hand_size):
        for h in hands:
            h.add(deck.pop())
    # First upcard: take from top of stock into discard
    discard = [deck.pop()] if deck else []
    return GameState(cfg=cfg, stock=deck, discard=discard,
                     players=[PlayerState(hand=h) for h in hands])



@dataclass
class Move:
    """A single turn action: draw, optional laydowns, discard."""
    draw_source: str        # "stock" | "discard"
    laydowns: List[Tuple[Card, ...]]   # melds to lay (may be empty)
    discard: Card           # card to end turn with


def legal_moves(state: GameState) -> List[Move]:
    player = state.current_player
    cfg = state.cfg
    moves: List[Move] = []

    # 1) Draw source
    draw_sources = []
    if state.stock:
        draw_sources.append("stock")
    if state.cfg.draw_from_stock_or_discard and state.discard:
        # Rami 51 rule: cannot take from discard until first meld is laid
        if cfg.block_discard_before_threshold and not player.has_laid_first:
            pass  # discard forbidden
        else:
            draw_sources.append("discard")
    if not draw_sources:
        return []  # no moves possible

    # 2) For each draw source, compute possible post-draw hands
    for src in draw_sources:
        if src == "stock":
            drawn = state.stock[-1]
        else:
            drawn = state.discard[-1]
        # Hypothetical hand after drawing
        new_hand_cards = player.hand.cards + [drawn]
        # Laydown options
        laydown_options = valid_laydowns(new_hand_cards, cfg,
                                          first_meld_done=player.has_laid_first)
        # Add the "no laydown" option (still need to discard)
        all_options: List[List[Tuple[Card, ...]]] = [[]] + laydown_options

        for lay in all_options:
            # Cards used by laydowns
            used = set()
            for m in lay:
                for c in m:
                    used.add((c.suit, c.rank, c.copy_id))
            # Remaining cards in hand after laydowns (and after drawing the source card)
            remaining = [c for c in new_hand_cards
                         if (c.suit, c.rank, c.copy_id) not in used]
            # If hand is empty after laydown (going out), no discard needed —
            # but classic Rami requires a discard to end. Handle both.
            if not remaining:
                # Going out without discard — allowed only if must_discard_to_end_turn is False
                if not cfg.must_discard_to_end_turn:
                    moves.append(Move(draw_source=src, laydowns=lay, discard=drawn))
                continue
            # Pick a discard from remaining
            for d in remaining:
                if d.is_joker and not cfg.can_discard_joker:
                    continue
                # discard must NOT be the same card we just drew from discard
                # (you can't grab and immediately throw the same card)
                if src == "discard" and d == drawn and len(remaining) == 1:
                    continue
                moves.append(Move(draw_source=src, laydowns=lay, discard=d))
    return moves


def apply_move(state: GameState, move: Move) -> GameState:
    player = state.current_player
    cfg = state.cfg

    # 1) Draw
    if move.draw_source == "stock":
        drawn = state.stock.pop()
    else:
        drawn = state.discard.pop()
    player.hand.add(drawn)

    # 2) Laydowns
    if move.laydowns:
        for meld in move.laydowns:
            # Remove each card from hand
            for c in meld:
                player.hand.remove(c)
            player.laid_melds.append(meld)
            if not player.has_laid_first:
                player.has_laid_first = True
        state.turns_since_meld = 0
    else:
        state.turns_since_meld += 1

    # 3) Discard
    player.hand.remove(move.discard)
    state.discard.append(move.discard)

    # 4) Check win
    if len(player.hand) == 0:
        state.winner = state.current
        state.terminal = True
        return state

    # 5) Check stalemate
    if state.turns_since_meld >= cfg.stalemate_turns:
        state.terminal = True
        return state

    # 6) Check stock empty
    if not state.stock and not state.discard:
        state.terminal = True
        return state

    # 7) Next player
    state.current = (state.current + 1) % cfg.num_players
    state.turn += 1
    return state


def score_terminal(state: GameState) -> List[int]:
    """Per-player scores at game end (positive = good for player).

    If a player went out, they get +opponent_deadwood, opponent gets -own_deadwood.
    If stock ran out, lower-deadwood player wins the difference.
    """
    cfg = state.cfg
    scores: List[int] = []
    deadwoods = [deadwood_score(p.hand.cards, cfg) for p in state.players]
    if state.winner is not None:
        for i, p in enumerate(state.players):
            if i == state.winner:
                # sum of opponents' deadwood
                scores.append(sum(deadwoods[j] for j in range(len(state.players)) if j != i))
            else:
                scores.append(-deadwoods[i])
        return scores
    # Stock empty: lowest deadwood wins
    min_d = min(deadwoods)
    winners = [i for i, d in enumerate(deadwoods) if d == min_d]
    for i in range(len(state.players)):
        if i in winners:
            # share of others' deadwood
            n = len(winners)
            others = sum(deadwoods[j] for j in range(len(state.players)) if j != i)
            scores.append(others // n if n else 0)
        else:
            scores.append(-deadwoods[i])
    return scores
