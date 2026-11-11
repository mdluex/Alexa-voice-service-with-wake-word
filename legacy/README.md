# Legacy assets

## `alexa_en_raspberry-pi_v2_1_0.ppn`

This is the original Picovoice Porcupine keyword file shipped with the 2022
project. It targeted Porcupine v2 on Raspberry Pi.

Do **not** expect it to work with current Porcupine releases without regenerating
the model in the [Picovoice Console](https://console.picovoice.ai/) for your
installed SDK version and platform.

Picovoice ended free-tier AccessKeys on **2026-06-30**. Porcupine is optional in
this project and requires a paid AccessKey. The default wake-word engine is
**openWakeWord** (`pyopen-wakeword`), which includes a built-in `alexa` model
and needs no AccessKey.

## AVS path (now the default again)

Amazon archived the [AVS Device SDK](https://github.com/alexa/avs-device-sdk) on
2024-01-16 and states AVS tools are no longer generally available for new Alexa
Built-in devices. This repository still defaults to SampleApp because it remains
the closest official Amazon software that produces a real Alexa on a Pi.
Use `./install.sh` and see `docs/AMAZON_AVS.md`.
