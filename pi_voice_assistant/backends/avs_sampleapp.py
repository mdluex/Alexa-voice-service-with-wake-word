"""Amazon AVS Device SDK SampleApp backend (real Alexa Built-in).

This is the closest official Amazon path that turns a Raspberry Pi into a genuine
Alexa Built-in device: the SampleApp authorizes with Login with Amazon (code-based
linking), talks to Alexa Voice Service, and the device is associated with the
owner's Amazon account / Alexa app.

Amazon status (2024–2026):
- AVS Device SDK GitHub repo archived 2024-01-16 (last release v3.0.0, 2022-09-29).
- Amazon states AVS developer tools are "no longer generally available" for new
  Alexa Built-in products and points commercial builders to Works with Alexa
  (smart-home control), which is NOT Alexa Built-in.

This backend starts SampleApp and sends tap-to-talk (`t`) on wake-word detection.
First-time authorization must be done interactively (see scripts/authorize-avs.sh).
"""

from __future__ import annotations

import logging
import os
import subprocess
import time
from pathlib import Path

from .base import AssistantBackend

logger = logging.getLogger(__name__)


class AvsSampleAppBackend(AssistantBackend):
    """Drive Amazon's SampleApp for real Alexa responses."""

    def __init__(
        self,
        start_script: Path,
        working_directory: Path | None = None,
        log_directory: Path | None = None,
    ) -> None:
        self.start_script = Path(start_script).expanduser()
        self.working_directory = (
            Path(working_directory).expanduser()
            if working_directory is not None
            else self.start_script.parent
        )
        self.log_directory = (
            Path(log_directory).expanduser()
            if log_directory is not None
            else self.working_directory / "logs"
        )
        self._process: subprocess.Popen[bytes] | None = None
        self._stdout_handle = None
        self._stderr_handle = None

    def start(self) -> None:
        if not self.start_script.is_file():
            raise FileNotFoundError(
                f"AVS SampleApp start script not found: {self.start_script}\n"
                "Build the archived AVS Device SDK SampleApp first:\n"
                "  ./scripts/install-avs-sdk.sh /path/to/config.json\n"
                "Then authorize once interactively:\n"
                "  ./scripts/authorize-avs.sh\n"
                "See docs/AMAZON_AVS.md for Amazon developer console steps."
            )
        if not os.access(self.start_script, os.X_OK):
            raise PermissionError(
                f"AVS start script is not executable: {self.start_script}\n"
                f"Run: chmod +x {self.start_script}"
            )

        self.log_directory.mkdir(parents=True, exist_ok=True)
        stdout_path = self.log_directory / "sampleapp.stdout.log"
        stderr_path = self.log_directory / "sampleapp.stderr.log"
        self._stdout_handle = open(stdout_path, "ab", buffering=0)
        self._stderr_handle = open(stderr_path, "ab", buffering=0)

        logger.info(
            "Starting Amazon AVS SampleApp (%s). "
            "If this is the first run, authorize with Code-Based Linking "
            "(see scripts/authorize-avs.sh). Logs: %s",
            self.start_script,
            self.log_directory,
        )
        env = os.environ.copy()
        # SampleApp historically needed this for ALSA plug devices on Pi.
        env.setdefault("PA_ALSA_PLUGHW", "1")

        self._process = subprocess.Popen(
            [str(self.start_script)],
            stdin=subprocess.PIPE,
            stdout=self._stdout_handle,
            stderr=self._stderr_handle,
            cwd=str(self.working_directory),
            env=env,
        )
        # Give SampleApp a moment to boot before accepting wake events.
        time.sleep(1.0)
        if self._process.poll() is not None:
            raise RuntimeError(
                "AVS SampleApp exited immediately after start. "
                f"Inspect {stdout_path} and {stderr_path}. "
                "If you see NOT YET AUTHORIZED, run ./scripts/authorize-avs.sh "
                "in a foreground terminal and complete amazon.com/us/code linking."
            )

    def on_wake(self, keyword: str) -> None:
        if self._process is None or self._process.stdin is None:
            raise RuntimeError("AVS SampleApp is not running")
        if self._process.poll() is not None:
            raise RuntimeError(
                "AVS SampleApp exited unexpectedly. Check SampleApp logs under "
                f"{self.log_directory}."
            )

        logger.info(
            "Wake word %r -> tap-to-talk on Amazon AVS SampleApp (real Alexa)",
            keyword,
        )
        self._process.stdin.write(b"t\n")
        self._process.stdin.flush()
        time.sleep(0.25)

    def close(self) -> None:
        try:
            if self._process is not None:
                if self._process.poll() is None and self._process.stdin is not None:
                    try:
                        self._process.stdin.write(b"q\n")
                        self._process.stdin.flush()
                        time.sleep(0.25)
                    except BrokenPipeError:
                        pass
                    self._process.terminate()
                    try:
                        self._process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        self._process.kill()
        except Exception:  # pragma: no cover - best-effort shutdown
            logger.exception("Failed to stop AVS SampleApp cleanly")
            if self._process is not None:
                self._process.kill()
        finally:
            self._process = None
            for handle in (self._stdout_handle, self._stderr_handle):
                if handle is not None:
                    try:
                        handle.close()
                    except Exception:  # pragma: no cover
                        pass
            self._stdout_handle = None
            self._stderr_handle = None
