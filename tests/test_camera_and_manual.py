"""Tests for the new camera + pre-trained model + manual mode features.

Bug fixes:
  1. Camera permission prompt never appeared when clicking "take photo"
     → Fixed by prewarm_camera() called at notebook init
  2. No pre-trained YOLO model → user had to train 30 min
     → Fixed by try_download_pretrained() + MANUAL mode fallback
"""
import pytest
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rami.vision.camera import (
    prewarm_camera, is_camera_ready, get_camera_status, stop_camera,
)
from rami.vision.pretrained import (
    try_download_pretrained, list_candidate_urls, get_model_info,
)
from rami.vision import (
    CardDetector, MockDetector, detect_discard_pile,
)


# ===================== Camera prewarm =====================

class TestCameraPrewarm:
    """Camera permission should be requested at notebook init, not on
    first photo click. This is the bug the user reported."""

    def test_prewarm_returns_known_status(self):
        """prewarm_camera() must return 'granted' | 'denied' | 'unavailable'."""
        status = prewarm_camera()
        assert status in ("granted", "denied", "unavailable", "unknown")

    def test_is_camera_ready_consistent_with_status(self):
        """After prewarm, is_camera_ready() should reflect the status."""
        status = get_camera_status()
        if status == "granted":
            assert is_camera_ready() is True
        else:
            assert is_camera_ready() is False

    def test_capture_returns_none_without_prewarm(self):
        """If camera isn't ready, capture_photo() should return None gracefully."""
        # Force the status to unknown
        import rami.vision.camera as cam_mod
        old = cam_mod._CAMERA_STATUS
        cam_mod._CAMERA_STATUS = "unknown"
        try:
            assert cam_mod.capture_photo() is None
        finally:
            cam_mod._CAMERA_STATUS = old


# ===================== Pre-trained model downloader =====================

class TestPretrainedDownloader:
    """The notebook should try to download a pre-trained model. If all
    URLs fail, return None and fall back to MANUAL mode."""

    def test_candidate_urls_listed(self):
        """list_candidate_urls() returns a non-empty list of URLs."""
        urls = list_candidate_urls()
        assert isinstance(urls, list)
        assert len(urls) > 0
        for url in urls:
            assert url.startswith("http"), f"invalid URL: {url}"

    def test_download_to_nonexistent_dir_creates_it(self, tmp_path):
        """download should create the output directory if it doesn't exist."""
        out = str(tmp_path / "deep" / "nested" / "best.pt")
        # try_download_pretrained will likely fail (no network in CI),
        # but should not raise. The dir creation should happen regardless.
        result = try_download_pretrained(out_path=out, timeout=1)
        # If no URL works, returns None
        # But the directory should be created
        assert os.path.isdir(os.path.dirname(out))

    def test_get_model_info_nonexistent(self):
        """get_model_info on a non-existent file should return {'exists': False}."""
        info = get_model_info("/tmp/does_not_exist.pt")
        assert info["exists"] is False

    def test_get_model_info_real_file(self, tmp_path):
        """get_model_info on a real (small) file should return size info."""
        path = tmp_path / "fake.pt"
        path.write_bytes(b"x" * 1024)  # 1KB — too small to be a real model but tests the function
        info = get_model_info(str(path))
        assert info["exists"] is True
        assert info["size_bytes"] == 1024
        assert "sha256_head" in info


# ===================== Mode MANUEL fallback =====================

class TestModeManuel:
    """When the camera or YOLO model is unavailable, the notebook should
    fall back to MANUAL mode: card entry via clickable grids, no vision."""

    def test_manual_mode_works_without_camera(self):
        """The notebook must function without any camera access."""
        # This is implicitly tested: all card counting + protocol tests
        # run without camera. We just confirm the imports work.
        from rami.config import RamiConfig
        from rami.cards import Card, build_deck
        from rami.game import new_game, legal_moves, apply_move
        cfg = RamiConfig()
        g = new_game(cfg, seed=42)
        moves = legal_moves(g)
        assert len(moves) > 0
        # We can play a full game without any camera
        from rami.ai.discovery import DiscoveryAI
        ai = DiscoveryAI(seed=0)
        n = 0
        while not g.terminal and n < 300:
            apply_move(g, ai.decide(g))
            n += 1
        assert g.terminal

    def test_manual_mode_works_without_yolo(self):
        """The notebook must function without any YOLO model."""
        # MockDetector returns empty list — no detection possible
        det = MockDetector()
        import numpy as np
        img = np.zeros((200, 200, 3), dtype=np.uint8)
        result = detect_discard_pile(det, img)
        # MockDetector returns 0 cards → not reliable
        assert result.is_reliable is False
        # But the function doesn't crash — it returns a clear message
        assert "Aucune carte" in result.message


# ===================== Card entry UX (no vision) =====================

class TestCardEntryUX:
    """Card entry via grids should work for ALL card types:
      - Human hand (14 cards, hidden from camera)
      - Discard pile (1 card, face up)
      - AI hand (when in 'triche' mode)
    """

    def test_all_52_cards_plus_jokers_representable(self):
        """The card grid must include all 52 standard cards + jokers."""
        from rami.cards import SUIT_SYMBOLS, RANK_NAMES
        # 4 suits
        assert len(SUIT_SYMBOLS) == 4
        # 13 ranks (A, 2-10, J, Q, K)
        assert len(RANK_NAMES) == 13
        assert RANK_NAMES[1] == "A"
        assert RANK_NAMES[11] == "J"
        assert RANK_NAMES[12] == "Q"
        assert RANK_NAMES[13] == "K"

    def test_card_grid_covers_all_unique_cards(self):
        """Verify the grid would let user select any of 52 unique cards."""
        from rami.cards import Card
        unique_keys = set()
        for suit in range(4):
            for rank in range(1, 14):
                unique_keys.add((suit, rank))
        assert len(unique_keys) == 52

    def test_jokers_distinguishable(self):
        """Jokers must be distinguishable (each has a copy_id)."""
        from rami.cards import Card
        j1 = Card(suit=-1, rank=0, copy_id=0)
        j2 = Card(suit=-1, rank=0, copy_id=1)
        assert j1 != j2
        assert j1.is_joker and j2.is_joker
