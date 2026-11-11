"""Assistant backends triggered after a wake-word detection."""

from __future__ import annotations

from ..config import Settings
from .avs_sampleapp import AvsSampleAppBackend
from .base import AssistantBackend
from .conversation import ConversationBackend
from .shell_command import ShellCommandBackend


def create_backend(settings: Settings) -> AssistantBackend:
    if settings.backend == "avs":
        assert settings.avs_start_script is not None
        return AvsSampleAppBackend(
            start_script=settings.avs_start_script,
            working_directory=settings.avs_working_directory,
            log_directory=settings.avs_log_directory,
        )
    if settings.backend == "conversation":
        return ConversationBackend(settings)
    if settings.backend == "command":
        assert settings.shell_command is not None
        return ShellCommandBackend(settings.shell_command)
    raise ValueError(f"Unknown backend: {settings.backend}")


__all__ = ["AssistantBackend", "create_backend"]
