from __future__ import annotations

from pathlib import Path

from pi_voice_assistant.backends.conversation import local_intent_reply
from pi_voice_assistant.wakeword.porcupine_engine import _label_from_path


def test_time_intent() -> None:
    reply = local_intent_reply("what time is it")
    assert reply is not None
    assert "It is" in reply


def test_date_intent() -> None:
    reply = local_intent_reply("what is today's date")
    assert reply is not None
    assert "Today is" in reply


def test_hello_intent() -> None:
    assert local_intent_reply("hello there") == "Hello! How can I help?"


def test_unknown_intent_returns_none() -> None:
    assert local_intent_reply("play some jazz music please") is None


def test_porcupine_label_from_path() -> None:
    path = Path("alexa_en_raspberry-pi_v2_1_0.ppn")
    assert _label_from_path(path) == "alexa"
