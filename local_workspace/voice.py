import subprocess
import tempfile
import threading
from pathlib import Path

_MODELS = {}
_LOCK = threading.Lock()


def transcribe(path, model_name="tiny"):
    from faster_whisper import WhisperModel
    with _LOCK:
        model = _MODELS.get(model_name)
        if model is None:
            model = WhisperModel(model_name, device="cpu", compute_type="int8")
            _MODELS[model_name] = model
    segments, info = model.transcribe(str(path), beam_size=3, vad_filter=True)
    text = " ".join(segment.text.strip() for segment in segments).strip()
    return {"text": text, "language": info.language, "probability": info.language_probability}


def speak(text):
    say = Path("/usr/bin/say")
    if not say.exists():
        raise RuntimeError("macOS speech is unavailable")
    payload = text[:12000]

    def worker():
        path = None
        try:
            with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as handle:
                handle.write(payload)
                path = Path(handle.name)
            subprocess.run([str(say), "-f", str(path)], check=False, timeout=300)
        finally:
            if path:
                path.unlink(missing_ok=True)

    threading.Thread(target=worker, daemon=True).start()
