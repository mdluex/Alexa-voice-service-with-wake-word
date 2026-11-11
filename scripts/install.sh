#!/usr/bin/env bash
# Install pi-voice-assistant on Raspberry Pi OS Bookworm (or similar Debian).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INSTALL_USER="${SUDO_USER:-${USER}}"
HOME_DIR="$(getent passwd "$INSTALL_USER" | cut -d: -f6)"
VENV_DIR="${VENV_DIR:-$HOME_DIR/.venvs/pi-voice-assistant}"
CONFIG_DIR="${CONFIG_DIR:-/etc/pi-voice-assistant}"

echo "==> Installing system packages"
sudo apt-get update
sudo apt-get install -y \
  python3 \
  python3-venv \
  python3-pip \
  python3-dev \
  portaudio19-dev \
  libportaudio2 \
  libasound2-dev \
  alsa-utils \
  espeak-ng \
  sox \
  git

echo "==> Creating virtualenv at $VENV_DIR"
python3 -m venv "$VENV_DIR"
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip wheel
python -m pip install -r "$REPO_ROOT/requirements.txt"

if [[ "${INSTALL_PORCUPINE:-0}" == "1" ]]; then
  echo "==> Installing optional Porcupine packages"
  python -m pip install -r "$REPO_ROOT/requirements-porcupine.txt"
fi

echo "==> Writing config template to $CONFIG_DIR"
sudo mkdir -p "$CONFIG_DIR"
if [[ ! -f "$CONFIG_DIR/config.env" ]]; then
  sudo cp "$REPO_ROOT/config.example.env" "$CONFIG_DIR/config.env"
  sudo chown "$INSTALL_USER":"$INSTALL_USER" "$CONFIG_DIR/config.env"
  sudo chmod 600 "$CONFIG_DIR/config.env"
  echo "    Edit $CONFIG_DIR/config.env before enabling the service."
else
  echo "    Keeping existing $CONFIG_DIR/config.env"
fi

# Convenience copy in the repo for interactive runs
if [[ ! -f "$REPO_ROOT/config.env" ]]; then
  cp "$REPO_ROOT/config.example.env" "$REPO_ROOT/config.env"
  chmod 600 "$REPO_ROOT/config.env"
fi

echo "==> Validating import"
PYTHONPATH="$REPO_ROOT" "$VENV_DIR/bin/python" -m pi_voice_assistant --version

cat <<EOF

Install complete.

Next steps:
  1. Edit config:  sudo nano $CONFIG_DIR/config.env
  2. Test mic:     PYTHONPATH=$REPO_ROOT $VENV_DIR/bin/python -m pi_voice_assistant --list-audio-devices
  3. Dry-run cfg:  PYTHONPATH=$REPO_ROOT $VENV_DIR/bin/python -m pi_voice_assistant --env-file $CONFIG_DIR/config.env --validate-config
  4. Run once:     PYTHONPATH=$REPO_ROOT $VENV_DIR/bin/python -m pi_voice_assistant --env-file $CONFIG_DIR/config.env
  5. Enable boot:  $REPO_ROOT/scripts/install-service.sh

EOF
