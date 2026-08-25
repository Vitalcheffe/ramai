"""Test the rules engine: meld validation, enumeration, deadwood."""
import pytest
from rami.cards import Card, build_deck, Hand
from rami.config import RamiConfig
from rami.engine import (
    is_valid_group, is_valid_run, is_valid_meld,
    valid_melds, meld_points, first_meld_score, can_lay_first,
    valid_laydowns, best_meld_partition, deadwood_score,
)
from rami.game import new_game, legal_moves, apply_move, Move


def c(suit, rank, copy=0):
    return Card(suit=suit, rank=rank, copy_id=copy)


JOKER = lambda copy=0: Card(suit=-1, rank=0, copy_id=copy)


# ---------- Group validation ----------

def test_group_valid_3_kings():
    cfg = RamiConfig()
    cards = [c(0, 13, 0), c(1, 13, 0), c(2, 13, 0)]
    assert is_valid_group(cards, cfg)


def test_group_invalid_2_cards():
    cfg = RamiConfig()
    cards = [c(0, 13, 0), c(1, 13, 0)]
    assert not is_valid_group(cards, cfg)


def test_group_invalid_different_ranks():
    cfg = RamiConfig()
    cards = [c(0, 13, 0), c(1, 13, 0), c(2, 12, 0)]
    assert not is_valid_group(cards, cfg)


def test_group_invalid_duplicate_suit_strict():
    cfg = RamiConfig()
    cards = [c(0, 13, 0), c(0, 13, 1), c(1, 13, 0)]
    assert not is_valid_group(cards, cfg)


def test_group_valid_duplicate_suit_when_allowed():
    cfg = RamiConfig(allow_duplicate_suits_in_groups=True)
    cards = [c(0, 13, 0), c(0, 13, 1), c(1, 13, 0)]
    assert is_valid_group(cards, cfg)


def test_group_valid_with_joker():
    cfg = RamiConfig()
    cards = [c(0, 13, 0), c(1, 13, 0), JOKER(0)]
    assert is_valid_group(cards, cfg)


def test_group_invalid_too_many_jokers():
    cfg = RamiConfig(max_jokers_per_meld=1)
    cards = [c(0, 13, 0), JOKER(0), JOKER(1)]
    assert not is_valid_group(cards, cfg)


# ---------- Run validation ----------

def test_run_valid_3_consecutive():
    cfg = RamiConfig()
    cards = [c(0, 1, 0), c(0, 2, 0), c(0, 3, 0)]
    assert is_valid_run(cards, cfg)


def test_run_valid_with_joker_middle():
    cfg = RamiConfig()
    cards = [c(0, 5, 0), JOKER(0), c(0, 7, 0)]
    assert is_valid_run(cards, cfg)


def test_run_valid_with_joker_end():
    cfg = RamiConfig()
    cards = [c(0, 5, 0), c(0, 6, 0), JOKER(0)]
    assert is_valid_run(cards, cfg)


def test_run_valid_ace_low():
    cfg = RamiConfig()
    cards = [c(0, 1, 0), c(0, 2, 0), c(0, 3, 0)]
    assert is_valid_run(cards, cfg)


def test_run_valid_ace_high():
    cfg = RamiConfig()
    cards = [c(0, 12, 0), c(0, 13, 0), c(0, 1, 0)]
    assert is_valid_run(cards, cfg)


def test_run_invalid_wraparound():
    cfg = RamiConfig(allow_wraparound=False)
    cards = [c(0, 13, 0), c(0, 1, 0), c(0, 2, 0)]
    assert not is_valid_run(cards, cfg)


def test_run_valid_wraparound_when_allowed():
    cfg = RamiConfig(allow_wraparound=True)
    cards = [c(0, 13, 0), c(0, 1, 0), c(0, 2, 0)]
    assert is_valid_run(cards, cfg)


def test_run_invalid_different_suits():
    cfg = RamiConfig()
    cards = [c(0, 1, 0), c(1, 2, 0), c(0, 3, 0)]
    assert not is_valid_run(cards, cfg)


def test_run_invalid_duplicate_rank():
    cfg = RamiConfig()
    cards = [c(0, 5, 0), c(0, 5, 1), c(0, 7, 0)]
    assert not is_valid_run(cards, cfg)


# ---------- is_valid_meld dispatch ----------

def test_is_valid_meld_dispatches_group():
    cfg = RamiConfig()
    assert is_valid_meld([c(0, 7, 0), c(1, 7, 0), c(2, 7, 0)], cfg)
    assert not is_valid_meld([c(0, 7, 0), c(0, 7, 1)], cfg)


# ---------- Meld enumeration ----------

def test_valid_melds_finds_group_in_hand():
    cfg = RamiConfig()
    hand = [c(0, 7, 0), c(1, 7, 0), c(2, 7, 0), c(3, 5, 0)]
    melds = valid_melds(hand, cfg)
    assert any(len(m) == 3 and all(x.rank == 7 for x in m) for m in melds)


def test_valid_melds_finds_run_in_hand():
    cfg = RamiConfig()
    hand = [c(0, 5, 0), c(0, 6, 0), c(0, 7, 0), c(0, 8, 0), c(1, 2, 0)]
    melds = valid_melds(hand, cfg)
    runs = [m for m in melds if all(x.suit == 0 for x in m)]
    assert len(runs) >= 2  # 5-6-7 and 6-7-8 at least


def test_valid_melds_no_valid():
    cfg = RamiConfig()
    hand = [c(0, 2, 0), c(1, 5, 0), c(2, 9, 0), c(3, 12, 0)]
    melds = valid_melds(hand, cfg)
    assert melds == []


# ---------- Points & threshold ----------

def test_meld_points_group_of_kings():
    cfg = RamiConfig()
    meld = (c(0, 13, 0), c(1, 13, 0), c(2, 13, 0))
    assert meld_points(meld, cfg) == 30  # 3 × 10


def test_meld_points_run_with_ace_low():
    cfg = RamiConfig()
    meld = (c(0, 1, 0), c(0, 2, 0), c(0, 3, 0))
    assert meld_points(meld, cfg) == 6  # 1+2+3


def test_can_lay_first_no_threshold():
    cfg = RamiConfig(first_meld_threshold=0)
    assert can_lay_first([(c(0, 2, 0), c(1, 2, 0), c(2, 2, 0))], cfg)


def test_can_lay_first_meets_30_threshold():
    cfg = RamiConfig(first_meld_threshold=30)
    melds = [(c(0, 13, 0), c(1, 13, 0), c(2, 13, 0))]  # 30 pts
    assert can_lay_first(melds, cfg)


def test_can_lay_first_below_30_threshold():
    cfg = RamiConfig(first_meld_threshold=30)
    melds = [(c(0, 2, 0), c(1, 2, 0), c(2, 2, 0))]  # 6 pts
    assert not can_lay_first(melds, cfg)


# ---------- Laydowns ----------

def test_valid_laydowns_empty_hand():
    cfg = RamiConfig()
    assert valid_laydowns([], cfg, first_meld_done=True) == []


def test_valid_laydowns_single_meld():
    cfg = RamiConfig(first_meld_threshold=0)
    hand = [c(0, 7, 0), c(1, 7, 0), c(2, 7, 0), c(3, 5, 0)]
    lays = valid_laydowns(hand, cfg, first_meld_done=True)
    assert len(lays) >= 1
    assert any(len(lay) == 1 and len(lay[0]) == 3 for lay in lays)


def test_valid_laydowns_requires_threshold_first_time():
    cfg = RamiConfig(first_meld_threshold=30)
    hand = [c(0, 2, 0), c(1, 2, 0), c(2, 2, 0), c(3, 5, 0)]
    # 6 pts only, threshold is 30 → no valid laydown
    lays = valid_laydowns(hand, cfg, first_meld_done=False)
    assert lays == []


# ---------- Deadwood partition ----------

def test_deadwood_zero_when_all_melds():
    cfg = RamiConfig()
    hand = [c(0, 7, 0), c(1, 7, 0), c(2, 7, 0)]
    assert deadwood_score(hand, cfg) == 0


def test_deadwood_counts_remaining():
    cfg = RamiConfig()
    hand = [c(0, 7, 0), c(1, 7, 0), c(2, 7, 0), c(3, 13, 0)]
    # 3 kings... no, 1 king left as deadwood (10 pts)
    assert deadwood_score(hand, cfg) == 10


def test_deadwood_joker_penalty():
    cfg = RamiConfig(joker_penalty=25)
    hand = [c(-1, 0, 0)]  # just a joker
    assert deadwood_score(hand, cfg) == 25


# ---------- Game flow ----------

def test_new_game_deals_14_to_each_player():
    cfg = RamiConfig()
    g = new_game(cfg, seed=1)
    assert len(g.players[0].hand) == 14
    assert len(g.players[1].hand) == 14
    assert len(g.discard) == 1
    assert len(g.stock) == 108 - 28 - 1


def test_legal_moves_at_least_one():
    cfg = RamiConfig()
    g = new_game(cfg, seed=1)
    moves = legal_moves(g)
    assert len(moves) >= 1


def test_apply_move_draws_and_discards():
    cfg = RamiConfig()
    g = new_game(cfg, seed=1)
    moves = legal_moves(g)
    m = moves[0]
    stock_before = len(g.stock)
    apply_move(g, m)
    assert len(g.players[0].hand) == 14  # drew 1, discarded 1
    assert g.current == 1  # moved to opponent
    assert g.turn == 1


def test_full_game_runs_to_completion():
    """Sanity: a random game should terminate."""
    from rami.ai.discovery import DiscoveryAI
    cfg = RamiConfig()
    g = new_game(cfg, seed=7)
    ai = DiscoveryAI(seed=42)
    moves_made = 0
    while not g.terminal and moves_made < 2000:
        m = ai.decide(g)
        apply_move(g, m)
        moves_made += 1
    assert g.terminal, "game did not terminate"
