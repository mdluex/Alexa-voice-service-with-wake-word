# Real Amazon Alexa on a Raspberry Pi

Turn a Raspberry Pi into a **genuine Alexa Built-in device**: wake on **“Alexa”**, talk to Amazon’s Alexa Voice Service, and manage the device from the official Alexa mobile app after Login with Amazon authorization.

## One-command install

```bash
curl -fsSL https://raw.githubusercontent.com/mdluex/Alexa-voice-service-with-wake-word/main/install.sh | bash
```

Or, after cloning:

```bash
git clone https://github.com/mdluex/Alexa-voice-service-with-wake-word.git
cd Alexa-voice-service-with-wake-word
./install.sh
```

`./install.sh` installs system packages, the wake-word daemon, builds the **latest AVS Device SDK release (`v3.0.0`) SampleApp** using Amazon’s official Raspberry Pi install scripts, writes `/etc/pi-voice-assistant/config.env`, walks you through Amazon authorization, and enables the systemd start-on-boot service.

**Interactive only where Amazon requires it:**

1. Paste / provide AVS `config.json` (or Client ID + Product ID from the Amazon developer console)
2. Complete Login with Amazon Code-Based Linking in a browser (`https://amazon.com/us/code`)

## Official Amazon / AVS Device SDK docs (primary guide)

This project follows Amazon’s AVS Device SDK documentation and Raspberry Pi quick starts:

| Resource | URL |
| --- | --- |
| **AVS Device SDK docs (API / overview)** | https://alexa.github.io/avs-device-sdk/ |
| **SDK wiki Home** | https://github.com/alexa/avs-device-sdk/wiki/Home/66a5d4ef1b19a1faf1fede5ecb922a18426a6938 |
| **Raspberry Pi Quick Start Guide with Script** | https://github.com/alexa/avs-device-sdk/wiki/Raspberry-Pi-Quick-Start-Guide-with-Script |
| **Raspberry Pi Quick Start Guide (manual)** | https://github.com/alexa/avs-device-sdk/wiki/Raspberry-Pi-Quick-Start-Guide |
| **SDK source / releases** | https://github.com/alexa/avs-device-sdk (latest release **v3.0.0**) |

> **Amazon availability:** The public AVS landing page states that AVS developer tools are [no longer generally available](https://developer.amazon.com/en-US/alexa/alexa-voice-service) for new Alexa Built-in products, and the GitHub SDK is [archived](https://github.com/alexa/avs-device-sdk) (2024-01-16). This repo still targets the latest published SDK release (**v3.0.0**) and the wiki Raspberry Pi scripts because that remains the closest official path that yields a **real Alexa** on a Pi. New developer-console registrations may fail — details in [`docs/AMAZON_AVS.md`](docs/AMAZON_AVS.md).

## What this is

| Piece | Choice |
| --- | --- |
| Wake word | openWakeWord (`alexa`) — free/open; Porcupine optional (paid) |
| Voice assistant | **Amazon AVS Device SDK SampleApp v3.0.0** (default) |
| Boot | systemd `pi-voice-assistant.service` |
| Config | `/etc/pi-voice-assistant/config.env` (no secrets in git) |

On wake, the daemon sends tap-to-talk (`t`) to SampleApp (same interaction model as the SampleApp console). SampleApp streams audio to Alexa and plays the reply. After CBL authorization (wiki “Authorize and run”), the device is linked to your Amazon account.

Optional fallbacks (`BACKEND=conversation` or `command`) exist for bring-up without AVS; they are **not** real Alexa.

## Hardware

Aligned with the SDK wiki Raspberry Pi guides (updated for current boards):

- Raspberry Pi 3 / 4 / 5 (Bookworm 64-bit recommended; Pi 4/5 preferred)
- USB microphone (or capture HAT)
- Speaker (3.5 mm, HDMI, or USB)
- Network connection

## Amazon developer console (before or during install)

Full step-by-step: [`docs/AMAZON_AVS.md`](docs/AMAZON_AVS.md). Summary from the wiki registration flow:

1. Sign in at [developer.amazon.com](https://developer.amazon.com/)
2. If still available to your account, register an AVS / Alexa Built-in product and Login with Amazon security profile
3. Download `config.json` in the official shape:

```json
{
  "deviceInfo": {
    "clientId": "amzn1.application-oa2-client....",
    "productId": "YourProductId"
  }
}
```

4. Run `./install.sh` and point it at that file (or paste the IDs when prompted)
5. When SampleApp shows a code, open [amazon.com/us/code](https://amazon.com/us/code), Allow, wait until Alexa is idle
6. Use the [Alexa app](https://www.amazon.com/alexa-app/b?ie=UTF8&node=18354642011) / [alexa.amazon.com](https://alexa.amazon.com/) with the same Amazon account

Related Amazon pages:

- [Alexa Built-in / AVS overview](https://developer.amazon.com/en-US/alexa/alexa-voice-service) (“no longer generally available” notice)
- [AVS FAQs](https://developer.amazon.com/en-US/docs/alexa/alexa-voice-service/faqs.html)
- [Works with Alexa](https://developer.amazon.com/en-US/alexa/works-with-alexa) — **not** Alexa Built-in; for devices Alexa controls

## Configuration

Primary file: `/etc/pi-voice-assistant/config.env` (see [`config.example.env`](config.example.env)).

| Variable | Default | Purpose |
| --- | --- | --- |
| `BACKEND` | `avs` | `avs` (real Alexa), optional `conversation` / `command` |
| `AVS_START_SCRIPT` | `~/avs-sdk/startsample.sh` | SampleApp launcher from `install-avs-sdk.sh` |
| `WAKE_ENGINE` | `openwakeword` | `openwakeword` or `porcupine` |
| `WAKE_MODEL` | `alexa` | openWakeWord model name |
| `WAKE_THRESHOLD` | `0.5` | Detection threshold |
| `AUDIO_DEVICE` | default mic | From `--list-audio-devices` |

## Manual / advanced commands

```bash
# Python daemon only (no AVS build)
./scripts/install.sh

# Build SampleApp from an existing config.json (pins SDK v3.0.0)
./scripts/install-avs-sdk.sh /secure/path/to/config.json

# One-time Amazon authorization (wiki CBL flow)
./scripts/authorize-avs.sh

# Enable/restart boot service
./scripts/install-service.sh

# Validate config
source ~/.venvs/pi-voice-assistant/bin/activate
export PYTHONPATH="$PWD"
python -m pi_voice_assistant --env-file /etc/pi-voice-assistant/config.env --validate-config
```

Installer knobs: `SKIP_AVS_BUILD=1`, `SKIP_AUTHORIZE=1`, `SKIP_SERVICE=1`, `AVS_DIR=...`, `AVS_SDK_VERSION=v3.0.0`, `AVS_CONFIG_JSON=/path/to/config.json`.

## Project layout

```
install.sh                 One-command installer
pi_voice_assistant/        Wake-word daemon (Python)
scripts/                   install.sh, install-avs-sdk.sh, authorize-avs.sh, install-service.sh
systemd/                   service unit template
docs/AMAZON_AVS.md         Amazon console + AVS status + wiki citations
assets/startup.wav         Ready chime
config.example.env         Config template
tests/                     Unit tests
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

| Symptom | Check |
| --- | --- |
| Console won’t create an AVS product | Amazon closed new AVS tools; see `docs/AMAZON_AVS.md` |
| SampleApp build fails on Bookworm | SDK unmaintained since 2024; inspect `~/avs-sdk` build logs; `PLATFORM="Raspberry pi"` is forced by the installer |
| NOT YET AUTHORIZED | Run `./scripts/authorize-avs.sh` and finish `amazon.com/us/code` (wiki Authorize and run) |
| No wake detections | `arecord -l`, `--list-audio-devices`, lower `WAKE_THRESHOLD` |
| Service fails | `sudo journalctl -u pi-voice-assistant -xe`; user in `audio` group |

## Limitations

- Not an Amazon-certified commercial Alexa Built-in product.
- Depends on the **archived** AVS Device SDK **v3.0.0** (latest release); builds and cloud access are best-effort.
- New AVS product registration may be impossible.
- First authorization must use a browser (Amazon CBL), per the official SampleApp flow.
- Hardware, Amazon credentials, SampleApp build, CBL, and Alexa-app visibility were **not** verified in the cloud agent environment used to prepare this repo.

## License

MIT — see [LICENSE](LICENSE).
