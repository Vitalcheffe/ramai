"""Camera capture — prewarm + iPad Safari fallback."""
from __future__ import annotations
from typing import Optional, Literal
import base64
import numpy as np


CameraStatus = Literal["granted", "denied", "unavailable", "unknown", "file_input"]


_CAMERA_STATUS: CameraStatus = "unknown"


# --- Method 1: getUserMedia stream ---

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
      console.warn('getUserMedia failed:', err);
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

    Returns "granted" if getUserMedia works (Chrome, Firefox, Android).
    Returns "denied" if blocked (iPad Safari in Colab iframe).
    Returns "unavailable" if no camera or no JS bridge.
    """
    global _CAMERA_STATUS
    try:
        from IPython.display import Javascript, display
        from google.colab.output import eval_js
    except ImportError:
        _CAMERA_STATUS = "unavailable"
        return _CAMERA_STATUS

    try:
        display(Javascript(_JS_BRIDGE))
        import time
        time.sleep(0.5)
        status = eval_js("window._ramiCamera.prewarm()")
        _CAMERA_STATUS = status if status in ("granted", "denied") else "unknown"
        if _CAMERA_STATUS == "denied":
            # Fall back to file input method
            _CAMERA_STATUS = "file_input"
        return _CAMERA_STATUS
    except Exception:
        _CAMERA_STATUS = "unavailable"
        return _CAMERA_STATUS


def is_camera_ready() -> bool:
    """Check if getUserMedia stream is ready (method 1)."""
    return _CAMERA_STATUS == "granted"


def is_file_input_mode() -> bool:
    """Check if we're in file-input fallback mode (method 2, iPad Safari)."""
    return _CAMERA_STATUS == "file_input"


def get_camera_status() -> CameraStatus:
    return _CAMERA_STATUS


def capture_photo(quality: float = 0.85) -> Optional[np.ndarray]:
    """Capture a photo.

    Method 1 (getUserMedia): if is_camera_ready() is True, snapshot the stream.
    Method 2 (file input): if is_file_input_mode() is True, fall back to
                            capture_photo_file_input() which opens the native
                            camera app.

    Returns numpy array (BGR) or None.
    """
    if _CAMERA_STATUS == "granted":
        return _capture_from_stream(quality)
    elif _CAMERA_STATUS == "file_input":
        return capture_photo_file_input()
    else:
        return None


def _capture_from_stream(quality: float = 0.85) -> Optional[np.ndarray]:
    """Capture from the running getUserMedia stream (method 1)."""
    try:
        from IPython.display import Javascript, display
        from google.colab.output import eval_js
        data_url = eval_js(f"window._ramiCamera.capture({quality})")
        if not data_url or data_url == "null":
            return None
        if "," in data_url:
            data_url = data_url.split(",", 1)[1]
        binary = base64.b64decode(data_url)
        arr = np.frombuffer(binary, dtype=np.uint8)
        import cv2
        return cv2.imdecode(arr, cv2.IMREAD_COLOR)
    except Exception:
        return None


# --- Method 2: <input type="file" accept="image/*" capture="environment"> ---

# This is the iPad Safari solution. It opens the native camera app,
# the user takes a single photo, and the photo is returned to the notebook.
#
# Implementation: we use ipywidgets to create a file upload button with
# capture=environment. When the user clicks it, iPad Safari opens the camera
# app. When the photo is taken, it's returned as a base64 string.

_FILE_INPUT_HTML = """
<div id="rami-file-input-container">
  <input type="file" id="rami-photo-input" accept="image/*" capture="environment"
         style="display: none;">
  <button id="rami-photo-button" onclick="document.getElementById('rami-photo-input').click()"
          style="padding: 12px 24px; font-size: 16px; background: #007bff; color: white;
                 border: none; border-radius: 6px; cursor: pointer;">
    📸 Take Photo
  </button>
  <div id="rami-photo-status" style="margin-top: 8px; color: #666;"></div>
</div>
<script>
window._ramiFilePhoto = {
  data: null,
  status: 'idle',

  setup() {
    const input = document.getElementById('rami-photo-input');
    const status = document.getElementById('rami-photo-status');
    input.addEventListener('change', function(e) {
      const file = e.target.files[0];
      if (!file) {
        status.textContent = 'No photo taken.';
        return;
      }
      status.textContent = 'Processing photo...';
      const reader = new FileReader();
      reader.onload = function(ev) {
        window._ramiFilePhoto.data = ev.target.result;
        window._ramiFilePhoto.status = 'captured';
        status.textContent = '✓ Photo captured (' + (file.size / 1024).toFixed(1) + ' KB)';
      };
      reader.readAsDataURL(file);
    });
  },

  capture() {
    window._ramiFilePhoto.data = null;
    window._ramiFilePhoto.status = 'capturing';
    document.getElementById('rami-photo-button').click();
    return window._ramiFilePhoto.status;
  },

  get_data() {
    return window._ramiFilePhoto.data;
  },

  get_status() {
    return window._ramiFilePhoto.status;
  }
};
window._ramiFilePhoto.setup();
</script>
"""


def init_file_input_mode():
    """Initialize the file-input HTML widget (call once when switching to
    file_input mode)."""
    from IPython.display import HTML, display
    display(HTML(_FILE_INPUT_HTML))


def capture_photo_file_input(timeout: int = 60) -> Optional[np.ndarray]:
    """Capture a photo using the native camera app (method 2).

    On iPad Safari, this opens the Camera app. The user takes a photo,
    and it's returned to the notebook.

    Polls for the photo data for up to `timeout` seconds.
    """
    from IPython.display import Javascript, display
    from google.colab.output import eval_js
    import time

    # Trigger the file input dialog
    eval_js("window._ramiFilePhoto.capture()")

    # Poll for the result
    start = time.time()
    while time.time() - start < timeout:
        status = eval_js("window._ramiFilePhoto.get_status()")
        if status == "captured":
            data_url = eval_js("window._ramiFilePhoto.get_data()")
            if not data_url:
                continue
            if "," in data_url:
                data_url = data_url.split(",", 1)[1]
            try:
                binary = base64.b64decode(data_url)
                arr = np.frombuffer(binary, dtype=np.uint8)
                import cv2
                img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
                return img
            except Exception:
                return None
        time.sleep(0.5)

    return None


def stop_camera() -> None:
    global _CAMERA_STATUS
    if _CAMERA_STATUS == "granted":
        try:
            from IPython.display import Javascript, display
            from google.colab.output import eval_js
            eval_js("window._ramiCamera.stop()")
        except Exception:
            pass
    _CAMERA_STATUS = "stopped"
