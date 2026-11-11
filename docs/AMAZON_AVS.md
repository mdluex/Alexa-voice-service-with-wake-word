# Real Amazon Alexa on a Raspberry Pi (official path & limits)

**Simplest install:** from the repo root run `./install.sh`, or:

```bash
curl -fsSL https://raw.githubusercontent.com/mdluex/Alexa-voice-service-with-wake-word/main/install.sh | bash
```

That single command installs dependencies, builds SampleApp, configures systemd, and only pauses for Amazon Client ID / Product ID (or `config.json`) and Login with Amazon authorization.

This project’s **default backend** is Amazon’s **Alexa Voice Service (AVS) Device SDK SampleApp**. That is the only Amazon-published software stack that makes a Raspberry Pi behave as an **Alexa Built-in** device: you speak to the Pi, Amazon’s Alexa cloud answers, and the device is authorized against your Amazon account (Code-Based Linking) so it can be managed from the Alexa mobile app / [alexa.amazon.com](https://alexa.amazon.com/).

## What Amazon says today

Amazon’s Alexa Built-in / AVS landing page states:

> Alexa Voice Service (AVS) developer tools are no longer generally available for Alexa Built-in. Please visit the Works with Alexa program if you are interested in building devices that connect to Alexa.

Sources:

- [Alexa Built-in / AVS overview](https://developer.amazon.com/en-US/alexa/alexa-voice-service)
- [Alexa Built-in devices](https://developer.amazon.com/en-US/alexa/devices/alexa-built-in)
- Nearly every remaining AVS doc page carries the same banner (for example [AVS FAQs](https://developer.amazon.com/en-US/docs/alexa/alexa-voice-service/faqs.html))

The open-source SDK itself is archived and unmaintained:

- GitHub: [alexa/avs-device-sdk](https://github.com/alexa/avs-device-sdk) — archived **2024-01-16**
- Last release: **v3.0.0** (2022-09-29)

### Works with Alexa is not a substitute

[Works with Alexa](https://developer.amazon.com/en-US/alexa/works-with-alexa) / [Alexa Connect Kit](https://developer.amazon.com/en-US/docs/alexa/ack-sdk/overview.html) let Alexa **control** a product (lights, plugs, appliances). They do **not** turn the Pi’s microphone/speaker into Alexa Built-in. Amazon’s own consumer FAQ distinguishes the two programs:

- [How Alexa works — Built-in vs Works with Alexa](https://www.amazon.com/b?ie=UTF8&node=23560784011)

**Closest official Amazon-supported route that still yields a real Alexa on the Pi:** build and run the archived **AVS Device SDK SampleApp**, using credentials from an AVS / Alexa Built-in product registration **if** the developer console still allows your account to create or reuse that product. New registrations may be blocked.

## What you must do in the Amazon developer console

Historical registration flow (Amazon’s “Register a Product with AVS” tutorial; pages may still exist behind the “no longer generally available” banner):

1. Create / sign in to an [Amazon developer account](https://developer.amazon.com/).
2. Open the Alexa Voice Service / Alexa Built-in product console (if still accessible to your account).
3. Register a product suitable for a Raspberry Pi prototype, for example:
   - Product type: Device with Alexa built-in
   - Interaction: Hands-free
   - Commercial distribution: No (prototype)
   - Choose a **Product ID** (no spaces), e.g. `PrototypePi`
4. Create a **Login with Amazon (LWA)** security profile for the product.
5. Under Other devices / platforms, generate a **Client ID**.
6. Download **`config.json`** containing at least:
   - `clientId`
   - `productId`
7. Keep `config.json` private. Place it outside git (this repo gitignores `config.json` / secrets).

If the console refuses new AVS / Alexa Built-in products, Amazon has closed the path for your account. There is no other public Amazon DIY path that produces a microphone Alexa Built-in device on a Pi.

## Build SampleApp on the Pi

```bash
# After ./scripts/install.sh
./scripts/install-avs-sdk.sh /secure/path/to/config.json
```

This fetches Amazon’s archived install scripts from the `v3.0.0` tag and runs `setup.sh`. On modern Raspberry Pi OS it forces `PLATFORM="Raspberry pi"` because Amazon’s detector only matches `ID=raspbian`.

Historical quick-start (same scripts Amazon published for Pi):

- [Raspberry Pi Quick Start Guide with Script (SDK wiki)](https://github.com/alexa/avs-device-sdk/wiki/Raspberry-Pi-Quick-Start-Guide-with-Script)

## Authorize so the device appears for your Amazon account

```bash
./scripts/authorize-avs.sh
```

When SampleApp prints **NOT YET AUTHORIZED** and a code:

1. Open [https://amazon.com/us/code](https://amazon.com/us/code)
2. Sign in with the Amazon account used in the Alexa mobile app
3. Enter the code → **Allow**
4. Wait until SampleApp reports Alexa is idle

This is Amazon’s **Code-Based Linking (CBL)** / Login with Amazon flow used by the SampleApp ([authorization overview](https://developer.amazon.com/en-US/docs/alexa/avs-device-sdk/authorization.html) — may 404/redirect under the AVS wind-down).

After success, refresh tokens are stored under the SDK `db/` directory. Later launches (including systemd) should not need the browser step. Manage device settings from the [Alexa app](https://www.amazon.com/alexa-app/b?ie=UTF8&node=18354642011) or [alexa.amazon.com](https://alexa.amazon.com/).

## How this repository uses SampleApp

1. openWakeWord listens for **“Alexa”** locally.
2. On detection, the daemon writes `t\n` to SampleApp stdin (**tap-to-talk**).
3. SampleApp streams audio to AVS and plays Alexa’s response.

Configure:

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
