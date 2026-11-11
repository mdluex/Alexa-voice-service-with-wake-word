#!/usr/bin/env bash
# Build Amazon's archived AVS Device SDK SampleApp on a Raspberry Pi.
#
# Official sources (archived / no longer generally available for new products):
#   https://github.com/alexa/avs-device-sdk
#   https://developer.amazon.com/en-US/alexa/alexa-voice-service
#   https://github.com/alexa/avs-device-sdk/wiki/Raspberry-Pi-Quick-Start-Guide-with-Script
#
# Usage:
#   ./scripts/install-avs-sdk.sh /path/to/config.json
#
# config.json comes from the Amazon developer console after registering an
# Alexa Built-in / AVS product (Client ID + Product ID). Never commit it.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INSTALL_USER="${SUDO_USER:-${USER}}"
HOME_DIR="$(getent passwd "$INSTALL_USER" | cut -d: -f6)"
AVS_DIR="${AVS_DIR:-$HOME_DIR/avs-sdk}"
CONFIG_JSON="${1:-}"

if [[ -z "$CONFIG_JSON" ]]; then
  cat <<EOF >&2
Usage: $0 /path/to/config.json

Obtain config.json from the Amazon developer console when registering an AVS /
Alexa Built-in product (Login with Amazon security profile + Product ID).

IMPORTANT: Amazon states that AVS developer tools are "no longer generally
available" for Alexa Built-in. New product registration may be blocked.
See docs/AMAZON_AVS.md.

EOF
  exit 1
fi

if [[ ! -f "$CONFIG_JSON" ]]; then
  echo "config.json not found: $CONFIG_JSON" >&2
  exit 1
fi

# Validate required keys without printing secrets.
python3 - "$CONFIG_JSON" <<'PY'
import json, sys
path = sys.argv[1]
with open(path, encoding="utf-8") as fh:
    data = json.load(fh)
missing = [k for k in ("clientId", "productId") if not data.get(k)]
if missing:
    raise SystemExit(f"config.json missing required keys: {', '.join(missing)}")
print(f"config.json OK (productId={data['productId']!r})")
PY

echo "==> Preparing AVS build directory: $AVS_DIR"
mkdir -p "$AVS_DIR"
cp "$CONFIG_JSON" "$AVS_DIR/config.json"
chmod 600 "$AVS_DIR/config.json"

echo "==> Fetching Amazon AVS Device SDK install scripts (archived GitHub)"
cd "$AVS_DIR"
BASE="https://raw.githubusercontent.com/alexa/avs-device-sdk/v3.0.0/tools/Install"
for f in setup.sh pi.sh genConfig.sh; do
  if [[ ! -f "$f" ]]; then
    wget -O "$f" "$BASE/$f"
  fi
  chmod +x "$f"
done

echo "==> Installing common build dependencies (Bookworm)"
sudo apt-get update
sudo apt-get install -y \
  git gcc cmake build-essential \
  libsqlite3-dev libssl-dev libnghttp2-dev libfaad-dev \
  libsoup2.4-dev libgcrypt20-dev \
  libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev \
  gstreamer1.0-plugins-good gstreamer1.0-plugins-ugly \
  libasound2-dev sox wget curl

# Modern Raspberry Pi OS often reports ID=debian, but Amazon's setup.sh only
# auto-detects ID=raspbian. Force the Raspberry Pi platform path.
export PLATFORM="Raspberry pi"

cat <<EOF

About to run Amazon's archived setup.sh.
This build can take a long time on a Pi and may fail on current Bookworm
toolchains because the SDK has been unmaintained since 2024-01-16.

Amazon's installer asks you to type AGREE for third-party dependency terms.
This script answers AGREE automatically so ./install.sh can stay one-command.
Review: https://github.com/alexa/avs-device-sdk/wiki/Dependencies

EOF

# setup.sh expects to be run from AVS_DIR with config.json as the first argument.
# Pipe AGREE for the External Dependencies prompt (non-interactive install).
printf 'AGREE\n' | bash ./setup.sh "$AVS_DIR/config.json"

if [[ ! -x "$AVS_DIR/startsample.sh" ]]; then
  echo "ERROR: startsample.sh was not created in $AVS_DIR" >&2
  exit 1
fi

CONFIG_ENV="${CONFIG_ENV:-/etc/pi-voice-assistant/config.env}"
if [[ -f "$CONFIG_ENV" ]]; then
  echo "==> Updating $CONFIG_ENV for AVS backend"
  sudo sed -i 's/^BACKEND=.*/BACKEND=avs/' "$CONFIG_ENV" || true
  if grep -q '^AVS_START_SCRIPT=' "$CONFIG_ENV"; then
    sudo sed -i "s|^AVS_START_SCRIPT=.*|AVS_START_SCRIPT=$AVS_DIR/startsample.sh|" "$CONFIG_ENV"
  else
    echo "AVS_START_SCRIPT=$AVS_DIR/startsample.sh" | sudo tee -a "$CONFIG_ENV" >/dev/null
  fi
fi

# Also update local repo config.env if present
if [[ -f "$REPO_ROOT/config.env" ]]; then
  sed -i 's/^BACKEND=.*/BACKEND=avs/' "$REPO_ROOT/config.env" || true
  if grep -q '^AVS_START_SCRIPT=' "$REPO_ROOT/config.env"; then
    sed -i "s|^AVS_START_SCRIPT=.*|AVS_START_SCRIPT=$AVS_DIR/startsample.sh|" "$REPO_ROOT/config.env"
  else
    echo "AVS_START_SCRIPT=$AVS_DIR/startsample.sh" >> "$REPO_ROOT/config.env"
  fi
fi

cat <<EOF

AVS SampleApp build finished (if setup.sh succeeded).

Next:
  1. Authorize the device to your Amazon account (one-time, interactive):
       $REPO_ROOT/scripts/authorize-avs.sh
  2. Confirm AVS_START_SCRIPT in config.env points to:
       $AVS_DIR/startsample.sh
  3. Run the wake-word daemon (or enable the systemd service).

After CBL authorization, the Pi is linked to your Amazon account as an AVS /
Alexa Built-in client and should be manageable from the Alexa mobile app /
alexa.amazon.com for that account.

EOF
