"""Run a configurable shell command when the wake word is detected."""

from __future__ import annotations

import logging
import subprocess

from .base import AssistantBackend

logger = logging.getLogger(__name__)


class ShellCommandBackend(AssistantBackend):
    def __init__(self, command: str) -> None:
        self.command = command

    def on_wake(self, keyword: str) -> None:
        logger.info("Wake word %r -> running shell command", keyword)
        completed = subprocess.run(self.command, shell=True, check=False)
        if completed.returncode != 0:
            logger.error("Shell command exited with %s", completed.returncode)
