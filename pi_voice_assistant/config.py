"""Configuration loaded from environment variables and optional .env files."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional at import time for unit tests
    load_dotenv = None


PACKAGE_ROOT = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_ROOT.parent
DEFAULT_ENV_PATHS = (
    Path.cwd() / ".env",
    Path.cwd() / "config.env",
    REPO_ROOT / ".env",
    REPO_ROOT / "config.env",
    Path("/etc/pi-voice-assistant/config.env"),
)


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return float(value)


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return int(value)


def load_env_files(extra_paths: list[Path] | None = None) -> list[Path]:
    """Load the first existing dotenv files without overriding real env vars."""
    if load_dotenv is None:
        return []

    loaded: list[Path] = []
    seen: set[Path] = set()
    candidates = list(DEFAULT_ENV_PATHS)
    if extra_paths:
        candidates = list(extra_paths) + candidates

    for path in candidates:
        resolved = path.expanduser().resolve()
        if resolved in seen or not resolved.is_file():
            continue
        load_dotenv(resolved, override=False)
        loaded.append(resolved)
        seen.add(resolved)
    return loaded


@dataclass(frozen=True)
class Settings:
    """Runtime settings for the voice assistant daemon."""

    wake_engine: str = "openwakeword"
    wake_model: str = "alexa"
    wake_threshold: float = 0.5
    wake_cooldown_seconds: float = 2.0
    audio_device: str | None = None
    sample_rate: int = 16000
    backend: str = "conversation"
    startup_sound: Path = field(default_factory=lambda: REPO_ROOT / "assets" / "startup.wav")
    play_startup_sound: bool = True

    # openWakeWord / custom model
    openwakeword_model_path: Path | None = None

    # Optional Porcupine (paid AccessKey required as of mid-2026)
    porcupine_access_key: str | None = None
    porcupine_keyword_paths: tuple[Path, ...] = ()
    porcupine_sensitivities: tuple[float, ...] = (0.5,)

    # Backends
    avs_start_script: Path | None = None
    shell_command: str | None = None
    listen_seconds: float = 5.0
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    tts_command: str = "espeak-ng"
    refractory_seconds: float = 1.5

    @classmethod
    def from_env(cls) -> Settings:
        load_env_files()

        keyword_paths_raw = os.getenv("PORCUPINE_KEYWORD_PATHS", "").strip()
        keyword_paths = tuple(
            Path(part.strip()).expanduser()
            for part in keyword_paths_raw.split(":")
            if part.strip()
        )

        sensitivities_raw = os.getenv("PORCUPINE_SENSITIVITIES", "").strip()
        if sensitivities_raw:
            sensitivities = tuple(float(part.strip()) for part in sensitivities_raw.split(","))
        elif keyword_paths:
            sensitivities = tuple(0.5 for _ in keyword_paths)
        else:
            sensitivities = (0.5,)

        startup_sound = Path(
            os.getenv("STARTUP_SOUND", str(REPO_ROOT / "assets" / "startup.wav"))
        ).expanduser()

        model_path_raw = os.getenv("OPENWAKEWORD_MODEL_PATH", "").strip()
        avs_script_raw = os.getenv("AVS_START_SCRIPT", "").strip()
        audio_device = os.getenv("AUDIO_DEVICE", "").strip() or None

        return cls(
            wake_engine=os.getenv("WAKE_ENGINE", "openwakeword").strip().lower(),
            wake_model=os.getenv("WAKE_MODEL", "alexa").strip().lower(),
            wake_threshold=_env_float("WAKE_THRESHOLD", 0.5),
            wake_cooldown_seconds=_env_float("WAKE_COOLDOWN_SECONDS", 2.0),
            audio_device=audio_device,
            sample_rate=_env_int("SAMPLE_RATE", 16000),
            backend=os.getenv("BACKEND", "conversation").strip().lower(),
            startup_sound=startup_sound,
            play_startup_sound=_env_bool("PLAY_STARTUP_SOUND", True),
            openwakeword_model_path=Path(model_path_raw).expanduser() if model_path_raw else None,
            porcupine_access_key=os.getenv("PORCUPINE_ACCESS_KEY") or None,
            porcupine_keyword_paths=keyword_paths,
            porcupine_sensitivities=sensitivities,
            avs_start_script=Path(avs_script_raw).expanduser() if avs_script_raw else None,
            shell_command=os.getenv("SHELL_COMMAND") or None,
            listen_seconds=_env_float("LISTEN_SECONDS", 5.0),
            openai_api_key=os.getenv("OPENAI_API_KEY") or None,
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip(),
            tts_command=os.getenv("TTS_COMMAND", "espeak-ng").strip(),
            refractory_seconds=_env_float("REFRACTORY_SECONDS", 1.5),
        )

    def validate(self) -> None:
        if self.wake_engine not in {"openwakeword", "porcupine"}:
            raise ValueError(
                f"Unsupported WAKE_ENGINE={self.wake_engine!r}. "
                "Use 'openwakeword' (default) or 'porcupine'."
            )
        if self.backend not in {"conversation", "avs", "command"}:
            raise ValueError(
                f"Unsupported BACKEND={self.backend!r}. "
                "Use 'conversation', 'avs', or 'command'."
            )
        if not 0.0 < self.wake_threshold <= 1.0:
            raise ValueError("WAKE_THRESHOLD must be between 0 and 1.")
        if self.wake_engine == "porcupine":
            if not self.porcupine_access_key:
                raise ValueError(
                    "PORCUPINE_ACCESS_KEY is required when WAKE_ENGINE=porcupine. "
                    "Picovoice ended free-tier AccessKeys on 2026-06-30; a paid key is required."
                )
            if self.porcupine_keyword_paths and len(self.porcupine_keyword_paths) != len(
                self.porcupine_sensitivities
            ):
                raise ValueError(
                    "PORCUPINE_KEYWORD_PATHS and PORCUPINE_SENSITIVITIES length must match."
                )
        if self.backend == "avs" and not self.avs_start_script:
            raise ValueError("AVS_START_SCRIPT is required when BACKEND=avs.")
        if self.backend == "command" and not self.shell_command:
            raise ValueError("SHELL_COMMAND is required when BACKEND=command.")
