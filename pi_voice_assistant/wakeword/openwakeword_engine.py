"""openWakeWord engine using the maintained pyopen-wakeword package."""

from __future__ import annotations

import logging
from pathlib import Path

from .base import WakeWordEngine

logger = logging.getLogger(__name__)


class OpenWakeWordEngine(WakeWordEngine):
    def __init__(
        self,
        model_name: str = "alexa",
        model_path: Path | None = None,
        threshold: float = 0.5,
    ) -> None:
        try:
            from pyopen_wakeword import Model, OpenWakeWord, OpenWakeWordFeatures
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "pyopen-wakeword is required. Install dependencies from requirements.txt."
            ) from exc

        self.threshold = threshold
        self.label = model_name
        self._features = OpenWakeWordFeatures.from_builtin()

        if model_path is not None:
            path = Path(model_path)
            if not path.is_file():
                raise FileNotFoundError(f"openWakeWord model not found: {path}")
            self._model = OpenWakeWord.from_model(str(path))
            self.label = path.stem
        else:
            try:
                builtin = Model(model_name)
            except ValueError as exc:
                valid = ", ".join(m.value for m in Model)
                raise ValueError(
                    f"Unknown openWakeWord model {model_name!r}. Built-ins: {valid}"
                ) from exc
            self._model = OpenWakeWord.from_builtin(builtin)
            self.label = builtin.value

        logger.info("openWakeWord ready (model=%s, threshold=%.2f)", self.label, threshold)

    def process(self, pcm_chunk: bytes) -> str | None:
        for features in self._features.process_streaming(pcm_chunk):
            for probability in self._model.process_streaming(features):
                if probability >= self.threshold:
                    self._model.reset()
                    self._features.reset()
                    return self.label
        return None

    def close(self) -> None:
        self._model.close()
        self._features.close()
