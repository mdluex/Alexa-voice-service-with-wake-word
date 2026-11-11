# Alexa-style Voice Assistant for Raspberry Pi

A wake-word voice assistant for Raspberry Pi OS. Say a wake word (default **“Alexa”**), then speak a short request and get a spoken reply.

This repository modernizes the 2022 project that glued [Picovoice Porcupine](https://picovoice.ai/) to Amazon’s AVS Device SDK SampleApp. That stack is no longer a viable default in 2026:

| Component (2022) | Status in 2026 | Replacement in this repo |
| --- | --- | --- |
| Amazon AVS Device SDK / SampleApp | [Archived](https://github.com/alexa/avs-device-sdk) (2024-01-16). AVS tools are not generally available for new Alexa Built-in devices. | Default **conversation** backend (local listen → STT → reply → TTS). Optional legacy `BACKEND=avs` for existing SampleApp installs only. |
| Picovoice Porcupine | Still maintained, but **free-tier AccessKeys stopped working after 2026-06-30**. | Default wake engine: **openWakeWord** via [`pyopen-wakeword`](https://pypi.org/project/pyopen-wakeword/) (includes a built-in `alexa` model, no AccessKey). Optional Porcupine for paid keys. |
| LXDE `autostart` | Not reliable on Bookworm (Wayland / labwc). | **systemd** service |
| Raspberry Pi OS Buster guidance | Obsolete | Raspberry Pi OS **Bookworm**, Python **3.11+** |

## Features

- Always-listening wake word (default: openWakeWord `alexa`)
- Pluggable backends: conversation (default), legacy AVS SampleApp, or a shell command
- Configuration via environment / `config.env` (no secrets committed)
- systemd unit for start-on-boot
- Install script with pinned Python dependencies
- Basic unit tests and GitHub Actions CI (lint + pytest)

## Hardware

- Raspberry Pi 3 / 4 / 5 (Bookworm 64-bit recommended; Pi 4/5 preferred)
- USB microphone (or HAT with capture support)
- Speaker (3.5 mm, HDMI, or USB)
- Network connection (needed for Google Web Speech STT and optional OpenAI / weather)

## Quick start

```bash
git clone https://github.com/mdluex/Alexa-voice-service-with-wake-word.git
cd Alexa-voice-service-with-wake-word
chmod +x scripts/*.sh
./scripts/install.sh
```

Edit configuration:

```bash
sudo nano /etc/pi-voice-assistant/config.env
```

Validate and do a foreground run:

```bash
source ~/.venvs/pi-voice-assistant/bin/activate
export PYTHONPATH="$PWD"
python -m pi_voice_assistant --list-audio-devices
python -m pi_voice_assistant --env-file /etc/pi-voice-assistant/config.env --validate-config
python -m pi_voice_assistant --env-file /etc/pi-voice-assistant/config.env
```

Enable start on boot:

```bash
./scripts/install-service.sh
```

## Configuration

Copy [`config.example.env`](config.example.env) to `config.env` or `/etc/pi-voice-assistant/config.env`. Important variables:

| Variable | Default | Purpose |
| --- | --- | --- |
| `WAKE_ENGINE` | `openwakeword` | `openwakeword` or `porcupine` |
| `WAKE_MODEL` | `alexa` | Built-in openWakeWord model name |
| `WAKE_THRESHOLD` | `0.5` | Detection threshold (0–1) |
| `AUDIO_DEVICE` | *(default mic)* | Device index/name from `--list-audio-devices` |
| `BACKEND` | `conversation` | `conversation`, `avs`, or `command` |
| `LISTEN_SECONDS` | `5.0` | How long to record after wake (conversation) |
| `TTS_COMMAND` | `espeak-ng` | Local TTS binary |
| `OPENAI_API_KEY` | *(unset)* | Optional richer answers |
| `AVS_START_SCRIPT` | *(unset)* | Legacy SampleApp `startsample.sh` |
| `SHELL_COMMAND` | *(unset)* | Command to run when `BACKEND=command` |
| `PORCUPINE_ACCESS_KEY` | *(unset)* | Required only for `WAKE_ENGINE=porcupine` |

Built-in openWakeWord models: `alexa`, `hey_jarvis`, `hey_mycroft`, `okay_nabu`, `hey_rhasspy`.

### Conversation backend

After the wake word:

1. Speaks a short acknowledgment (“Yes?”)
2. Records `LISTEN_SECONDS` of audio
3. Transcribes with SpeechRecognition (Google Web Speech by default)
4. Answers with local intents (time, date, hello, weather) or OpenAI when `OPENAI_API_KEY` is set
5. Speaks the reply through `espeak-ng`

### Legacy AVS backend

Only for machines that already have a working AVS SampleApp:

```env
BACKEND=avs
AVS_START_SCRIPT=/home/pi/sdk-folder/startsample.sh
```

On wake, the daemon writes `t\n` to SampleApp stdin (tap-to-talk). New AVS setups are not supported.

### Optional Porcupine

```bash
INSTALL_PORCUPINE=1 ./scripts/install.sh
```

```env
WAKE_ENGINE=porcupine
PORCUPINE_ACCESS_KEY=your-paid-key
PORCUPINE_KEYWORD_PATHS=/path/to/keyword_raspberry-pi.ppn
PORCUPINE_SENSITIVITIES=0.6
```

The `.ppn` file from the 2022 project lives under [`legacy/`](legacy/) for historical reference. Regenerate keyword models for your Porcupine version before use.

## Project layout

```
pi_voice_assistant/     Python package (daemon, wake engines, backends)
scripts/                install.sh, install-service.sh
systemd/                service unit template
assets/startup.wav      boot / ready chime
config.example.env      configuration template
legacy/                 old Porcupine keyword + notes
tests/                  unit tests
```

## Development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pytest -q
ruff check pi_voice_assistant tests
```

## Troubleshooting

| Symptom | Things to check |
| --- | --- |
| No wake detections | Mic levels (`arecord -l`, `alsamixer`); try `--list-audio-devices` and set `AUDIO_DEVICE`; lower `WAKE_THRESHOLD` slightly (for example `0.4`). |
| Service dies on boot | `sudo journalctl -u pi-voice-assistant -xe`; ensure the service user is in the `audio` group: `sudo usermod -aG audio $USER`. |
| STT always fails | Needs outbound HTTPS for Google Web Speech; check DNS/network. |
| TTS silent | Confirm `espeak-ng` is installed and speakers work (`speaker-test -c2`). |
| Porcupine activation errors | Free-tier keys no longer work; use a paid AccessKey or switch back to `WAKE_ENGINE=openwakeword`. |
| Old LXDE autostart | Remove `@bash ./runAlexa` from any leftover LXDE autostart files; use systemd instead. |

## Limitations

- This is **not** an official Alexa Built-in product. Amazon no longer offers AVS developer tools for new DIY Alexa devices.
- Default speech recognition uses a cloud STT endpoint (Google Web Speech via SpeechRecognition).
- Default TTS (`espeak-ng`) is robotic; swap `TTS_COMMAND` for another local engine if you prefer.
- Conversation quality without `OPENAI_API_KEY` is limited to simple built-in intents.
- Wake-word and full duplex audio were **not** hardware-tested in CI (no Raspberry Pi or Amazon credentials in the modernization environment).

## License

MIT — see [LICENSE](LICENSE).
