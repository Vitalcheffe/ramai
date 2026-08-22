"""Test card, deck, hand primitives."""
import pytest
from rami.cards import Card, build_deck, Hand
from rami.config import RamiConfig


def test_card_equality():
    a = Card(suit=0, rank=1, copy_id=0)
    b = Card(suit=0, rank=1, copy_id=0)
    c = Card(suit=0, rank=1, copy_id=1)
    assert a == b
    assert a != c
    assert hash(a) == hash(b)


def test_card_name_joker():
    j = Card(suit=-1, rank=0, copy_id=0)
    assert j.is_joker
    assert j.name == "★"


def test_card_name_ace_spades():
    a = Card(suit=0, rank=1, copy_id=0)
    assert a.name == "A♠"


def test_deck_size_default_2_decks_with_jokers():
    cfg = RamiConfig()
    deck = build_deck(cfg)
    assert len(deck) == 108  # 2 × 54


def test_deck_size_no_jokers():
    cfg = RamiConfig.no_jokers()
    deck = build_deck(cfg)
    assert len(deck) == 104  # 2 × 52


def test_deck_size_1_deck():
    cfg = RamiConfig(num_decks=1, num_jokers_per_deck=2)
    deck = build_deck(cfg)
    assert len(deck) == 54


def test_deck_deterministic_with_seed():
    cfg = RamiConfig()
    d1 = build_deck(cfg, seed=42)
    d2 = build_deck(cfg, seed=42)
    assert d1 == d2
    d3 = build_deck(cfg, seed=43)
    assert d1 != d3


def test_hand_add_remove():
    h = Hand(cards=[Card(0, 1, 0)])
    h.add(Card(1, 2, 0))
    assert len(h) == 2
    h.remove(Card(0, 1, 0))
    assert len(h) == 1


def test_hand_remove_not_present():
    h = Hand(cards=[Card(0, 1, 0)])
    with pytest.raises(ValueError):
        h.remove(Card(2, 5, 0))


def test_hand_jokers_filter():
    h = Hand(cards=[Card(0, 1, 0), Card(-1, 0, 0), Card(2, 5, 0)])
    js = h.jokers()
    assert len(js) == 1


def test_hand_by_suit():
    h = Hand(cards=[Card(0, 1, 0), Card(0, 5, 0), Card(1, 2, 0)])
    by = h.by_suit()
    assert len(by[0]) == 2
    assert by[0][0].rank < by[0][1].rank


def test_card_ordering():
    cards = [Card(1, 5, 0), Card(0, 1, 0), Card(2, 10, 0)]
    s = sorted(cards)
    assert s[0].suit == 0
    assert s[1].suit == 1
