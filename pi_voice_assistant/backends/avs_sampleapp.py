"""Legacy Amazon AVS Device SDK SampleApp backend.

The AVS Device SDK repository was archived on 2024-01-16 and Amazon states that
AVS developer tools are no longer generally available for new Alexa Built-in
projects. This backend remains only for existing installs that still have a
working SampleApp and tap-to-talk (`t` on stdin).
"""

from __future__ import annotations

import logging
import subprocess
import time
from pathlib import Path

from .base import AssistantBackend

logger = logging.getLogger(__name__)


class AvsSampleAppBackend(AssistantBackend):
    def __init__(self, start_script: Path) -> None:
        self.start_script = Path(start_script)
        self._process: subprocess.Popen[bytes] | None = None

    def start(self) -> None:
        if not self.start_script.is_file():
            raise FileNotFoundError(
                f"AVS start script not found: {self.start_script}. "
                "The AVS Device SDK is archived; this backend is for legacy installs only."
            )
        if not self.start_script.stat().st_mode & 0o111:
            raise PermissionError(
                f"AVS start script is not executable: {self.start_script}"
            )

        logger.warning(
            "Starting legacy AVS SampleApp (%s). This path is deprecated and may stop working.",
            self.start_script,
        )
        self._process = subprocess.Popen(
            [str(self.start_script)],
            stdin=subprocess.PIPE,
            cwd=str(self.start_script.parent),
        )

    def on_wake(self, keyword: str) -> None:
        if self._process is None or self._process.stdin is None:
            raise RuntimeError("AVS SampleApp is not running")
        if self._process.poll() is not None:
            raise RuntimeError("AVS SampleApp exited unexpectedly")

        logger.info("Wake word %r -> sending tap-to-talk to AVS SampleApp", keyword)
        self._process.stdin.write(b"t\n")
        self._process.stdin.flush()
        time.sleep(0.25)

    def close(self) -> None:
        if self._process is None:
            return
        try:
            if self._process.poll() is None and self._process.stdin is not None:
                self._process.stdin.write(b"q\n")
                self._process.stdin.flush()
                time.sleep(0.25)
                self._process.terminate()
                self._process.wait(timeout=5)
        except Exception:  # pragma: no cover - best-effort shutdown
            logger.exception("Failed to stop AVS SampleApp cleanly")
            self._process.kill()
        finally:
            self._process = None
