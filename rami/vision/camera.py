"""Robust Colab camera bridge with permission pre-warming.

PROBLEM: The standard `getUserMedia` JS bridge only requests camera
permission when called. If the JS isn't loaded yet, or the user clicks
the capture button before the JS is ready, the permission prompt never
appears — the photo call just returns null or hangs.

SOLUTION: This module provides a single `prewarm_camera()` function
that you call at notebook init. It:
  1. Injects the JS bridge into the Colab page
  2. Calls `getUserMedia` immediately to trigger the browser permission prompt
  3. Keeps the stream alive in a hidden <video> element
  4. Returns "granted" | "denied" | "unavailable"

Once pre-warmed, `capture_photo()` just snapshots the running stream —
no new permission prompt, no race condition.

Usage:
    from rami.vision.camera import prewarm_camera, capture_photo, is_camera_ready

    status = prewarm_camera()  # call in Cellule 1
    if status == "granted":
        img = capture_photo()  # call later, no permission prompt
"""
from __future__ import annotations
from typing import Optional, Literal
import base64
import numpy as np


CameraStatus = Literal["granted", "denied", "unavailable", "unknown"]


# Global state — set by prewarm_camera(), read by is_camera_ready()
_CAMERA_STATUS: CameraStatus = "unknown"


# The JS bridge code, injected once via IPython.display.Javascript
_JS_BRIDGE = """
window._ramiCamera = {
  stream: null,
  video: null,
  status: 'unknown',

  async prewarm() {
    try {
      this.stream = await navigator.mediaDevices.getUserMedia({video: true});
      this.video = document.createElement('video');
      this.video.style.display = 'none';
      this.video.srcObject = this.stream;
      document.body.appendChild(this.video);
      await this.video.play();
      this.status = 'granted';
      return 'granted';
    } catch (err) {
      console.warn('Camera permission denied or unavailable:', err);
      this.status = 'denied';
      return 'denied';
    }
  },

  capture(quality) {
    if (this.status !== 'granted' || !this.video) {
      return null;
    }
    const canvas = document.createElement('canvas');
    canvas.width = this.video.videoWidth || 640;
    canvas.height = this.video.videoHeight || 480;
    canvas.getContext('2d').drawImage(this.video, 0, 0);
    return canvas.toDataURL('image/jpeg', quality);
  },

  stop() {
    if (this.stream) {
      this.stream.getTracks().forEach(t => t.stop());
      this.stream = null;
      this.video = null;
      this.status = 'stopped';
    }
  }
};
"""


def prewarm_camera() -> CameraStatus:
    """Pre-warm the camera by requesting permission immediately.

    Call this at the top of the notebook (Cellule 1). It triggers the
    browser permission prompt BEFORE any photo button is clicked, so
    the prompt actually appears.

    Returns "granted" if the camera is ready, "denied" if the user
    refused, "unavailable" if no camera detected.
    """
    global _CAMERA_STATUS
    try:
        from IPython.display import Javascript, display
        from google.colab.output import eval_js
    except ImportError:
        _CAMERA_STATUS = "unavailable"
        return _CAMERA_STATUS

    try:
        # Inject the JS bridge
        display(Javascript(_JS_BRIDGE))
        # Small delay to let JS load
        import time
        time.sleep(0.5)
        # Trigger the permission prompt
        status = eval_js("window._ramiCamera.prewarm()")
        _CAMERA_STATUS = status if status in ("granted", "denied") else "unknown"
        return _CAMERA_STATUS
    except Exception as e:
        _CAMERA_STATUS = "unavailable"
        return _CAMERA_STATUS


def is_camera_ready() -> bool:
    """Check if the camera is ready to capture (prewarm_camera was called
    and permission was granted)."""
    return _CAMERA_STATUS == "granted"


def get_camera_status() -> CameraStatus:
    """Return the current camera status."""
    return _CAMERA_STATUS


def capture_photo(quality: float = 0.85) -> Optional[np.ndarray]:
    """Capture a photo from the running camera stream.

    Requires prewarm_camera() to have been called and granted.

    Returns a numpy array (BGR format for OpenCV), or None if the
    camera isn't ready.
    """
    if not is_camera_ready():
        return None
    try:
        from IPython.display import Javascript, display
        from google.colab.output import eval_js
    except ImportError:
        return None

    try:
        data_url = eval_js(f"window._ramiCamera.capture({quality})")
        if not data_url or data_url == "null":
            return None
        # Strip the "data:image/jpeg;base64," prefix
        if "," in data_url:
            data_url = data_url.split(",", 1)[1]
        binary = base64.b64decode(data_url)
        arr = np.frombuffer(binary, dtype=np.uint8)
        import cv2
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        return img
    except Exception:
        return None


def stop_camera() -> None:
    """Stop the camera stream (releases the device)."""
    global _CAMERA_STATUS
    try:
        from IPython.display import Javascript, display
        from google.colab.output import eval_js
        eval_js("window._ramiCamera.stop()")
    except Exception:
        pass
    _CAMERA_STATUS = "stopped"
