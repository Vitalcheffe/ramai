"""Tests for the croupier architecture: stream, voice, zones, sheet."""
import pytest
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from rami.zones import (
    ZoneName, ZoneBox, ZoneMap, DEFAULT_ZONE_LAYOUT,
    calibrate_zones_from_image, which_zone, cards_in_zone,
    slot_number_for_detection, draw_zones_overlay,
)
from rami.voice import Voice


# ===================== Zones =====================

class TestZones:
    """The 5 zones on the A4 sheet must be locatable and usable for
    filtering detections."""

    def test_all_5_zones_defined(self):
        """The default layout must have all 5 zones."""
        assert len(DEFAULT_ZONE_LAYOUT) == 5
        for name in ZoneName:
            assert name in DEFAULT_ZONE_LAYOUT

    def test_zone_box_contains_center(self):
        """A detection whose center is inside the zone should match."""
        box = ZoneBox(name=ZoneName.MONTRE, x1=100, y1=100, x2=300, y2=300)
        # Detection entirely inside
        assert box.contains((150, 150, 200, 200)) is True
        # Detection centered inside but extending outside
        assert box.contains((50, 50, 250, 250)) is True   # center is (150,150) inside
        # Detection entirely outside
        assert box.contains((500, 500, 600, 600)) is False

    def test_zone_map_which_classifies_correctly(self):
        """which_zone should return the correct zone for a bbox."""
        zones = {
            ZoneName.MONTRE:   ZoneBox(ZoneName.MONTRE, 100, 100, 300, 300),
            ZoneName.CENTRE:   ZoneBox(ZoneName.CENTRE, 100, 500, 600, 700),
        }
        zmap = ZoneMap(zones=zones)
        assert zmap.which((150, 150, 200, 200)) == ZoneName.MONTRE
        assert zmap.which((300, 550, 400, 600)) == ZoneName.CENTRE
        assert zmap.which((1000, 1000, 1100, 1100)) is None

    def test_calibration_from_image(self):
        """calibrate_zones_from_image should return a ZoneMap."""
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        zmap = calibrate_zones_from_image(img)
        assert zmap is not None
        for name in ZoneName:
            box = zmap.get(name)
            assert box is not None, f"zone {name} missing"
            assert box.x2 > box.x1
            assert box.y2 > box.y1

    def test_calibration_with_explicit_corners(self):
        """Calibrate with sheet corners that don't fill the image."""
        img = np.zeros((1000, 1000, 3), dtype=np.uint8)
        # Sheet occupies (100,100) to (900,900)
        corners = ((100, 100), (900, 100), (900, 900), (100, 900))
        zmap = calibrate_zones_from_image(img, sheet_corners=corners)
        assert zmap is not None
        montre = zmap.get(ZoneName.MONTRE)
        # MONTRE should be in the top-left, so x1 ≥ 100
        assert montre.x1 >= 100
        assert montre.y1 >= 100

    def test_slot_number_for_position(self):
        """ZONE_IA has 15 numbered slots (1-15, top-to-bottom, left-to-right).
        A detection in slot 2 (top-middle) should return 2."""
        # 3 rows × 5 cols, box is 500 wide × 300 tall starting at (100, 100)
        box = ZoneBox(name=ZoneName.ZONE_IA, x1=100, y1=100, x2=600, y2=400)
        zmap = ZoneMap(zones={ZoneName.ZONE_IA: box})
        # Top-left slot = position 1, center = (150, 150)
        slot = box.slot_for_position((140, 140, 160, 160))
        assert slot == 1
        # Top-second-from-left = position 2 (col=1, row=0)
        slot = box.slot_for_position((240, 140, 260, 160))
        assert slot == 2
        # Top-right = position 5 (col=4, row=0)
        slot = box.slot_for_position((540, 140, 560, 160))
        assert slot == 5
        # Second row, first col = position 6 (col=0, row=1)
        slot = box.slot_for_position((140, 240, 160, 260))
        assert slot == 6

    def test_draw_zones_overlay_returns_image(self):
        """draw_zones_overlay should return an image of the same shape."""
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        zmap = calibrate_zones_from_image(img)
        out = draw_zones_overlay(img, zmap)
        assert out.shape == img.shape

    def test_cards_in_zone_filters_correctly(self):
        """cards_in_zone should filter detections by zone."""

        class FakeDet:
            def __init__(self, bbox):
                self.bbox = bbox

        dets = [
            FakeDet((150, 150, 200, 200)),  # in MONTRE
            FakeDet((300, 550, 400, 600)),  # in CENTRE
            FakeDet((170, 170, 220, 220)),  # in MONTRE
        ]
        zones = {
            ZoneName.MONTRE: ZoneBox(ZoneName.MONTRE, 100, 100, 300, 300),
            ZoneName.CENTRE: ZoneBox(ZoneName.CENTRE, 100, 500, 600, 700),
        }
        zmap = ZoneMap(zones=zones)
        montre_cards = cards_in_zone(dets, ZoneName.MONTRE, zmap)
        assert len(montre_cards) == 2
        centre_cards = cards_in_zone(dets, ZoneName.CENTRE, zmap)
        assert len(centre_cards) == 1


# ===================== Voice =====================

class TestVoice:
    """The AI voice should speak French, print every phrase, and record
    the history for the report."""

    def test_voice_says_and_records(self):
        """say() should record the phrase in history."""
        v = Voice(use_browser=False, use_gtts=False, verbose=False)
        record = v.say("Test phrase", also_print=False)
        assert record["text"] == "Test phrase"
        assert record["success"] is False  # both methods disabled
        assert record["method"] == "none"
        assert len(v.history()) == 1

    def test_voice_history_accumulates(self):
        """Multiple say() calls should accumulate in history."""
        v = Voice(use_browser=False, use_gtts=False, verbose=False)
        v.say("Phrase 1", also_print=False)
        v.say("Phrase 2", also_print=False)
        v.say("Phrase 3", also_print=False)
        assert len(v.history()) == 3
        last = v.last_phrases(2)
        assert len(last) == 2
        assert last[-1]["text"] == "Phrase 3"

    def test_voice_records_timestamp(self):
        """Each record should have a timestamp."""
        v = Voice(use_browser=False, use_gtts=False, verbose=False)
        record = v.say("Timestamped", also_print=False)
        assert "timestamp" in record
        assert "datetime" in record
        assert record["timestamp"] > 0

    def test_voice_uses_french_lang(self):
        """Voice should default to fr-FR."""
        v = Voice()
        assert v.lang == "fr-FR"


# ===================== Sheet generation =====================

class TestSheetGeneration:
    """The printable A4 sheet must be generated as a PDF."""

    def test_sheet_pdf_generated(self):
        """make_sheet() should produce a PDF file."""
        from scripts.make_sheet import make_sheet
        path = make_sheet("/tmp/test_sheet.pdf")
        assert os.path.exists(path)
        size = os.path.getsize(path)
        assert size > 1000  # at least 1KB
        assert path.endswith(".pdf")

    def test_sheet_pdf_is_valid(self):
        """The PDF should be a valid PDF (starts with %PDF)."""
        from scripts.make_sheet import make_sheet
        path = make_sheet("/tmp/test_sheet2.pdf")
        with open(path, "rb") as f:
            header = f.read(4)
        assert header == b"%PDF"


# ===================== Stream module =====================

class TestStreamModule:
    """The stream module should expose start/stop/capture functions
    even when not running in Colab (returns 'unavailable' gracefully)."""

    def test_start_stream_returns_known_status(self):
        """start_stream() should return a known status, not raise."""
        from rami.vision.stream import start_stream, get_stream_status
        status = start_stream()
        assert status in ("streaming", "file_input", "unavailable")

    def test_get_latest_frame_returns_none_without_stream(self):
        """Without a running stream, get_latest_frame should return None."""
        from rami.vision.stream import get_latest_frame
        frame = get_latest_frame()
        # In CLI context, this is None
        assert frame is None

    def test_capture_photo_returns_none_without_stream(self):
        """capture_photo should return None if no stream is running."""
        from rami.vision.stream import capture_photo
        result = capture_photo()
        assert result is None

    def test_stop_stream_does_not_raise(self):
        """stop_stream should not raise even if nothing is running."""
        from rami.vision.stream import stop_stream
        stop_stream()  # should not raise
