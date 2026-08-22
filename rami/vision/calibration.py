"""Vision pipeline for Rami: camera calibration, discard detection, meld cluster detection.

P6: Camera calibration
    - User points camera at table (iPad propped against a book, ~30° tilt)
    - We compute the homography from the table's 4 corners
    - If corners are well-detected and the perspective transform is reasonable
      (not too skewed), we display a green frame. Otherwise red.

P7: Discard detection (mandatory photo at end of turn)
    - Focus on the discard pile region only
    - Verify exactly 1 card is detected (the top)
    - If 0 or 2+ cards detected, refuse and re-prompt

P7b: Meld cluster detection
    - Detect all cards on the table
    - Group cards that are spatially close (< 1.5 × card-width apart)
    - Each cluster = a meld (or pile of deadwood if not recognized)
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Tuple
import math

import numpy as np


@dataclass
class CalibrationResult:
    is_good: bool
    message: str
    corners: Optional[Tuple[Tuple[int, int], ...]] = None  # 4 table corners
    perspective_ok: bool = False
    tilt_degrees: float = 0.0


@dataclass
class DiscardDetection:
    card_rank: Optional[str]   # "A", "2".."10", "J", "Q", "K", "Joker"
    card_suit: Optional[str]
    confidence: float
    is_reliable: bool          # True iff exactly 1 card detected + conf > 0.7
    n_cards_detected: int
    message: str


@dataclass
class MeldCluster:
    """A spatial group of cards on the table that likely form a meld."""
    cards: List[Tuple[str, str]]   # list of (rank, suit) tuples
    centroid: Tuple[float, float]
    bbox: Tuple[float, float, float, float]


# ---------- P6: Camera calibration ----------

def calibrate_camera(image: np.ndarray,
                     table_corners: Optional[Tuple[Tuple[int, int],
                                                   Tuple[int, int],
                                                   Tuple[int, int],
                                                   Tuple[int, int]]] = None) -> CalibrationResult:
    """Check if the camera angle is acceptable.

    Heuristic: if the user has marked the 4 corners of the table, we
    compute the perspective transform and check the skew. If not, we
    fall back to checking the image's aspect ratio of detected cards.

    For now, this is a stub that always returns 'good' if image is non-empty.
    The real implementation (in Colab, with the camera widget) uses
    cv2.getPerspectiveTransform + cv2.getPerspectiveTransform to compute
    the homography and check its condition number.
    """
    if image is None or image.size == 0:
        return CalibrationResult(is_good=False,
                                 message="Image vide.",
                                 perspective_ok=False)

    h, w = image.shape[:2]
    if h < 200 or w < 200:
        return CalibrationResult(is_good=False,
                                 message="Image trop petite. Rapproche la caméra.",
                                 perspective_ok=False)

    if table_corners is None:
        # No corners provided — assume OK but warn
        return CalibrationResult(
            is_good=True,
            message="Cadre la table avec les 4 coins pour activer la vérification d'angle.",
            perspective_ok=True,
            tilt_degrees=30.0,
        )

    # Compute perspective transform
    src = np.array(table_corners, dtype=np.float32)
    # Target: a rectangle 600x400 (typical table aspect)
    dst = np.array([[0, 0], [600, 0], [600, 400], [0, 400]], dtype=np.float32)
    M = cv2_getPerspectiveTransform(src, dst)

    # Compute tilt from the transform's first two rows
    # Tilt ≈ atan2(M[1, 0], M[0, 0]) × (180 / π)
    tilt = math.degrees(math.atan2(M[1, 0], M[0, 0]))

    # Check condition number (well-conditioned = good angle)
    cond = np.linalg.cond(M)
    perspective_ok = cond < 1e6 and abs(tilt) < 60

    if perspective_ok:
        return CalibrationResult(
            is_good=True,
            message=f"✓ Angle OK ({tilt:.1f}°). Tu peux jouer.",
            corners=table_corners,
            perspective_ok=True,
            tilt_degrees=tilt,
        )
    return CalibrationResult(
        is_good=False,
        message=f"✗ Angle trop prononcé ({tilt:.1f}°). Bouge l'iPad pour viser ~30°.",
        corners=table_corners,
        perspective_ok=False,
        tilt_degrees=tilt,
    )


def cv2_getPerspectiveTransform(src, dst):
    """Lazy import of cv2.getPerspectiveTransform so this module loads without cv2."""
    import cv2
    return cv2.getPerspectiveTransform(src, dst)


# ---------- P7: Discard detection ----------

def detect_discard_pile(detector, image: np.ndarray,
                         region: Optional[Tuple[int, int, int, int]] = None) -> DiscardDetection:
    """Detect the top of the discard pile. Refuses if not exactly 1 card.

    `region` is an optional bounding box (x1, y1, x2, y2) to crop to the
    discard area only (improves accuracy + avoids detecting other cards).
    """
    if image is None or image.size == 0:
        return DiscardDetection(card_rank=None, card_suit=None,
                               confidence=0.0, is_reliable=False,
                               n_cards_detected=0,
                               message="Image vide.")

    if region is not None:
        x1, y1, x2, y2 = region
        crop = image[y1:y2, x1:x2]
    else:
        crop = image

    detections = detector.predict(crop)
    n = len(detections)

    if n == 0:
        return DiscardDetection(card_rank=None, card_suit=None,
                               confidence=0.0, is_reliable=False,
                               n_cards_detected=0,
                               message="Aucune carte détectée. Recadre la défausse.")
    if n > 1:
        # Pick the highest-confidence detection
        best = max(detections, key=lambda d: d.confidence)
        return DiscardDetection(
            card_rank=best.rank, card_suit=best.suit,
            confidence=best.confidence,
            is_reliable=False,
            n_cards_detected=n,
            message=f"{n} cartes détectées. La défausse doit montrer UNE seule carte. "
                    f"Top: {best.rank}{best.suit} ({best.confidence*100:.0f}%)",
        )
    # Exactly 1 card
    d = detections[0]
    reliable = d.confidence > 0.7
    if reliable:
        return DiscardDetection(
            card_rank=d.rank, card_suit=d.suit,
            confidence=d.confidence,
            is_reliable=True,
            n_cards_detected=1,
            message=f"✓ Défausse reconnue: {d.rank}{d.suit} ({d.confidence*100:.0f}%)",
        )
    return DiscardDetection(
        card_rank=d.rank, card_suit=d.suit,
        confidence=d.confidence,
        is_reliable=False,
        n_cards_detected=1,
        message=f"Carte détectée ({d.rank}{d.suit}) mais confiance faible ({d.confidence*100:.0f}%). "
                f"Reprends la photo.",
    )


# ---------- P7b: Meld cluster detection ----------

def detect_meld_clusters(detector, image: np.ndarray,
                          card_distance_threshold: float = 1.5) -> List[MeldCluster]:
    """Detect all cards on the table and group them into clusters.

    Two cards are in the same cluster if their bboxes are within
    `card_distance_threshold` × card-width of each other.

    Returns a list of MeldCluster. Empty list if no cards detected.
    """
    detections = detector.predict(image)
    if not detections:
        return []

    # Compute pairwise distances between card centers
    centers = [((d.bbox[0] + d.bbox[2]) / 2, (d.bbox[1] + d.bbox[3]) / 2) for d in detections]
    widths = [d.bbox[2] - d.bbox[0] for d in detections]
    avg_width = sum(widths) / len(widths) if widths else 100

    # Union-find for clustering
    n = len(detections)
    parent = list(range(n))
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    def union(x, y):
        px, py = find(x), find(y)
        if px != py:
            parent[px] = py

    threshold = card_distance_threshold * avg_width
    for i in range(n):
        for j in range(i + 1, n):
            dx = centers[i][0] - centers[j][0]
            dy = centers[i][1] - centers[j][1]
            dist = math.sqrt(dx*dx + dy*dy)
            if dist < threshold:
                union(i, j)

    # Group detections by root
    clusters: dict = {}
    for i in range(n):
        root = find(i)
        clusters.setdefault(root, []).append(detections[i])

    # Build MeldCluster objects
    out: List[MeldCluster] = []
    for group in clusters.values():
        cards = [(d.rank, d.suit) for d in group]
        cx = sum((d.bbox[0] + d.bbox[2]) / 2 for d in group) / len(group)
        cy = sum((d.bbox[1] + d.bbox[3]) / 2 for d in group) / len(group)
        x1 = min(d.bbox[0] for d in group)
        y1 = min(d.bbox[1] for d in group)
        x2 = max(d.bbox[2] for d in group)
        y2 = max(d.bbox[3] for d in group)
        out.append(MeldCluster(cards=cards, centroid=(cx, cy), bbox=(x1, y1, x2, y2)))
    return out


def find_extendable_melds(clusters: List[MeldCluster],
                          player_card: Tuple[str, str]) -> List[int]:
    """Find which clusters a player's card can extend.

    Returns indices into `clusters` of melds the card can be added to.
    (Used by the AI to decide whether to extend an existing meld.)
    """
    from ..cards import RANK_NAMES
    target_rank, target_suit = player_card
    out = []
    for i, cluster in enumerate(clusters):
        # Group check: all same rank?
        ranks = set(r for r, _ in cluster.cards)
        if len(ranks) == 1 and target_rank == ranks.pop():
            if all(s != target_suit for _, s in cluster.cards):
                out.append(i)
            continue
        # Run check: same suit?
        suits = set(s for _, s in cluster.cards)
        if len(suits) == 1 and target_suit == suits.pop():
            # Convert ranks to integers
            from ..cards import RANK_NAMES
            rank_to_int = {v: k for k, v in RANK_NAMES.items()}
            int_ranks = sorted(rank_to_int.get(r, 0) for r, _ in cluster.cards)
            if int_ranks:
                if target_rank in RANK_NAMES.values():
                    target_int = rank_to_int[target_rank]
                    if target_int == int_ranks[0] - 1 or target_int == int_ranks[-1] + 1:
                        out.append(i)
    return out
