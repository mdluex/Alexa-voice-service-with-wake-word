# Real Amazon Alexa on a Raspberry Pi (official path & limits)

**Simplest install:** from the repo root run `./install.sh`, or:

```bash
curl -fsSL https://raw.githubusercontent.com/mdluex/Alexa-voice-service-with-wake-word/main/install.sh | bash
```

That single command installs dependencies, builds the **latest AVS Device SDK release (`v3.0.0`) SampleApp**, configures systemd, and only pauses for Amazon Client ID / Product ID (or `config.json`) and Login with Amazon authorization.

## Primary official documentation

Follow these first (owner-provided / SDK wiki):

1. **[AVS Device SDK documentation](https://alexa.github.io/avs-device-sdk/)** — what AVS is, SampleApp, platforms (including Raspberry Pi), security requirements, API references.
2. **[AVS Device SDK wiki Home](https://github.com/alexa/avs-device-sdk/wiki/Home/66a5d4ef1b19a1faf1fede5ecb922a18426a6938)** — overview, build platforms, links into Raspberry Pi / Linux / macOS guides.
3. **[Raspberry Pi Quick Start Guide with Script](https://github.com/alexa/avs-device-sdk/wiki/Raspberry-Pi-Quick-Start-Guide-with-Script)** — `setup.sh` / `pi.sh` / `config` flow used by `scripts/install-avs-sdk.sh`.
4. **[Raspberry Pi Quick Start Guide](https://github.com/alexa/avs-device-sdk/wiki/Raspberry-Pi-Quick-Start-Guide)** — manual register → dependencies → cmake/make SampleApp → `genConfig.sh` → authorize.

**SDK release used by this repo:** [v3.0.0](https://github.com/alexa/avs-device-sdk/releases/tag/v3.0.0) (latest GitHub release; published 2022-09-29).

## What Amazon says about availability today

Amazon’s Alexa Built-in / AVS landing page states:

> Alexa Voice Service (AVS) developer tools are no longer generally available for Alexa Built-in. Please visit the Works with Alexa program if you are interested in building devices that connect to Alexa.

Sources:

- [Alexa Built-in / AVS overview](https://developer.amazon.com/en-US/alexa/alexa-voice-service)
- [Alexa Built-in devices](https://developer.amazon.com/en-US/alexa/devices/alexa-built-in)
- [AVS FAQs](https://developer.amazon.com/en-US/docs/alexa/alexa-voice-service/faqs.html)

The open-source SDK itself is archived and unmaintained:

- GitHub: [alexa/avs-device-sdk](https://github.com/alexa/avs-device-sdk) — archived **2024-01-16**

### Works with Alexa is not a substitute

[Works with Alexa](https://developer.amazon.com/en-US/alexa/works-with-alexa) / [Alexa Connect Kit](https://developer.amazon.com/en-US/docs/alexa/ack-sdk/overview.html) let Alexa **control** a product (lights, plugs, appliances). They do **not** turn the Pi’s microphone/speaker into Alexa Built-in ([Amazon’s Built-in vs Works with Alexa FAQ](https://www.amazon.com/b?ie=UTF8&node=23560784011)).

**Closest official Amazon-supported route that still yields a real Alexa on the Pi:** build and run the latest AVS Device SDK release SampleApp (`v3.0.0`) per the wiki Raspberry Pi guides, using credentials from an AVS / Alexa Built-in product registration **if** the developer console still allows your account to create or reuse that product.

## What you must do in the Amazon developer console

From the wiki Raspberry Pi Quick Start Guide (“Register your product with Amazon”):

1. Create / sign in to an [Amazon developer account](https://developer.amazon.com/).
2. Open the Alexa Voice Service / Alexa Built-in product console (if still accessible to your account).
3. Register an AVS product / create a Login with Amazon security profile.
4. Download **`config.json`**. Official shape expected by `genConfig.sh` / this installer:

```json
{
  "deviceInfo": {
    "clientId": "amzn1.application-oa2-client.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "productId": "PrototypePi"
  }
}
```

5. Keep `config.json` private (this repo gitignores it).

If the console refuses new AVS / Alexa Built-in products, Amazon has closed the path for your account. There is no other public Amazon DIY path that produces a microphone Alexa Built-in device on a Pi.

## Build SampleApp on the Pi

```bash
# After ./scripts/install.sh (or just use ./install.sh for everything)
./scripts/install-avs-sdk.sh /secure/path/to/config.json
```

This:

1. Fetches Amazon’s `setup.sh`, `pi.sh`, and `genConfig.sh` from tag **`v3.0.0`**
2. Patches the clone step to `git clone --branch v3.0.0` (latest release)
3. Forces `PLATFORM="Raspberry pi"` for Bookworm/`ID=debian`
4. Runs the wiki script installer (`printf AGREE | setup.sh config.json`)

Override the tag only if you know you need another release: `AVS_SDK_VERSION=v3.0.0`.

## Authorize so the device appears for your Amazon account

```bash
./scripts/authorize-avs.sh
```

When SampleApp prints **NOT YET AUTHORIZED** and a code (wiki “Authorize and run”):

1. Open [https://amazon.com/us/code](https://amazon.com/us/code)
2. Sign in with the Amazon account used in the Alexa mobile app
3. Enter the code → **Allow**
4. Wait until SampleApp reports Alexa is idle / Authorized

Afterwards, refresh tokens live under the SDK `db/` directory. Later launches (including systemd) should not need the browser step. Manage device settings from the [Alexa app](https://www.amazon.com/alexa-app/b?ie=UTF8&node=18354642011) or [alexa.amazon.com](https://alexa.amazon.com/).

## How this repository uses SampleApp

1. openWakeWord listens for **“Alexa”** locally (Sensory wake word from the old wiki guide is optional/unmaintained; openWakeWord is the maintained default here).
2. On detection, the daemon writes `t\n` to SampleApp stdin (**tap-to-talk**).
3. SampleApp streams audio to AVS and plays Alexa’s response.

```env
BACKEND=avs
AVS_START_SCRIPT=/home/pi/avs-sdk/startsample.sh
WAKE_ENGINE=openwakeword
WAKE_MODEL=alexa
```

## Honest limitations

- New AVS product registration may be impossible.
- The SDK is archived; builds on Bookworm may need manual dependency fixes.
- First authorization must be interactive (not fully headless).
- This environment did **not** verify a live Amazon registration, SampleApp build on Pi hardware, CBL, or Alexa-app visibility.
