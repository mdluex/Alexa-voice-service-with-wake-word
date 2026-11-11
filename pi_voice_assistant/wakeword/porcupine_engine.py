"""Optional Picovoice Porcupine wake-word engine.

Picovoice ended free-tier AccessKeys on 2026-06-30. This backend remains for
users with a valid paid AccessKey. Porcupine keyword files (.ppn) are
platform- and version-specific; regenerate models in the Picovoice Console for
the Porcupine version you install.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from pathlib import Path

from .base import WakeWordEngine

logger = logging.getLogger(__name__)


class PorcupineEngine(WakeWordEngine):
    def __init__(
        self,
        access_key: str,
        keyword_paths: Sequence[Path] = (),
        sensitivities: Sequence[float] = (0.5,),
        builtin_keyword: str = "porcupine",
    ) -> None:
        try:
            import pvporcupine
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "pvporcupine is required for WAKE_ENGINE=porcupine. "
                "Install optional deps: pip install -r requirements-porcupine.txt"
            ) from exc

        self._pvporcupine = pvporcupine
        create_kwargs = {"access_key": access_key}

        if keyword_paths:
            paths = [str(path) for path in keyword_paths]
            create_kwargs["keyword_paths"] = paths
            create_kwargs["sensitivities"] = list(sensitivities)
            self._labels = [_label_from_path(path) for path in keyword_paths]
        else:
            create_kwargs["keywords"] = [builtin_keyword]
            create_kwargs["sensitivities"] = [sensitivities[0] if sensitivities else 0.5]
            self._labels = [builtin_keyword]

        self._porcupine = pvporcupine.create(**create_kwargs)
        self._frame_length = self._porcupine.frame_length
        self._buffer = bytearray()
        logger.info(
            "Porcupine ready (keywords=%s, frame_length=%s)",
            self._labels,
            self._frame_length,
        )

    def process(self, pcm_chunk: bytes) -> str | None:
        import struct

        self._buffer.extend(pcm_chunk)
        bytes_needed = self._frame_length * 2

        while len(self._buffer) >= bytes_needed:
            frame_bytes = bytes(self._buffer[:bytes_needed])
            del self._buffer[:bytes_needed]
            pcm = struct.unpack(f"{self._frame_length}h", frame_bytes)
            result = self._porcupine.process(pcm)
            if result >= 0:
                self._buffer.clear()
                return self._labels[result]
        return None

    def close(self) -> None:
        self._porcupine.delete()


def _label_from_path(path: Path) -> str:
    stem = Path(path).name.replace(".ppn", "")
    parts = stem.split("_")
    if len(parts) > 6:
        return " ".join(parts[0:-6])
    return parts[0]
