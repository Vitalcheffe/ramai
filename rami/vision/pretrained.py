"""Pre-trained YOLO model downloader.

Downloads from the project's own GitHub release. This URL is permanent
and reliable (unlike ad-hoc HuggingFace/Roboflow mirrors).

Release URL:
  https://github.com/VitalCheffe/ramai/releases/download/v0.1.0-vision-bootstrap/yolov8n.pt

This is the YOLOv8n COCO-pretrained backbone. To get a CARDS-specific
model, the user runs notebooks/train_yolo.ipynb in Colab (30 min on
free GPU), then uploads the resulting best.pt to a new release
v0.2.0-cards and updates DOWNLOAD_URL below.
"""
from __future__ import annotations
import os
import urllib.request
from typing import Optional
import hashlib


# Permanent URL — the project's own GitHub release
DOWNLOAD_URL = "https://github.com/VitalCheffe/ramai/releases/download/v0.1.0-vision-bootstrap/yolov8n.pt"
EXPECTED_SIZE = 6_534_387  # bytes


def try_download_pretrained(out_path: str = "models/yolov8n.pt",
                              timeout: int = 30) -> Optional[str]:
    """Download the YOLO model from the project's GitHub release.

    Returns the path to the downloaded model if successful, None otherwise.
    The caller should fall back to MANUAL mode if None is returned.
    """
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)

    # If file already exists and has the right size, skip download
    if os.path.exists(out_path):
        size = os.path.getsize(out_path)
        if size == EXPECTED_SIZE or size > 1_000_000:
            return out_path

    try:
        req = urllib.request.Request(DOWNLOAD_URL,
                                      headers={"User-Agent": "ramai/0.1"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status != 200:
                return None
            data = resp.read()
            if len(data) < 1_000_000:
                return None
            with open(out_path, "wb") as f:
                f.write(data)
            return out_path
    except Exception:
        return None


def get_model_info(path: str) -> dict:
    """Return basic info about a downloaded model file."""
    if not os.path.exists(path):
        return {"exists": False}
    size = os.path.getsize(path)
    with open(path, "rb") as f:
        head = f.read(4096)
    return {
        "exists": True,
        "size_bytes": size,
        "size_mb": round(size / (1024 * 1024), 2),
        "sha256_head": hashlib.sha256(head).hexdigest()[:16],
        "path": path,
    }


def get_download_url() -> str:
    """Return the canonical download URL."""
    return DOWNLOAD_URL
