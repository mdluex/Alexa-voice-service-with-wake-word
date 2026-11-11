"""Assistant backend interface."""

from __future__ import annotations

from abc import ABC, abstractmethod


class AssistantBackend(ABC):
    def start(self) -> None:
        """Optional warm-up when the daemon starts."""
        return None

    @abstractmethod
    def on_wake(self, keyword: str) -> None:
        """Handle a wake-word detection."""

    def close(self) -> None:
        """Release resources."""
        return None

    def __enter__(self) -> AssistantBackend:
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
