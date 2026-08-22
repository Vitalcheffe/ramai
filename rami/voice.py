"""AI voice channel — French speech synthesis with gTTS fallback.

Primary: browser speechSynthesis (instant, free, no API key).
Fallback: gTTS (Google Text-to-Speech) + IPython.display.Audio, used
when the browser doesn't have speechSynthesis or when running in a
context that mutes it (some Colab iframes).

Every spoken phrase is ALSO printed to the notebook output, so the
game is playable in silence and accessible.

Usage:
    from rami.voice import Voice
    v = Voice()
    v.say("9 de pique. Range-le face cachée en position 12.")
    # → printed: "[voice] 9 de pique..."
    # → spoken via speechSynthesis in the browser
"""
from __future__ import annotations
from typing import Optional
import time


class Voice:
    """French-speaking voice for the AI croupier."""

    def __init__(self, lang: str = "fr-FR", use_browser: bool = True,
                 use_gtts: bool = True, verbose: bool = True):
        self.lang = lang
        self.use_browser = use_browser
        self.use_gtts = use_gtts
        self.verbose = verbose
        self._history: list[dict] = []
        self._browser_available: Optional[bool] = None
        self._init_browser()

    def _init_browser(self) -> None:
        """Initialize the browser speechSynthesis (inject JS check)."""
        if not self.use_browser:
            self._browser_available = False
            return
        try:
            from IPython.display import Javascript, display
            from google.colab.output import eval_js
            # The JS bridge is part of stream.py's _JS_LIVE_STREAM
            # Try to use it; if not loaded, voice just prints
            self._browser_available = True  # optimistically
        except ImportError:
            self._browser_available = False

    def say(self, text: str, also_print: bool = True) -> dict:
        """Speak a phrase in French and record it.

        Returns a dict with the text, timestamp, and method used.
        """
        ts = time.time()
        record = {
            "text": text,
            "timestamp": ts,
            "datetime": time.strftime("%H:%M:%S", time.localtime(ts)),
            "method": None,
            "success": False,
        }

        # Always print (for silence / accessibility / debugging)
        if also_print and self.verbose:
            print(f"[voice {record['datetime']}] {text}")

        # Try browser speechSynthesis first
        if self._try_browser(text):
            record["method"] = "browser"
            record["success"] = True
        elif self.use_gtts and self._try_gtts(text):
            record["method"] = "gtts"
            record["success"] = True
        else:
            record["method"] = "none"
            record["success"] = False

        self._history.append(record)
        return record

    def _try_browser(self, text: str) -> bool:
        """Try to speak via the browser's speechSynthesis API."""
        if not self._browser_available:
            return False
        try:
            from google.colab.output import eval_js
            # Escape quotes in text
            escaped = text.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"')
            result = eval_js(f"window._ramiVoice.speak('{escaped}', '{self.lang}')")
            # Give it time to actually speak (rough estimate: 150 wpm = ~70ms per word)
            words = len(text.split())
            time.sleep(min(0.5 + words * 0.07, 8.0))
            return result == "spoken"
        except Exception:
            return False

    def _try_gtts(self, text: str) -> bool:
        """Fallback: generate audio via gTTS and play it."""
        try:
            from gtts import gTTS
            from IPython.display import Audio, display
            import tempfile, os
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                tts = gTTS(text=text, lang=self.lang[:2])
                tts.save(f.name)
                path = f.name
            display(Audio(path, autoplay=True))
            # Wait for playback
            words = len(text.split())
            time.sleep(min(0.5 + words * 0.07, 8.0))
            try:
                os.unlink(path)
            except Exception:
                pass
            return True
        except ImportError:
            return False
        except Exception:
            return False

    def cancel(self) -> None:
        """Stop any ongoing speech."""
        if self._browser_available:
            try:
                from google.colab.output import eval_js
                eval_js("window._ramiVoice.cancel()")
            except Exception:
                pass

    def history(self) -> list[dict]:
        """Return the full voice history (for the report)."""
        return list(self._history)

    def last_phrases(self, n: int = 10) -> list[dict]:
        """Return the last N spoken phrases."""
        return self._history[-n:]


def speak_sequence(phrases: list[str]) -> list[dict]:
    """Convenience: speak a sequence of phrases, return the history."""
    v = Voice()
    for p in phrases:
        v.say(p)
    return v.history()
