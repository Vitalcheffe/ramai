"""Test config presets and parametric rules."""
from rami.config import RamiConfig
from rami.cards import build_deck
from rami.engine import is_valid_meld, is_valid_run, is_valid_group
from rami.cards import Card


def c(s, r, copy=0):
    return Card(s, r, copy)


def test_classic_moroccan_defaults():
    cfg = RamiConfig.classic_moroccan()
    assert cfg.num_decks == 2
    assert cfg.num_jokers_per_deck == 2
    assert cfg.first_meld_threshold == 30
    assert cfg.hand_size == 14


def test_threshold_51_preset():
    cfg = RamiConfig.threshold_51()
    assert cfg.first_meld_threshold == 51


def test_no_threshold_preset():
    cfg = RamiConfig.no_threshold()
    assert cfg.first_meld_threshold == 0


def test_no_jokers_preset():
    cfg = RamiConfig.no_jokers()
    assert cfg.num_jokers_per_deck == 0
    deck = build_deck(cfg)
    assert len(deck) == 104


def test_total_cards_derived():
    cfg = RamiConfig()
    assert cfg.total_cards == 108


def test_card_value_ace_low():
    cfg = RamiConfig(ace_low_value=1)
    assert cfg.card_value(1) == 1


def test_card_value_face_cards():
    cfg = RamiConfig()
    assert cfg.card_value(11) == 10  # J
    assert cfg.card_value(12) == 10  # Q
    assert cfg.card_value(13) == 10  # K


def test_card_value_number_cards():
    cfg = RamiConfig()
    assert cfg.card_value(5) == 5
    assert cfg.card_value(10) == 10


def test_aces_low_high_both_off():
    cfg = RamiConfig(aces_low=False, aces_high=False)
    # No valid run including an ace
    cards = [c(0, 1, 0), c(0, 2, 0), c(0, 3, 0)]
    assert not is_valid_run(cards, cfg)


def test_aces_low_only():
    cfg = RamiConfig(aces_low=True, aces_high=False)
    assert is_valid_run([c(0, 1, 0), c(0, 2, 0), c(0, 3, 0)], cfg)
    assert not is_valid_run([c(0, 12, 0), c(0, 13, 0), c(0, 1, 0)], cfg)


def test_aces_high_only():
    cfg = RamiConfig(aces_low=False, aces_high=True)
    assert not is_valid_run([c(0, 1, 0), c(0, 2, 0), c(0, 3, 0)], cfg)
    assert is_valid_run([c(0, 12, 0), c(0, 13, 0), c(0, 1, 0)], cfg)


def test_min_meld_size_4_strict():
    cfg = RamiConfig(min_meld_size=4)
    assert not is_valid_group([c(0, 5, 0), c(1, 5, 0), c(2, 5, 0)], cfg)
    assert is_valid_group([c(0, 5, 0), c(1, 5, 0), c(2, 5, 0), c(3, 5, 0)], cfg)


def test_joker_per_meld_limit():
    cfg = RamiConfig(max_jokers_per_meld=0)
    cards = [c(0, 5, 0), c(0, 6, 0), Card(-1, 0, 0)]
    assert not is_valid_run(cards, cfg)


def test_num_players_configurable():
    cfg = RamiConfig(num_players=3)
    assert cfg.num_players == 3
