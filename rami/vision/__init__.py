"""Rami vision package — YOLO card detection (run in Colab, not in CLI).

This module is imported by the notebook. It gracefully degrades to a
mock detector when torch/ultralytics are not available (so the rest of
the notebook can be developed without GPU).
"""
from .detector import CardDetector, Detection, MockDetector

__all__ = ["CardDetector", "Detection", "MockDetector"]
