"""Main wake-word daemon loop."""

from __future__ import annotations

import logging
import signal
import time

from .audio_io import MicrophoneStream, play_wav
from .backends import create_backend
from .config import Settings
from .wakeword import create_wake_engine

logger = logging.getLogger(__name__)


class VoiceAssistantDaemon:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._stop = False

    def request_stop(self, *_args) -> None:
        logger.info("Stop requested")
        self._stop = True

    def run(self) -> int:
        self.settings.validate()
        signal.signal(signal.SIGINT, self.request_stop)
        signal.signal(signal.SIGTERM, self.request_stop)

        if self.settings.play_startup_sound:
            play_wav(self.settings.startup_sound)

        with create_wake_engine(self.settings) as engine, create_backend(self.settings) as backend:
            with MicrophoneStream(
                sample_rate=self.settings.sample_rate,
                device=self.settings.audio_device,
            ) as mic:
                logger.info(
                    "Listening for wake word (engine=%s, backend=%s)",
                    self.settings.wake_engine,
                    self.settings.backend,
                )
                last_detection = 0.0
                while not self._stop:
                    chunk = mic.read_chunk()
                    keyword = engine.process(chunk)
                    if not keyword:
                        continue

                    now = time.monotonic()
                    if now - last_detection < self.settings.wake_cooldown_seconds:
                        logger.debug("Ignoring detection during cooldown")
                        continue
                    last_detection = now

                    logger.info("Detected wake word: %s", keyword)
                    try:
                        backend.on_wake(keyword)
                    except Exception:
                        logger.exception("Backend failed while handling wake word")

                    # Brief refractory period so TTS / AVS audio does not re-trigger.
                    time.sleep(self.settings.refractory_seconds)

        logger.info("Daemon stopped")
        return 0


def configure_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def run_from_settings(settings: Settings | None = None, verbose: bool = False) -> int:
    configure_logging(verbose=verbose)
    resolved = settings or Settings.from_env()
    return VoiceAssistantDaemon(resolved).run()
