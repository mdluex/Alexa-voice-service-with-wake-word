#!/usr/bin/env bash
# First-time Amazon AVS SampleApp authorization (Code-Based Linking / CBL).
#
# Official flow from the AVS Device SDK Raspberry Pi guides:
#   1. Start SampleApp
#   2. When it prints NOT YET AUTHORIZED + a code, open https://amazon.com/us/code
#   3. Sign in with the Amazon account that owns the Alexa app
#   4. Enter the code and Allow
#   5. Wait until SampleApp reports Authorized / Alexa is idle
#
# References:
#   https://alexa.github.io/avs-device-sdk/
#   https://github.com/alexa/avs-device-sdk/wiki/Home/66a5d4ef1b19a1faf1fede5ecb922a18426a6938
#   https://github.com/alexa/avs-device-sdk/wiki/Raspberry-Pi-Quick-Start-Guide-with-Script
#   https://github.com/alexa/avs-device-sdk/wiki/Raspberry-Pi-Quick-Start-Guide
set -euo pipefail

INSTALL_USER="${SUDO_USER:-${USER}}"
HOME_DIR="$(getent passwd "$INSTALL_USER" | cut -d: -f6)"
AVS_DIR="${AVS_DIR:-$HOME_DIR/avs-sdk}"
START_SCRIPT="${AVS_START_SCRIPT:-$AVS_DIR/startsample.sh}"

if [[ ! -x "$START_SCRIPT" ]]; then
  echo "SampleApp start script not found/executable: $START_SCRIPT" >&2
  echo "Run ./scripts/install-avs-sdk.sh /path/to/config.json first." >&2
  exit 1
fi

cat <<EOF
========================================================================
 Amazon AVS authorization (Code-Based Linking)
========================================================================
 1. Leave this terminal open.
 2. When SampleApp prints a code, open: https://amazon.com/us/code
 3. Sign in with YOUR Amazon account (same as the Alexa mobile app).
 4. Enter the code and choose Allow.
 5. Wait until SampleApp shows that Alexa is idle.
 6. Press Ctrl+C here once authorization succeeds (tokens are stored).

Afterwards, systemd / pi-voice-assistant can start SampleApp headlessly.
========================================================================

Starting: $START_SCRIPT
EOF

cd "$(dirname "$START_SCRIPT")"
export PA_ALSA_PLUGHW=1
# Do not exec: the root ./install.sh continues to systemd after this returns.
"$START_SCRIPT"
