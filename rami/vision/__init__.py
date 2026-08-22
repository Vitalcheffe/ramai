"""Rami vision package — YOLO card detection + calibration + clusters + camera."""
from .detector import CardDetector, Detection, MockDetector
from .calibration import (
    CalibrationResult, DiscardDetection, MeldCluster,
    calibrate_camera, detect_discard_pile, detect_meld_clusters,
    find_extendable_melds,
)
from .camera import (
    CameraStatus, prewarm_camera, capture_photo, is_camera_ready,
    get_camera_status, stop_camera,
)
from .pretrained import (
    try_download_pretrained, list_candidate_urls, get_model_info,
)

__all__ = [
    # Detector
    "CardDetector", "Detection", "MockDetector",
    # Calibration
    "CalibrationResult", "DiscardDetection", "MeldCluster",
    "calibrate_camera", "detect_discard_pile", "detect_meld_clusters",
    "find_extendable_melds",
    # Camera
    "CameraStatus", "prewarm_camera", "capture_photo", "is_camera_ready",
    "get_camera_status", "stop_camera",
    # Pre-trained model downloader
    "try_download_pretrained", "list_candidate_urls", "get_model_info",
]
