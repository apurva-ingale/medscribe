import functools
import subprocess

from faster_whisper import WhisperModel

from .config import settings


@functools.lru_cache(maxsize=1)
def _model() -> WhisperModel:
    return WhisperModel(settings.whisper_model, device="cpu", compute_type=settings.whisper_compute_type)


def preprocess(src: str, dst: str) -> None:
    """Any container/codec -> 16 kHz mono WAV, high-pass filtered and loudness-normalised."""
    cmd = ["ffmpeg", "-y", "-i", src, "-vn", "-ac", "1", "-ar", "16000", "-af", "highpass=f=80,loudnorm", dst]
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode != 0:
        raise RuntimeError("Could not read the audio file: " + r.stderr.decode(errors="ignore")[-300:])


def transcribe(wav_path: str) -> str:
    segments, _ = _model().transcribe(wav_path, vad_filter=True, beam_size=5)
    text = "\n".join(s.text.strip() for s in segments if s.text.strip())
    if not text:
        raise RuntimeError("No speech detected in the recording")
    return text
