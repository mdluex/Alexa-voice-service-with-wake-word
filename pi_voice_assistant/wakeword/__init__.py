"""Wake-word engine factories."""

from __future__ import annotations

from ..config import Settings
from .base import WakeWordEngine
from .openwakeword_engine import OpenWakeWordEngine


def create_wake_engine(settings: Settings) -> WakeWordEngine:
    if settings.wake_engine == "openwakeword":
        return OpenWakeWordEngine(
            model_name=settings.wake_model,
            model_path=settings.openwakeword_model_path,
            threshold=settings.wake_threshold,
        )
    if settings.wake_engine == "porcupine":
        from .porcupine_engine import PorcupineEngine

        return PorcupineEngine(
            access_key=settings.porcupine_access_key or "",
            keyword_paths=settings.porcupine_keyword_paths,
            sensitivities=settings.porcupine_sensitivities,
            builtin_keyword=settings.wake_model,
        )
    raise ValueError(f"Unknown wake engine: {settings.wake_engine}")


__all__ = ["WakeWordEngine", "create_wake_engine"]
