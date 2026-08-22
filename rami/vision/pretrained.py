"""Pre-trained YOLO model downloader.

Tries to download a pre-trained YOLOv8 model for playing cards from
several public mirrors. If all downloads fail (offline, 404, etc.),
returns None — caller should fall back to MANUAL mode (no vision).

We do NOT ship a model in the repo (would be too large). We try a list
of known public URLs, in order. The first one that succeeds wins.

Known public mirrors (as of 2026):
  1. Roboflow Universe public weights (no API key needed for some projects)
  2. Hugging Face Hub (specific spaces)
  3. GitHub releases of well-known cards-yolo repos

Each URL is tried with a short timeout (5s). If it returns a 200 with
content > 1MB, we save it to `out_path` and return the path.
"""
from __future__ import annotations
import os
import urllib.request
from typing import List, Optional
import hashlib


# Candidate URLs for pre-trained YOLOv8 playing-cards models.
# Order matters: we try them in sequence.
CANDIDATE_URLS: List[str] = [
    # 1. HuggingFace — public cards detector spaces (most reliable)
    "https://huggingface.co/spaces/playing-cards/yolov8-cards/resolve/main/best.pt",
    "https://huggingface.co/playing-cards-yolo/best/resolve/main/best.pt",
    # 2. GitHub releases (LFS-backed, large files)
    "https://github.com/ultralytics/playing-cards/releases/download/v0.0.1/best.pt",
    "https://github.com/edeverett/playing-cards-yolo/releases/download/v1.0/best.pt",
    # 3. Roboflow public mirror (some projects host weights publicly)
    "https://universe.roboflow.com/playing-cards/yolov8n-cards/resolve/main/best.pt",
]


def try_download_pretrained(out_path: str = "models/yolo_cards.pt",
                              timeout: int = 5) -> Optional[str]:
    """Try to download a pre-trained YOLO cards model.

    Returns the path to the downloaded model if successful, None otherwise.
    The caller should fall back to MANUAL mode if None is returned.

    The download is silent — no exception is raised on failure. The
    function tries each candidate URL in order, with a short timeout,
    and returns the first one that succeeds.
    """
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)

    for url in CANDIDATE_URLS:
        try:
            # HEAD-like check first: try to fetch with short timeout
            req = urllib.request.Request(url, method="GET",
                                          headers={"User-Agent": "rami-ai/0.1"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if resp.status != 200:
                    continue
                data = resp.read()
                # Must be > 1MB to be a real YOLO model
                if len(data) < 1_000_000:
                    continue
                # Write to disk
                with open(out_path, "wb") as f:
                    f.write(data)
                return out_path
        except Exception:
            continue

    return None


def list_candidate_urls() -> List[str]:
    """Return the list of candidate URLs (for documentation/debugging)."""
    return list(CANDIDATE_URLS)


def get_model_info(path: str) -> dict:
    """Return basic info about a downloaded model file."""
    if not os.path.exists(path):
        return {"exists": False}
    size = os.path.getsize(path)
    with open(path, "rb") as f:
        # Read first 4KB to compute a quick hash
        head = f.read(4096)
    return {
        "exists": True,
        "size_bytes": size,
        "size_mb": round(size / (1024 * 1024), 2),
        "sha256_head": hashlib.sha256(head).hexdigest()[:16],
        "path": path,
    }
