from __future__ import annotations

import os
from pathlib import Path

import pytest

from pi_voice_assistant.backends.avs_sampleapp import AvsSampleAppBackend


def test_missing_start_script_raises(tmp_path: Path) -> None:
    missing = tmp_path / "startsample.sh"
    backend = AvsSampleAppBackend(missing)
    with pytest.raises(FileNotFoundError, match="install-avs-sdk"):
        backend.start()


def test_non_executable_start_script_raises(tmp_path: Path) -> None:
    script = tmp_path / "startsample.sh"
    script.write_text("#!/bin/sh\nread line\n")
    os.chmod(script, 0o644)
    backend = AvsSampleAppBackend(script)
    with pytest.raises(PermissionError, match="not executable"):
        backend.start()


def test_tap_to_talk_writes_t(tmp_path: Path) -> None:
    script = tmp_path / "startsample.sh"
    # Keep stdin open until we send q / terminate.
    script.write_text("#!/bin/sh\nwhile read -r line; do echo \"$line\"; done\n")
    os.chmod(script, 0o755)

    backend = AvsSampleAppBackend(script, log_directory=tmp_path / "logs")
    backend.start()
    try:
        assert backend._process is not None
        backend.on_wake("alexa")
    finally:
        backend.close()

    log = (tmp_path / "logs" / "sampleapp.stdout.log").read_text(encoding="utf-8", errors="replace")
    assert "t" in log
