"""Live video stream from Colab output via getUserMedia bridge.

This is the heart of the croupier architecture. A continuous video
stream is displayed in the notebook output, frames are pulled into
Python at 2-5 FPS for detection, and the user sees themselves live
while the AI watches the table.

Architecture:
  - JS bridge injects a <video> element + <canvas> into the page
  - The <video> plays the getUserMedia stream live (user sees themselves)
  - Every 200-500ms, JS encodes the current frame as base64 JPEG
  - Python polls for the latest frame via eval_js
  - The frame is decoded into a numpy array for OpenCV/YOLO

If getUserMedia is blocked (iPad Safari in iframe), the module falls
back to file-input mode: each capture_photo() opens the native camera
app and returns a single photo.
"""
from __future__ import annotations
from typing import Optional, Literal
import base64
import time
import threading
import numpy as np


StreamStatus = Literal["streaming", "file_input", "unavailable", "stopped"]


_STREAM_STATUS: StreamStatus = "stopped"
_LATEST_FRAME: Optional[np.ndarray] = None
_FRAME_LOCK = threading.Lock()
_STREAM_THREAD: Optional[threading.Thread] = None
_STOP_FLAG = threading.Event()


# --- JS bridge for live video + speech synthesis ---

_JS_LIVE_STREAM = r"""
window._ramiStream = {
  video: null,
  canvas: null,
  stream: null,
  status: 'stopped',
  lastFrame: null,
  frameNumber: 0,
  container: null,

  async start() {
    try {
      this.stream = await navigator.mediaDevices.getUserMedia({
        video: {facingMode: 'environment', width: 1280, height: 720}
      });
      this.container = document.createElement('div');
      this.container.style.cssText = 'border: 4px solid #00ff00; padding: 8px; margin: 8px 0; background: #000; position: relative;';
      this.video = document.createElement('video');
      this.video.style.cssText = 'width: 100%; max-width: 640px; display: block;';
      this.video.autoplay = true;
      this.video.playsInline = true;
      this.video.muted = true;
      this.video.srcObject = this.stream;
      this.container.appendChild(this.video);

      // Status overlay
      const status = document.createElement('div');
      status.id = 'rami-status';
      status.style.cssText = 'position: absolute; top: 8px; right: 8px; background: rgba(0,0,0,0.7); color: #0f0; padding: 4px 8px; font-family: monospace; font-size: 12px;';
      this.container.appendChild(status);

      this.canvas = document.createElement('canvas');
      this.canvas.style.display = 'none';

      document.body.appendChild(this.container);
      document.body.appendChild(this.canvas);

      await this.video.play();
      this.status = 'streaming';
      this._loop();
      return 'streaming';
    } catch (err) {
      console.warn('getUserMedia failed:', err);
      this.status = 'file_input';
      return 'file_input';
    }
  },

  _loop() {
    if (this.status !== 'streaming') return;
    try {
      if (this.video.videoWidth > 0) {
        this.canvas.width = this.video.videoWidth;
        this.canvas.height = this.video.videoHeight;
        const ctx = this.canvas.getContext('2d');
        ctx.drawImage(this.video, 0, 0);
        // Downscale for transport — 640px wide is plenty for card detection
        const targetW = 640;
        const scale = targetW / this.canvas.width;
        const targetH = Math.round(this.canvas.height * scale);
        const tmp = document.createElement('canvas');
        tmp.width = targetW;
        tmp.height = targetH;
        tmp.getContext('2d').drawImage(this.canvas, 0, 0, targetW, targetH);
        this.lastFrame = tmp.toDataURL('image/jpeg', 0.7);
        this.frameNumber++;
        const status = document.getElementById('rami-status');
        if (status) status.textContent = `FRAME ${this.frameNumber} • LIVE`;
      }
    } catch (e) {
      console.warn('frame capture error:', e);
    }
    setTimeout(() => this._loop(), 250);  // 4 FPS
  },

  getFrame() {
    return this.lastFrame;
  },

  getFrameNumber() {
    return this.frameNumber;
  },

  stop() {
    if (this.stream) {
      this.stream.getTracks().forEach(t => t.stop());
      this.stream = null;
    }
    if (this.container) {
      this.container.remove();
      this.container = null;
    }
    this.video = null;
    this.canvas = null;
    this.lastFrame = null;
    this.status = 'stopped';
  }
};

window._ramiVoice = {
  speak(text, lang) {
    if ('speechSynthesis' in window) {
      const u = new SpeechSynthesisUtterance(text);
      u.lang = lang || 'fr-FR';
      u.rate = 1.0;
      u.pitch = 1.0;
      window.speechSynthesis.speak(u);
      return 'spoken';
    }
    return 'unavailable';
  },
  cancel() {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
  }
};
"""


def start_stream() -> StreamStatus:
    """Start the live video stream. Injects the JS bridge, requests camera
    permission, displays the live video in the notebook output, and starts
    a background thread that pulls frames into Python at 4 FPS.

    Returns 'streaming' if the live stream is up, 'file_input' if
    getUserMedia was blocked (iPad Safari fallback), 'unavailable' if no
    camera at all.
    """
    global _STREAM_STATUS, _STREAM_THREAD, _STOP_FLAG
    try:
        from IPython.display import Javascript, display
        from google.colab.output import eval_js
    except ImportError:
        _STREAM_STATUS = "unavailable"
        return _STREAM_STATUS

    try:
        display(Javascript(_JS_LIVE_STREAM))
        time.sleep(0.5)
        status = eval_js("window._ramiStream.start()")
        _STREAM_STATUS = status if status in ("streaming", "file_input") else "unavailable"

        if _STREAM_STATUS == "streaming":
            _STOP_FLAG.clear()
            _STREAM_THREAD = threading.Thread(target=_frame_puller, daemon=True)
            _STREAM_THREAD.start()
        return _STREAM_STATUS
    except Exception:
        _STREAM_STATUS = "unavailable"
        return _STREAM_STATUS


def _frame_puller() -> None:
    """Background thread: pulls latest frame from JS into Python."""
    global _LATEST_FRAME
    try:
        from google.colab.output import eval_js
    except ImportError:
        return
    while not _STOP_FLAG.is_set() and _STREAM_STATUS == "streaming":
        try:
            data_url = eval_js("window._ramiStream.getFrame()")
            if data_url and data_url != "null":
                if "," in data_url:
                    data_url = data_url.split(",", 1)[1]
                binary = base64.b64decode(data_url)
                arr = np.frombuffer(binary, dtype=np.uint8)
                import cv2
                img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
                if img is not None:
                    with _FRAME_LOCK:
                        global _LATEST_FRAME
                        _LATEST_FRAME = img
        except Exception:
            pass
        time.sleep(0.25)


def get_latest_frame() -> Optional[np.ndarray]:
    """Return the latest captured frame (numpy array, BGR) or None."""
    with _FRAME_LOCK:
        if _LATEST_FRAME is not None:
            return _LATEST_FRAME.copy()
    return None


def get_frame_number() -> int:
    """Return the current frame counter from JS."""
    if _STREAM_STATUS != "streaming":
        return 0
    try:
        from google.colab.output import eval_js
        return int(eval_js("window._ramiStream.getFrameNumber()") or 0)
    except Exception:
        return 0


def capture_photo() -> Optional[np.ndarray]:
    """Capture a single photo. In streaming mode, returns the latest frame.
    In file_input mode, opens the native camera app."""
    if _STREAM_STATUS == "streaming":
        return get_latest_frame()
    elif _STREAM_STATUS == "file_input":
        from .camera import capture_photo_file_input
        return capture_photo_file_input()
    else:
        return None


def get_stream_status() -> StreamStatus:
    return _STREAM_STATUS


def is_streaming() -> bool:
    return _STREAM_STATUS == "streaming"


def stop_stream() -> None:
    """Stop the stream and clean up."""
    global _STREAM_STATUS
    _STOP_FLAG.set()
    if _STREAM_THREAD:
        _STREAM_THREAD.join(timeout=2)
    try:
        from google.colab.output import eval_js
        eval_js("window._ramiStream.stop()")
    except Exception:
        pass
    _STREAM_STATUS = "stopped"
