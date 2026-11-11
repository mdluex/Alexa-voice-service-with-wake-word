"""CLI entrypoint: python -m pi_voice_assistant"""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .config import Settings, load_env_files
from .daemon import configure_logging, run_from_settings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pi-voice-assistant",
        description="Raspberry Pi wake-word daemon for real Amazon Alexa (AVS SampleApp).",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "--env-file",
        action="append",
        default=[],
        help="Optional path to a config.env / .env file (repeatable).",
    )
    parser.add_argument(
        "--list-audio-devices",
        action="store_true",
        help="List sounddevice input devices and exit.",
    )
    parser.add_argument(
        "--validate-config",
        action="store_true",
        help="Load and validate configuration, then exit.",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging.")
    return parser


def list_audio_devices() -> int:
    try:
        import sounddevice as sd
    except ImportError:
        print("sounddevice is not installed", file=sys.stderr)
        return 1

    devices = sd.query_devices()
    for index, device in enumerate(devices):
        if device["max_input_channels"] > 0:
            print(f"{index}: {device['name']} (inputs={device['max_input_channels']})")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    configure_logging(verbose=args.verbose)

    if args.env_file:
        from pathlib import Path

        load_env_files([Path(path) for path in args.env_file])

    if args.list_audio_devices:
        return list_audio_devices()

    settings = Settings.from_env()
    if args.validate_config:
        settings.validate()
        print("Configuration OK")
        print(f"  wake_engine={settings.wake_engine}")
        print(f"  wake_model={settings.wake_model}")
        print(f"  backend={settings.backend}")
        return 0

    return run_from_settings(settings=settings, verbose=args.verbose)


if __name__ == "__main__":
    raise SystemExit(main())
