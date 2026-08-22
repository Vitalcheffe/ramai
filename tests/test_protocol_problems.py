"""Tests for the 7 problems identified in the protocol simulation.

P1: Rami 51 — cannot take from discard until threshold met
P2: Meld extensions — extend opponent's 5-6-7♥ with 4♥
P3: Joker designation — say explicitly what card the joker represents
P4: Card counting — deduce opponent's hand size by arithmetic
P5: Protocol — discard photo mandatory at end of turn
P6: Camera calibration — green frame when angle OK
P7: Discard detection — refuse if not exactly 1 card
"""
import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rami.config import RamiConfig
from rami.cards import Card, build_deck, Hand
from rami.game import new_game, legal_moves, apply_move, Move
from rami.engine import is_valid_meld, valid_melds
from rami.extensions import (
    designate_jokers, find_meld_extensions, all_laid_melds,
    JokerDesignation,
)
from rami.counting import CardCountingState
from rami.protocol import (
    ProtocolStep, TurnContext, next_step, should_show_ai_hand,
)
from rami.ai.discovery import DiscoveryAI


def c(suit, rank, copy=0):
    return Card(suit, rank, copy)


JOKER = lambda copy=0: Card(suit=-1, rank=0, copy_id=copy)


# ===================== P1: Rami 51 =====================

class TestRami51:
    """At Rami 51, you cannot take from the discard pile until your
    first meld has been laid (which meets the 51-point threshold)."""

    def test_rami_51_config_has_block_discard_rule(self):
        cfg = RamiConfig.threshold_51()
        assert cfg.first_meld_threshold == 51
        assert cfg.block_discard_before_threshold is True

    def test_classic_moroccan_does_not_block_discard(self):
        cfg = RamiConfig.classic_moroccan()
        assert cfg.block_discard_before_threshold is False

    def test_legal_moves_excludes_discard_before_first_meld_at_51(self):
        """At Rami 51, before first meld, AI cannot draw from discard."""
        cfg = RamiConfig.threshold_51()
        g = new_game(cfg, seed=1)
        # Force a top discard that would normally be drawable
        g.discard = [c(0, 13, 0)]
        moves = legal_moves(g)
        # No move should draw from discard (player hasn't laid first meld)
        sources = {m.draw_source for m in moves}
        assert "discard" not in sources
        assert "stock" in sources

    def test_legal_moves_allows_discard_after_first_meld(self):
        """Once first meld is laid, discard becomes available."""
        cfg = RamiConfig.threshold_51()
        g = new_game(cfg, seed=1)
        g.discard = [c(0, 13, 0)]
        # Mark player as having laid first meld
        g.current_player.has_laid_first = True
        moves = legal_moves(g)
        sources = {m.draw_source for m in moves}
        assert "discard" in sources


# ===================== P2: Meld extensions =====================

class TestMeldExtensions:
    """A player can extend an existing laid meld by adding a card to it
    (e.g. 4♥ onto opponent's 5♥-6♥-7♥ run), but only if they've passed
    their own first-meld threshold."""

    def test_find_extension_for_run_low(self):
        """4♥ extends 5♥-6♥-7♥."""
        cfg = RamiConfig(allow_meld_extensions=True)
        existing_melds = [(0, 0, (c(1, 5, 0), c(1, 6, 0), c(1, 7, 0)))]
        card = c(1, 4, 0)
        exts = find_meld_extensions(card, existing_melds, cfg)
        assert len(exts) == 1
        assert exts[0].extends_at == "start"

    def test_find_extension_for_run_high(self):
        """8♥ extends 5♥-6♥-7♥."""
        cfg = RamiConfig(allow_meld_extensions=True)
        existing_melds = [(0, 0, (c(1, 5, 0), c(1, 6, 0), c(1, 7, 0)))]
        card = c(1, 8, 0)
        exts = find_meld_extensions(card, existing_melds, cfg)
        assert len(exts) == 1
        assert exts[0].extends_at == "end"

    def test_no_extension_for_unrelated_card(self):
        """4♠ does NOT extend 5♥-6♥-7♥."""
        cfg = RamiConfig(allow_meld_extensions=True)
        existing_melds = [(0, 0, (c(1, 5, 0), c(1, 6, 0), c(1, 7, 0)))]
        card = c(0, 4, 0)  # 4♠
        exts = find_meld_extensions(card, existing_melds, cfg)
        assert exts == []

    def test_extension_for_group_different_suit(self):
        """7♦ extends 7♠-7♥-7♣."""
        cfg = RamiConfig(allow_meld_extensions=True)
        existing_melds = [(0, 0, (c(0, 7, 0), c(1, 7, 0), c(2, 7, 0)))]
        card = c(3, 7, 0)  # 7♦
        exts = find_meld_extensions(card, existing_melds, cfg)
        assert len(exts) == 1

    def test_no_extension_when_duplicate_suit_strict(self):
        """7♠ does NOT extend 7♠-7♥-7♣ (duplicate suit)."""
        cfg = RamiConfig(allow_duplicate_suits_in_groups=False)
        existing_melds = [(0, 0, (c(0, 7, 0), c(1, 7, 0), c(2, 7, 0)))]
        card = c(0, 7, 1)  # another 7♠
        exts = find_meld_extensions(card, existing_melds, cfg)
        assert exts == []

    def test_extensions_disabled_by_config(self):
        cfg = RamiConfig(allow_meld_extensions=False)
        existing_melds = [(0, 0, (c(1, 5, 0), c(1, 6, 0), c(1, 7, 0)))]
        card = c(1, 4, 0)
        exts = find_meld_extensions(card, existing_melds, cfg)
        assert exts == []


# ===================== P3: Joker designation =====================

class TestJokerDesignation:
    """When a joker is used in a meld, the rules require declaring what
    card it represents. We compute that automatically."""

    def test_joker_in_run_middle(self):
        """In [5♥, ★, 7♥], the joker represents 6♥."""
        cfg = RamiConfig()
        meld = (c(1, 5, 0), JOKER(0), c(1, 7, 0))
        desigs = designate_jokers(meld, cfg)
        assert len(desigs) == 1
        assert desigs[0].represented_rank == 6
        assert desigs[0].represented_suit == 1  # ♥

    def test_joker_at_run_start(self):
        """In [★, 5♥, 6♥, 7♥], the joker represents 4♥."""
        cfg = RamiConfig()
        meld = (JOKER(0), c(1, 5, 0), c(1, 6, 0), c(1, 7, 0))
        desigs = designate_jokers(meld, cfg)
        assert desigs[0].represented_rank == 4
        assert desigs[0].represented_suit == 1

    def test_joker_at_run_end(self):
        """In [5♥, 6♥, 7♥, ★], the joker represents 8♥."""
        cfg = RamiConfig()
        meld = (c(1, 5, 0), c(1, 6, 0), c(1, 7, 0), JOKER(0))
        desigs = designate_jokers(meld, cfg)
        assert desigs[0].represented_rank == 8
        assert desigs[0].represented_suit == 1

    def test_joker_in_group(self):
        """In [7♠, 7♥, ★], the joker represents 7♦ (or 7♣)."""
        cfg = RamiConfig()
        meld = (c(0, 7, 0), c(1, 7, 0), JOKER(0))
        desigs = designate_jokers(meld, cfg)
        assert desigs[0].represented_rank == 7
        # Should pick the first available suit (♦ = 2 if ♠,♥ used)
        assert desigs[0].represented_suit == 2

    def test_two_jokers_in_group(self):
        """In [7♠, ★, ★], jokers represent 7♥ and 7♦ (in order)."""
        cfg = RamiConfig()
        meld = (c(0, 7, 0), JOKER(0), JOKER(1))
        desigs = designate_jokers(meld, cfg)
        assert len(desigs) == 2
        assert all(d.represented_rank == 7 for d in desigs)
        # First available suit after ♠(0): ♥(1) and ♦(2)
        suits = [d.represented_suit for d in desigs]
        assert 1 in suits and 2 in suits

    def test_no_jokers_no_designations(self):
        cfg = RamiConfig()
        meld = (c(1, 5, 0), c(1, 6, 0), c(1, 7, 0))
        assert designate_jokers(meld, cfg) == []

    def test_designation_name_human_readable(self):
        """The designation should produce a human-readable name like
        '★ → 6♥' so the player knows what card the joker represents."""
        cfg = RamiConfig()
        meld = (c(1, 5, 0), JOKER(0), c(1, 7, 0))
        desigs = designate_jokers(meld, cfg)
        name = desigs[0].name
        assert "6" in name
        assert "♥" in name


# ===================== P4: Card counting =====================

class TestCardCounting:
    """The AI tracks the opponent's hand size by arithmetic — even though
    it never sees the opponent's hand."""

    def test_initial_hand_count(self):
        """At game start, every player has cfg.hand_size cards."""
        cfg = RamiConfig()
        g = new_game(cfg, seed=1)
        counting = CardCountingState.fresh(cfg, ai_player_idx=0,
                                            ai_hand=g.players[0].hand.cards)
        for p in range(cfg.num_players):
            assert counting.hand_count(p) == cfg.hand_size

    def test_opponent_empty_after_all_cards_laid_or_discarded(self):
        """If opponent has drawn N cards and laid+discarded N cards,
        hand count should be 0."""
        cfg = RamiConfig(first_meld_threshold=0)
        g = new_game(cfg, seed=1)
        counting = CardCountingState.fresh(cfg, ai_player_idx=0,
                                            ai_hand=g.players[0].hand.cards)
        # Opponent draws 1, discards 1, repeat 14 times
        for _ in range(14):
            counting.record_draw(1, "stock", None, ai_player_idx=0)
            counting.record_discard(1, c(0, 5, 0))
        # Plus they laid their 14 initial cards as melds
        for _ in range(14):
            counting.record_meld(1, (c(0, 1, 0),))
        assert counting.hand_count(1) == 0
        assert counting.is_opponent_empty(1) is True

    def test_unseen_cards_excludes_visible(self):
        """Unseen set = full deck - visible."""
        cfg = RamiConfig()
        g = new_game(cfg, seed=1)
        counting = CardCountingState.fresh(cfg, ai_player_idx=0,
                                            ai_hand=g.players[0].hand.cards)
        unseen = counting.unseen_cards(cfg)
        # Should be 108 - 14 (my hand) = 94
        assert len(unseen) == 108 - 14

    def test_arithmetic_consistency(self):
        """hand_count(opponent) should equal unseen - stock_size when
        the initial discard is correctly tracked."""
        cfg = RamiConfig()
        g = new_game(cfg, seed=1)
        counting = CardCountingState.fresh(cfg, ai_player_idx=0,
                                            ai_hand=g.players[0].hand.cards,
                                            initial_discard=g.discard)
        # Opponent draws 5 from stock (cards not visible to AI)
        for _ in range(5):
            counting.record_draw(1, "stock", None, ai_player_idx=0)
        # Opponent discards 3 DIFFERENT cards (visible)
        for card in [c(0, 5, 0), c(1, 9, 0), c(2, 11, 0)]:
            counting.record_discard(1, card)
        # Opponent lays 2 cards as meld (visible)
        counting.record_meld(1, (c(0, 7, 0), c(1, 7, 0)))
        # Initial stock = 108 - 28 (dealt) - 1 (initial discard) = 79
        # After opp draws 5 = 74
        estimate = counting.opponent_hand_estimate(cfg, opponent_idx=1,
                                                    stock_size=74)
        # hand = 14 + 5 - 3 - 2 = 14
        assert estimate["hand_count"] == 14
        # visible = 14 (my hand) + 1 (initial discard) + 3 (opp discards, all unique) + 2 (opp melds) = 20
        # unseen = 108 - 20 = 88
        # stock = 74
        # opp_hidden = 88 - 74 = 14 ✓ matches arithmetic
        assert estimate["opponent_hidden_estimate"] == 14
        assert estimate["arithmetic_consistent"] is True


# ===================== P5: Protocol — discard photo mandatory =====================

class TestProtocolMandatoryDiscardPhoto:
    """The protocol refuses to advance until the discard photo is taken."""

    def _setup_ctx(self):
        cfg = RamiConfig()
        g = new_game(cfg, seed=1)
        counting = CardCountingState.fresh(cfg, ai_player_idx=1,
                                            ai_hand=g.players[1].hand.cards)
        ctx = TurnContext(cfg=cfg, state=g, counting=counting, ai_player_idx=1)
        return ctx

    def test_discard_photo_step_blocks_without_photo(self):
        """If we're at PHOTO_DISCARD_AFTER_HUMAN and photo_taken is False,
        the next_step should return the SAME step with a warning."""
        ctx = self._setup_ctx()
        ctx.current_step = ProtocolStep.PHOTO_DISCARD_AFTER_HUMAN
        ctx.photo_taken = False
        prompt = next_step(ctx, last_input_ok=True)
        assert prompt.step == ProtocolStep.PHOTO_DISCARD_AFTER_HUMAN
        assert "OBLIGATOIRE" in prompt.warning or "OBLIGATOIRE" in prompt.message

    def test_discard_photo_step_advances_with_photo(self):
        """If photo_taken is True, the step advances to CHECK_END_OF_GAME."""
        ctx = self._setup_ctx()
        ctx.current_step = ProtocolStep.PHOTO_DISCARD_AFTER_HUMAN
        ctx.photo_taken = True
        prompt = next_step(ctx, last_input_ok=True)
        assert prompt.step == ProtocolStep.CHECK_END_OF_GAME

    def test_ai_discard_photo_step_blocks_without_photo(self):
        """Same for AI's discard — mandatory photo."""
        ctx = self._setup_ctx()
        ctx.current_step = ProtocolStep.PHOTO_AI_DISCARD
        ctx.photo_taken = False
        prompt = next_step(ctx, last_input_ok=True)
        assert prompt.step == ProtocolStep.PHOTO_AI_DISCARD
        assert prompt.warning is not None

    def test_failed_input_loops_back(self):
        """If last_input_ok is False, the same step is repeated with a warning."""
        ctx = self._setup_ctx()
        ctx.current_step = ProtocolStep.PHOTO_DISCARD_AFTER_HUMAN
        ctx.photo_taken = False
        prompt = next_step(ctx, last_input_ok=False)
        assert prompt.step == ProtocolStep.PHOTO_DISCARD_AFTER_HUMAN
        assert "Réessaie" in prompt.warning


# ===================== P5b: AI hand visibility =====================

class TestAIHandVisibility:
    """Discovery shows AI's hand (pedagogical). Strategy/Champion hide it.
    A 'triche' button lets the user reveal it with a warning."""

    def test_discovery_shows_hand(self):
        assert should_show_ai_hand("discovery") is True

    def test_strategy_hides_hand(self):
        assert should_show_ai_hand("strategy") is False

    def test_champion_hides_hand(self):
        assert should_show_ai_hand("champion") is False

    def test_triche_warning_explicit(self):
        from rami.protocol import show_ai_hand_warning
        w = show_ai_hand_warning()
        assert "triche" in w.lower()


# ===================== P6: Camera calibration =====================

class TestCalibration:
    """The camera calibration produces a green frame when the angle is
    acceptable (~30°) and a red frame when it's too skewed."""

    def test_empty_image_fails(self):
        from rami.vision import calibrate_camera
        result = calibrate_camera(None)
        assert result.is_good is False

    def test_tiny_image_fails(self):
        import numpy as np
        from rami.vision import calibrate_camera
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        result = calibrate_camera(img)
        assert result.is_good is False
        assert "trop petite" in result.message.lower()

    def test_normal_image_without_corners_passes(self):
        import numpy as np
        from rami.vision import calibrate_camera
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        result = calibrate_camera(img, table_corners=None)
        assert result.is_good is True

    def test_skewed_corners_fail(self):
        """If the perspective transform is degenerate, calibration fails."""
        import numpy as np
        from rami.vision import calibrate_camera
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        # Collinear corners → degenerate transform
        bad_corners = ((0, 0), (100, 0), (200, 0), (300, 0))
        result = calibrate_camera(img, table_corners=bad_corners)
        # Should fail because corners are collinear
        assert result.is_good is False


# ===================== P7: Discard detection =====================

class TestDiscardDetection:
    """The discard pile must show exactly ONE card. If 0 or 2+ cards
    are detected, the system refuses to advance."""

    def _make_mock_detector(self, n_cards: int, confidence: float = 0.9):
        from rami.vision import MockDetector, Detection
        class FakeDetector(MockDetector):
            def predict(self, image):
                return [Detection(rank="7", suit="♥",
                                   confidence=confidence,
                                   bbox=(10, 10, 100, 140))
                        for _ in range(n_cards)]
        return FakeDetector()

    def test_exactly_one_card_passes(self):
        from rami.vision import detect_discard_pile
        import numpy as np
        img = np.zeros((200, 200, 3), dtype=np.uint8)
        det = self._make_mock_detector(n_cards=1, confidence=0.9)
        result = detect_discard_pile(det, img)
        assert result.is_reliable is True
        assert result.card_rank == "7"
        assert result.card_suit == "♥"

    def test_zero_cards_fails(self):
        from rami.vision import detect_discard_pile
        import numpy as np
        img = np.zeros((200, 200, 3), dtype=np.uint8)
        det = self._make_mock_detector(n_cards=0)
        result = detect_discard_pile(det, img)
        assert result.is_reliable is False
        assert "Aucune carte" in result.message

    def test_multiple_cards_fails(self):
        from rami.vision import detect_discard_pile
        import numpy as np
        img = np.zeros((200, 200, 3), dtype=np.uint8)
        det = self._make_mock_detector(n_cards=2)
        result = detect_discard_pile(det, img)
        assert result.is_reliable is False
        assert "2 cartes" in result.message or "UNE" in result.message

    def test_low_confidence_fails(self):
        from rami.vision import detect_discard_pile
        import numpy as np
        img = np.zeros((200, 200, 3), dtype=np.uint8)
        det = self._make_mock_detector(n_cards=1, confidence=0.5)
        result = detect_discard_pile(det, img)
        assert result.is_reliable is False
        assert "confiance faible" in result.message.lower()


# ===================== P7b: Meld cluster detection =====================

class TestMeldClusters:
    """When the AI looks at the table, it groups spatially close cards
    into clusters that represent melds."""

    def test_no_cards_returns_empty(self):
        from rami.vision import detect_meld_clusters, MockDetector
        import numpy as np
        img = np.zeros((200, 200, 3), dtype=np.uint8)
        clusters = detect_meld_clusters(MockDetector(), img)
        assert clusters == []

    def test_cards_grouped_by_proximity(self):
        from rami.vision import detect_meld_clusters, Detection
        import numpy as np
        class FakeDetector(MockDetector if False else object):
            def predict(self, image):
                # 3 cards close together (a meld) + 1 far away
                return [
                    Detection("5", "♥", 0.9, (10, 10, 50, 80)),
                    Detection("6", "♥", 0.9, (55, 10, 95, 80)),    # close to 5♥
                    Detection("7", "♥", 0.9, (100, 10, 140, 80)),  # close to 6♥
                    Detection("K", "♠", 0.9, (300, 300, 340, 370)), # far
                ]
        from rami.vision import MockDetector as MD
        class FakeDet(MD):
            def predict(self, image):
                return [
                    Detection("5", "♥", 0.9, (10, 10, 50, 80)),
                    Detection("6", "♥", 0.9, (55, 10, 95, 80)),
                    Detection("7", "♥", 0.9, (100, 10, 140, 80)),
                    Detection("K", "♠", 0.9, (300, 300, 340, 370)),
                ]
        img = np.zeros((400, 400, 3), dtype=np.uint8)
        clusters = detect_meld_clusters(FakeDet(), img)
        # Should find 2 clusters: {5♥,6♥,7♥} and {K♠}
        assert len(clusters) == 2
        # Find the bigger cluster
        big = max(clusters, key=lambda c: len(c.cards))
        assert len(big.cards) == 3

    def test_find_extendable_melds(self):
        from rami.vision import MeldCluster, find_extendable_melds
        clusters = [
            MeldCluster(cards=[("5", "♥"), ("6", "♥"), ("7", "♥")],
                        centroid=(0, 0), bbox=(0, 0, 0, 0)),
            MeldCluster(cards=[("K", "♠")],
                        centroid=(0, 0), bbox=(0, 0, 0, 0)),
        ]
        # 4♥ should extend the 5-6-7♥ cluster
        exts = find_extendable_melds(clusters, ("4", "♥"))
        assert len(exts) == 1
        assert exts[0] == 0
        # 8♥ should also extend it
        exts = find_extendable_melds(clusters, ("8", "♥"))
        assert len(exts) == 1
        # K♣ should extend the K♠ group
        exts = find_extendable_melds(clusters, ("K", "♣"))
        assert len(exts) == 1
        # 2♦ should not extend anything
        exts = find_extendable_melds(clusters, ("2", "♦"))
        assert exts == []
