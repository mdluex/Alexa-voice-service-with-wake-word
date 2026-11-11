#!/usr/bin/env bash
# Build the latest AVS Device SDK release (v3.0.0) SampleApp on a Raspberry Pi.
#
# Primary official guides (follow these):
#   https://alexa.github.io/avs-device-sdk/
#   https://github.com/alexa/avs-device-sdk/wiki/Home/66a5d4ef1b19a1faf1fede5ecb922a18426a6938
#   https://github.com/alexa/avs-device-sdk/wiki/Raspberry-Pi-Quick-Start-Guide-with-Script
#   https://github.com/alexa/avs-device-sdk/wiki/Raspberry-Pi-Quick-Start-Guide
#
# This wrapper mirrors the wiki "Quick Start Guide with Script" flow
# (setup.sh + pi.sh + config), pinning the SDK clone to the latest GitHub
# release tag: v3.0.0 (2022-09-29). The repo is archived; Amazon states AVS
# tools are no longer generally available for new Alexa Built-in products.
#
# Usage:
#   ./scripts/install-avs-sdk.sh /path/to/config.json
#
# config.json must match the official deviceInfo shape from the wiki:
#   { "deviceInfo": { "clientId": "...", "productId": "..." } }
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INSTALL_USER="${SUDO_USER:-${USER}}"
HOME_DIR="$(getent passwd "$INSTALL_USER" | cut -d: -f6)"
AVS_DIR="${AVS_DIR:-$HOME_DIR/avs-sdk}"
# Latest AVS Device SDK release on GitHub (also the final release).
AVS_SDK_VERSION="${AVS_SDK_VERSION:-v3.0.0}"
CONFIG_JSON="${1:-}"

if [[ -z "$CONFIG_JSON" ]]; then
  cat <<EOF >&2
Usage: $0 /path/to/config.json

Obtain config.json from the Amazon developer console when registering an AVS /
Alexa Built-in product (Login with Amazon security profile + Product ID).

Official shape (Raspberry Pi Quick Start Guide):
  {
    "deviceInfo": {
      "clientId": "amzn1.application-oa2-client....",
      "productId": "YourProductId"
    }
  }

See docs/AMAZON_AVS.md and:
  https://alexa.github.io/avs-device-sdk/
  https://github.com/alexa/avs-device-sdk/wiki/Home/66a5d4ef1b19a1faf1fede5ecb922a18426a6938

EOF
  exit 1
fi

if [[ ! -f "$CONFIG_JSON" ]]; then
  echo "config.json not found: $CONFIG_JSON" >&2
  exit 1
fi

# Normalize + validate config.json into the official deviceInfo shape.
NORMALIZED_CONFIG="$(mktemp)"
python3 - "$CONFIG_JSON" "$NORMALIZED_CONFIG" <<'PY'
import json
import re
import sys

src, dst = sys.argv[1], sys.argv[2]
with open(src, encoding="utf-8") as fh:
    data = json.load(fh)

device = data.get("deviceInfo") if isinstance(data.get("deviceInfo"), dict) else data
client_id = device.get("clientId") or device.get("clientID")
product_id = device.get("productId") or device.get("productID")
if not client_id or not product_id:
    raise SystemExit(
        "config.json must include deviceInfo.clientId and deviceInfo.productId "
        "(official AVS wiki format)."
    )
if not re.fullmatch(r"amzn1\.application-oa2-client\.[0-9a-z]{32}", client_id):
    print(
        "WARNING: clientId does not match genConfig.sh expected pattern "
        "amzn1.application-oa2-client.<32 hex chars>. Continuing anyway.",
        file=sys.stderr,
    )
if not re.fullmatch(r"[0-9a-zA-Z_]+", product_id):
    raise SystemExit("productId must be alphanumeric/underscore (no spaces).")

normalized = {"deviceInfo": {"clientId": client_id, "productId": product_id}}
with open(dst, "w", encoding="utf-8") as fh:
    json.dump(normalized, fh, indent=2)
    fh.write("\n")
print(f"config.json OK (productId={product_id!r})")
PY

echo "==> Preparing AVS build directory: $AVS_DIR (SDK $AVS_SDK_VERSION)"
mkdir -p "$AVS_DIR"
cp "$NORMALIZED_CONFIG" "$AVS_DIR/config.json"
chmod 600 "$AVS_DIR/config.json"
rm -f "$NORMALIZED_CONFIG"

echo "==> Fetching official Install scripts from alexa/avs-device-sdk@$AVS_SDK_VERSION"
cd "$AVS_DIR"
BASE="https://raw.githubusercontent.com/alexa/avs-device-sdk/${AVS_SDK_VERSION}/tools/Install"
for f in setup.sh pi.sh genConfig.sh; do
  wget -O "$f" "$BASE/$f"
  chmod +x "$f"
done

# Pin the SDK source clone to the latest release tag (setup.sh otherwise clones
# the default branch tip). Matches "build against the latest AVS Device SDK release".
if ! grep -q 'git clone --single-branch \$CLONE_URL avs-device-sdk' setup.sh \
  && ! grep -q 'git clone --single-branch $CLONE_URL avs-device-sdk' setup.sh; then
  echo "Unexpected setup.sh clone line; refusing to patch." >&2
  grep -n "git clone" setup.sh || true
  exit 1
fi
sed -i \
  's|git clone --single-branch $CLONE_URL avs-device-sdk|git clone --branch '"${AVS_SDK_VERSION}"' --single-branch "$CLONE_URL" avs-device-sdk|' \
  setup.sh

echo "==> Installing dependencies (wiki Raspberry Pi guide + Bookworm extras)"
# From wiki Raspberry Pi Quick Start Guide + packages required by pi.sh/setup.sh.
sudo apt-get update
sudo apt-get install -y \
  git gcc cmake build-essential doxygen \
  libsqlite3-dev libcurl4-openssl-dev libssl-dev libnghttp2-dev libfaad-dev \
  libsoup2.4-dev libgcrypt20-dev \
  libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev \
  libgstreamer-plugins-bad1.0-dev \
  gstreamer1.0-plugins-good gstreamer1.0-plugins-ugly \
  libasound2-dev sox wget curl python3

# commentjson is used by some SDK config tooling (manual Pi guide).
python3 -m pip install --user commentjson || true

# Modern Raspberry Pi OS often reports ID=debian; Amazon setup.sh only auto-detects
# ID=raspbian. Force the Raspberry Pi platform path from pi.sh.
export PLATFORM="Raspberry pi"
export CLONE_URL="${CLONE_URL:-https://github.com/alexa/avs-device-sdk.git}"

cat <<EOF

About to run Amazon's official setup.sh from $AVS_SDK_VERSION
(Raspberry Pi Quick Start Guide with Script flow).

This can take a long time. The SDK has been archived since 2024-01-16; Bookworm
builds may need manual fixes.

Amazon's installer asks you to type AGREE for third-party dependency terms.
This script answers AGREE automatically so ./install.sh can stay one-command.
Review: https://github.com/alexa/avs-device-sdk/wiki/Dependencies

EOF

printf 'AGREE\n' | bash ./setup.sh "$AVS_DIR/config.json"

if [[ ! -x "$AVS_DIR/startsample.sh" ]]; then
  echo "ERROR: startsample.sh was not created in $AVS_DIR" >&2
  echo "See the official guides:" >&2
  echo "  https://alexa.github.io/avs-device-sdk/" >&2
  echo "  https://github.com/alexa/avs-device-sdk/wiki/Raspberry-Pi-Quick-Start-Guide-with-Script" >&2
  exit 1
fi

echo "$AVS_SDK_VERSION" > "$AVS_DIR/AVS_SDK_VERSION"

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

if [[ -f "$REPO_ROOT/config.env" ]]; then
  sed -i 's/^BACKEND=.*/BACKEND=avs/' "$REPO_ROOT/config.env" || true
  if grep -q '^AVS_START_SCRIPT=' "$REPO_ROOT/config.env"; then
    sed -i "s|^AVS_START_SCRIPT=.*|AVS_START_SCRIPT=$AVS_DIR/startsample.sh|" "$REPO_ROOT/config.env"
  else
    echo "AVS_START_SCRIPT=$AVS_DIR/startsample.sh" >> "$REPO_ROOT/config.env"
  fi
fi

cat <<EOF

AVS Device SDK $AVS_SDK_VERSION SampleApp build finished (if setup.sh succeeded).

Official docs:
  https://alexa.github.io/avs-device-sdk/
  https://github.com/alexa/avs-device-sdk/wiki/Home/66a5d4ef1b19a1faf1fede5ecb922a18426a6938

Next (wiki Authorize and run):
  1. $REPO_ROOT/scripts/authorize-avs.sh
  2. Open https://amazon.com/us/code , enter the code, Allow
  3. Wait until SampleApp reports Alexa is idle
  4. Enable boot via ./scripts/install-service.sh (or ./install.sh)

EOF
