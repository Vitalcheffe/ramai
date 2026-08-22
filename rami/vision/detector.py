"""YOLOv8 card detector wrapper. Imports torch lazily.

Usage in Colab (after training):
    from rami.vision import CardDetector
    det = CardDetector(weights_path="models/yolo_cards.pt")
    detections = det.predict(image_array)
    for d in detections:
        print(d.rank, d.suit, d.confidence)

In CLI (no torch installed): falls back to MockDetector so the rest of
the notebook can still be exercised.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Tuple
import os


@dataclass
class Detection:
    rank: str          # "A", "2".."10", "J", "Q", "K", or "Joker"
    suit: str          # "♠","♥","♦","♣", or "★" for joker
    confidence: float
    bbox: Tuple[float, float, float, float]  # (x1,y1,x2,y2) in pixels


class CardDetector:
    """Real YOLOv8 detector. Requires torch + ultralytics installed."""

    def __init__(self, weights_path: str = "models/yolo_cards.pt",
                 conf_threshold: float = 0.4):
        try:
            from ultralytics import YOLO
        except ImportError as e:
            raise ImportError(
                "ultralytics not installed. Run in Colab or "
                "`pip install ultralytics` to enable real detection."
            ) from e
        if not os.path.exists(weights_path):
            raise FileNotFoundError(
                f"weights not found: {weights_path}. Train with scripts/train_yolo.py"
            )
        self.model = YOLO(weights_path)
        self.conf_threshold = conf_threshold
        # YOLO class names — produced during training. They follow the
        # pattern "{rank}{suit}" e.g. "A♠", "2♥", "Joker". We re-derive
        # them from model.names which ultralytics populates from data.yaml.
        self.names = self.model.names

    def predict(self, image_array) -> List[Detection]:
        results = self.model(image_array, conf=self.conf_threshold, verbose=False)
        out: List[Detection] = []
        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                xyxy = box.xyxy[0].tolist()
                name = self.names[cls_id]
                rank, suit = _parse_class_name(name)
                out.append(Detection(rank=rank, suit=suit, confidence=conf,
                                     bbox=tuple(xyxy)))
        return out


class MockDetector:
    """Deterministic mock used when torch is unavailable. Returns empty list."""

    def __init__(self, *args, **kwargs):
        pass

    def predict(self, image_array) -> List[Detection]:
        return []


def _parse_class_name(name: str) -> Tuple[str, str]:
    """Convert YOLO class name to (rank, suit)."""
    if name.lower().startswith("joker"):
        return ("Joker", "★")
    # Names look like "A♠", "10♥", "2♦", "K♣"
    if name[0].isdigit() and len(name) > 1 and name[1].isdigit():
        return (name[:2], name[2:])
    return (name[0], name[1:])
