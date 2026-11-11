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

## Legacy AVS path

Amazon archived the [AVS Device SDK](https://github.com/alexa/avs-device-sdk) on
2024-01-16. AVS developer tools are no longer generally available for new Alexa
Built-in devices. The optional `BACKEND=avs` mode only helps existing SampleApp
installs that still accept tap-to-talk (`t`) on stdin.
