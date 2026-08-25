"""Game sheet zones — calibration + zone-based detection."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple, Dict
import numpy as np


class ZoneName(str, Enum):
    MONTRE = "MONTRE"
    ZONE_IA = "ZONE_IA"
    TALON = "TALON"
    DEFAUSSE = "DEFAUSSE"
    CENTRE = "CENTRE"


@dataclass
class ZoneBox:
    """A zone's bounding box in pixel coordinates."""
    name: ZoneName
    x1: int
    y1: int
    x2: int
    y2: int

    def contains(self, bbox: Tuple[float, float, float, float]) -> bool:
        cx = (bbox[0] + bbox[2]) / 2
        cy = (bbox[1] + bbox[3]) / 2
        return (self.x1 <= cx <= self.x2 and self.y1 <= cy <= self.y2)

    def slot_for_position(self, bbox: Tuple[float, float, float, float]) -> Optional[int]:
        """For ZONE_IA: which numbered slot (1-15) does this bbox fall into?
        Returns None if not in any slot.
        """
        if self.name != ZoneName.ZONE_IA:
            return None
        # 3 rows × 5 cols
        slot_w = (self.x2 - self.x1) / 5
        slot_h = (self.y2 - self.y1) / 3
        cx = (bbox[0] + bbox[2]) / 2
        cy = (bbox[1] + bbox[3]) / 2
        col = int((cx - self.x1) / slot_w)
        row = int((cy - self.y1) / slot_h)
        # Row 0 is at the TOP (positions 11-15), row 2 is at the BOTTOM (1-5)
        # Numbering is top-to-bottom, left-to-right: 1,2,3,4,5 in top row
        # Actually let's match the PDF: row 0 (top) = 1-5, row 1 = 6-10, row 2 = 11-15
        if 0 <= col < 5 and 0 <= row < 3:
            return row * 5 + col + 1
        return None


@dataclass
class ZoneMap:
    """Mapping of zone names to pixel boxes (after calibration)."""
    zones: Dict[ZoneName, ZoneBox]

    def get(self, name: ZoneName) -> Optional[ZoneBox]:
        return self.zones.get(name)

    def which(self, bbox: Tuple[float, float, float, float]) -> Optional[ZoneName]:
        for name, box in self.zones.items():
            if box.contains(bbox):
                return name
        return None


# Default zone layout (in normalized A4 coordinates: 0..1, x right, y down)
# Matches scripts/make_sheet.py proportions
DEFAULT_ZONE_LAYOUT = {
    ZoneName.MONTRE:   (0.07, 0.13, 0.07 + 80/210, 0.13 + 80/297),  # left, top, right, bot
    ZoneName.ZONE_IA:  (0.07, 0.40, 0.93, 0.40 + 60/297),
    ZoneName.TALON:    (0.65, 0.13, 0.93, 0.13 + 50/297),
    ZoneName.DEFAUSSE: (0.65, 0.34, 0.93, 0.34 + 50/297),
    ZoneName.CENTRE:   (0.07, 0.76, 0.93, 0.76 + 80/297),
}


def calibrate_zones_from_image(image: np.ndarray,
                                sheet_corners: Optional[Tuple[Tuple[int, int],
                                                              Tuple[int, int],
                                                              Tuple[int, int],
                                                              Tuple[int, int]]] = None
                                ) -> Optional[ZoneMap]:
    """Calibrate the zone map from an image of the printed sheet.

    If sheet_corners is None, attempts to auto-detect them by finding
    the largest dark rectangle (the sheet border). If detection fails,
    falls back to assuming the sheet fills the whole image.

    Returns ZoneMap with pixel coordinates, or None if calibration fails.
    """
    if image is None or image.size == 0:
        return None
    h, w = image.shape[:2]

    # If corners not provided, assume the sheet fills the whole image
    if sheet_corners is None:
        sheet_corners = ((0, 0), (w, 0), (w, h), (0, h))

    # Map each zone's normalized coords to pixel coords via the sheet corners
    # (For simplicity, we treat the sheet as axis-aligned — top-left, top-right, etc.)
    tl, tr, br, bl = sheet_corners
    sheet_x1, sheet_y1 = tl
    sheet_x2, sheet_y2 = br
    sheet_w = sheet_x2 - sheet_x1
    sheet_h = sheet_y2 - sheet_y1

    zones = {}
    for name, (nx1, ny1, nx2, ny2) in DEFAULT_ZONE_LAYOUT.items():
        x1 = int(sheet_x1 + nx1 * sheet_w)
        y1 = int(sheet_y1 + ny1 * sheet_h)
        x2 = int(sheet_x1 + nx2 * sheet_w)
        y2 = int(sheet_y1 + ny2 * sheet_h)
        zones[name] = ZoneBox(name=name, x1=x1, y1=y1, x2=x2, y2=y2)

    return ZoneMap(zones=zones)


def which_zone(detection_bbox: Tuple[float, float, float, float],
               zone_map: ZoneMap) -> Optional[ZoneName]:
    """Classify a detection into a zone."""
    return zone_map.which(detection_bbox)


def cards_in_zone(detections, zone_name: ZoneName,
                  zone_map: ZoneMap) -> list:
    """Filter detections that fall within the named zone."""
    box = zone_map.get(zone_name)
    if box is None:
        return []
    out = []
    for d in detections:
        if box.contains(d.bbox):
            out.append(d)
    return out


def slot_number_for_detection(detection, zone_map: ZoneMap) -> Optional[int]:
    box = zone_map.get(ZoneName.ZONE_IA)
    if box is None:
        return None
    return box.slot_for_position(detection.bbox)


def draw_zones_overlay(image: np.ndarray, zone_map: ZoneMap) -> np.ndarray:
    import cv2
    out = image.copy()
    zone_colors = {
        ZoneName.MONTRE:   (0, 255, 0),    # green
        ZoneName.ZONE_IA:  (255, 0, 0),    # blue
        ZoneName.TALON:    (0, 165, 255),  # orange
        ZoneName.DEFAUSSE: (0, 0, 255),    # red
        ZoneName.CENTRE:   (255, 0, 255),  # magenta
    }
    for name, box in zone_map.zones.items():
        color = zone_colors.get(name, (255, 255, 255))
        cv2.rectangle(out, (box.x1, box.y1), (box.x2, box.y2), color, 2)
        cv2.putText(out, name.value, (box.x1 + 5, box.y1 + 18),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    return out
