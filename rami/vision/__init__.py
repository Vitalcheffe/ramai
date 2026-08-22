"""Rami vision package — YOLO card detection + live stream + camera fallback."""
from .detector import CardDetector, Detection, MockDetector
from .calibration import (
    CalibrationResult, DiscardDetection, MeldCluster,
    calibrate_camera, detect_discard_pile, detect_meld_clusters,
    find_extendable_melds,
)
from .stream import (
    StreamStatus, start_stream, stop_stream, get_latest_frame,
    get_frame_number, get_stream_status, is_streaming, capture_photo,
)
from .camera import (
    CameraStatus, prewarm_camera, is_camera_ready, is_file_input_mode,
    get_camera_status, capture_photo_file_input, init_file_input_mode,
)
from .pretrained import (
    try_download_pretrained, get_model_info, get_download_url,
)

__all__ = [
    "CardDetector", "Detection", "MockDetector",
    "CalibrationResult", "DiscardDetection", "MeldCluster",
    "calibrate_camera", "detect_discard_pile", "detect_meld_clusters",
    "find_extendable_melds",
    "StreamStatus", "start_stream", "stop_stream", "get_latest_frame",
    "get_frame_number", "get_stream_status", "is_streaming", "capture_photo",
    "CameraStatus", "prewarm_camera", "is_camera_ready", "is_file_input_mode",
    "get_camera_status", "capture_photo_file_input", "init_file_input_mode",
    "try_download_pretrained", "get_model_info", "get_download_url",
]
