from __future__ import annotations

from pi_voice_assistant import __version__
from pi_voice_assistant.__main__ import build_parser, main


def test_version_flag(capsys) -> None:
    parser = build_parser()
    try:
        parser.parse_args(["--version"])
    except SystemExit as exc:
        assert exc.code == 0
    captured = capsys.readouterr()
    assert __version__ in captured.out


def test_validate_config_ok(monkeypatch, capsys) -> None:
    monkeypatch.setenv("WAKE_ENGINE", "openwakeword")
    monkeypatch.setenv("BACKEND", "conversation")
    assert main(["--validate-config"]) == 0
    out = capsys.readouterr().out
    assert "Configuration OK" in out
