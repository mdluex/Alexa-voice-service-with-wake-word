"""Modern conversation backend: listen, transcribe, reply, speak.

Default path after Amazon archived the AVS Device SDK. Uses:
- local microphone capture
- SpeechRecognition (Google Web Speech by default; no API key required)
- built-in replies, optionally upgraded with OpenAI when OPENAI_API_KEY is set
- espeak-ng (or TTS_COMMAND) for speech output
"""

from __future__ import annotations

import json
import logging
import tempfile
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

from ..audio_io import record_seconds, speak_text, write_wav
from ..config import Settings
from .base import AssistantBackend

logger = logging.getLogger(__name__)


class ConversationBackend(AssistantBackend):
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def on_wake(self, keyword: str) -> None:
        logger.info("Wake word %r -> listening for command", keyword)
        speak_text("Yes?", self.settings.tts_command)

        try:
            pcm = record_seconds(
                self.settings.listen_seconds,
                sample_rate=self.settings.sample_rate,
                device=self.settings.audio_device,
            )
        except Exception:
            logger.exception("Failed to record utterance")
            speak_text("I could not hear you.", self.settings.tts_command)
            return

        transcript = self._transcribe(pcm)
        if not transcript:
            speak_text("Sorry, I did not catch that.", self.settings.tts_command)
            return

        logger.info("Heard: %s", transcript)
        reply = self._respond(transcript)
        logger.info("Reply: %s", reply)
        speak_text(reply, self.settings.tts_command)

    def _transcribe(self, pcm: bytes) -> str:
        try:
            import speech_recognition as sr
        except ImportError:
            logger.error("SpeechRecognition is not installed")
            return ""

        recognizer = sr.Recognizer()
        with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
            write_wav(Path(tmp.name), pcm, sample_rate=self.settings.sample_rate)
            with sr.AudioFile(tmp.name) as source:
                audio = recognizer.record(source)

        try:
            return recognizer.recognize_google(audio)
        except sr.UnknownValueError:
            return ""
        except sr.RequestError:
            logger.exception("Speech recognition request failed")
            return ""

    def _respond(self, transcript: str) -> str:
        local = local_intent_reply(transcript)
        if local is not None:
            return local
        if self.settings.openai_api_key:
            try:
                return openai_chat_reply(
                    transcript,
                    api_key=self.settings.openai_api_key,
                    model=self.settings.openai_model,
                )
            except Exception:
                logger.exception("OpenAI request failed; falling back")
        return (
            f"I heard: {transcript}. "
            "Set OPENAI_API_KEY for richer answers, or ask for the time or date."
        )


def local_intent_reply(transcript: str) -> str | None:
    """Handle a few offline-friendly intents without an LLM."""
    text = transcript.strip().lower()
    if not text:
        return None

    if any(phrase in text for phrase in ("what time", "the time", "current time")):
        return datetime.now().strftime("It is %I:%M %p.")
    if any(phrase in text for phrase in ("what day", "what date", "today's date", "the date")):
        return datetime.now().strftime("Today is %A, %B %d, %Y.")
    if text in {"hello", "hi", "hey"} or text.startswith("hello") or text.startswith("hi "):
        return "Hello! How can I help?"
    if "your name" in text or "who are you" in text:
        return "I am a local Raspberry Pi voice assistant with a wake word."
    if "weather" in text:
        return _weather_reply()
    return None


def _weather_reply() -> str:
    """Best-effort weather summary via wttr.in (no API key)."""
    try:
        with urllib.request.urlopen("https://wttr.in/?format=3", timeout=5) as response:
            body = response.read().decode("utf-8", errors="replace").strip()
            if body:
                return body
    except (urllib.error.URLError, TimeoutError):
        logger.warning("Weather lookup failed")
    return "I could not reach the weather service right now."


def openai_chat_reply(transcript: str, api_key: str, model: str) -> str:
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a concise voice assistant on a Raspberry Pi. "
                    "Keep answers under two short sentences."
                ),
            },
            {"role": "user", "content": transcript},
        ],
    }
    request = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"].strip()


__all__ = [
    "ConversationBackend",
    "local_intent_reply",
    "openai_chat_reply",
]
