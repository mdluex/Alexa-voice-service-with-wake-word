"""Wake-word engine interface."""

from __future__ import annotations

from abc import ABC, abstractmethod


class WakeWordEngine(ABC):
    """Process PCM audio chunks and report wake-word detections."""

    @abstractmethod
    def process(self, pcm_chunk: bytes) -> str | None:
        """Return the detected wake-word label, or None."""

    def close(self) -> None:
        """Release native resources."""
        return None

    def __enter__(self) -> WakeWordEngine:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
