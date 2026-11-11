from __future__ import annotations

from pi_voice_assistant.backends.shell_command import ShellCommandBackend


def test_shell_command_backend_runs(tmp_path) -> None:
    marker = tmp_path / "woke"
    backend = ShellCommandBackend(f"touch '{marker}'")
    backend.on_wake("alexa")
    assert marker.is_file()
