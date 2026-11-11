from __future__ import annotations

import os
from pathlib import Path

import pytest

from pi_voice_assistant.config import Settings


def test_default_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in list(os.environ):
        if key.startswith(
            (
                "WAKE_",
                "BACKEND",
                "PORCUPINE_",
                "AVS_",
                "SHELL_",
                "OPENAI_",
                "AUDIO_",
                "SAMPLE_",
                "LISTEN_",
                "TTS_",
                "PLAY_",
                "STARTUP_",
                "OPENWAKEWORD_",
                "REFRACTORY_",
            )
        ):
            monkeypatch.delenv(key, raising=False)

    settings = Settings.from_env()
    assert settings.wake_engine == "openwakeword"
    assert settings.wake_model == "alexa"
    assert settings.backend == "conversation"
    settings.validate()


def test_validate_porcupine_requires_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WAKE_ENGINE", "porcupine")
    monkeypatch.delenv("PORCUPINE_ACCESS_KEY", raising=False)
    settings = Settings.from_env()
    with pytest.raises(ValueError, match="PORCUPINE_ACCESS_KEY"):
        settings.validate()


def test_validate_avs_requires_script(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BACKEND", "avs")
    monkeypatch.delenv("AVS_START_SCRIPT", raising=False)
    settings = Settings.from_env()
    with pytest.raises(ValueError, match="AVS_START_SCRIPT"):
        settings.validate()


def test_validate_command_requires_shell(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BACKEND", "command")
    monkeypatch.delenv("SHELL_COMMAND", raising=False)
    settings = Settings.from_env()
    with pytest.raises(ValueError, match="SHELL_COMMAND"):
        settings.validate()


def test_porcupine_sensitivity_mismatch(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    keyword = tmp_path / "alexa_raspberry-pi.ppn"
    keyword.write_bytes(b"fake")
    monkeypatch.setenv("WAKE_ENGINE", "porcupine")
    monkeypatch.setenv("PORCUPINE_ACCESS_KEY", "test-key")
    monkeypatch.setenv("PORCUPINE_KEYWORD_PATHS", str(keyword))
    monkeypatch.setenv("PORCUPINE_SENSITIVITIES", "0.5,0.6")
    settings = Settings.from_env()
    with pytest.raises(ValueError, match="length must match"):
        settings.validate()
