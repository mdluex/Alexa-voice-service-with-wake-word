"""Microphone capture and simple playback helpers."""

from __future__ import annotations

import logging
import shutil
import subprocess
import wave
from collections.abc import Iterator
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

SAMPLE_RATE = 16000
SAMPLE_WIDTH = 2
CHANNELS = 1
# 1024 samples = 64 ms at 16 kHz; matches pyopen-wakeword CLI chunking.
DEFAULT_CHUNK_SAMPLES = 1024


def play_wav(path: Path) -> None:
    """Play a WAV file with aplay when available, otherwise skip gracefully."""
    if not path.is_file():
        logger.warning("Startup sound not found: %s", path)
        return

    aplay = shutil.which("aplay")
    if aplay:
        subprocess.run([aplay, "-q", str(path)], check=False)
        return

    logger.warning("aplay not found; skipping playback of %s", path)


def speak_text(text: str, tts_command: str = "espeak-ng") -> None:
    """Speak text with a local TTS binary (default: espeak-ng)."""
    binary = shutil.which(tts_command) or shutil.which("espeak") or shutil.which("festival")
    if not binary:
        logger.warning("No TTS binary found (%s); printing reply instead: %s", tts_command, text)
        print(text)
        return

    name = Path(binary).name
    if name.startswith("espeak"):
        subprocess.run([binary, text], check=False)
    elif name == "festival":
        subprocess.run([binary, "--tts"], input=text.encode("utf-8"), check=False)
    else:
        subprocess.run([binary, text], check=False)


class MicrophoneStream:
    """Blocking microphone reader that yields raw int16 mono PCM bytes."""

    def __init__(
        self,
        sample_rate: int = SAMPLE_RATE,
        chunk_samples: int = DEFAULT_CHUNK_SAMPLES,
        device: str | None = None,
    ) -> None:
        self.sample_rate = sample_rate
        self.chunk_samples = chunk_samples
        self.device = _parse_device(device)
        self._stream = None
        self._sd = None

    def __enter__(self) -> MicrophoneStream:
        try:
            import sounddevice as sd
        except ImportError as exc:  # pragma: no cover - exercised on incomplete installs
            raise RuntimeError(
                "sounddevice is required for microphone capture. "
                "Install dependencies from requirements.txt."
            ) from exc

        self._sd = sd
        self._stream = sd.RawInputStream(
            samplerate=self.sample_rate,
            blocksize=self.chunk_samples,
            dtype="int16",
            channels=CHANNELS,
            device=self.device,
        )
        self._stream.start()
        logger.info(
            "Microphone opened (device=%s, rate=%s, chunk=%s)",
            self.device if self.device is not None else "default",
            self.sample_rate,
            self.chunk_samples,
        )
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None

    def read_chunk(self) -> bytes:
        if self._stream is None:
            raise RuntimeError("MicrophoneStream is not open")
        data, overflowed = self._stream.read(self.chunk_samples)
        if overflowed:
            logger.debug("Microphone overflow detected")
        return bytes(data)

    def chunks(self) -> Iterator[bytes]:
        while True:
            yield self.read_chunk()


def record_seconds(
    seconds: float,
    sample_rate: int = SAMPLE_RATE,
    device: str | None = None,
) -> bytes:
    """Record a fixed amount of mono int16 audio and return raw PCM bytes."""
    try:
        import sounddevice as sd
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("sounddevice is required for recording") from exc

    frames = int(seconds * sample_rate)
    audio = sd.rec(
        frames,
        samplerate=sample_rate,
        channels=CHANNELS,
        dtype="int16",
        device=_parse_device(device),
    )
    sd.wait()
    return np.asarray(audio).tobytes()


def write_wav(path: Path, pcm: bytes, sample_rate: int = SAMPLE_RATE) -> None:
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(CHANNELS)
        wav_file.setsampwidth(SAMPLE_WIDTH)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm)


def _parse_device(device: str | None):
    if device is None or device == "":
        return None
    try:
        return int(device)
    except ValueError:
        return device
