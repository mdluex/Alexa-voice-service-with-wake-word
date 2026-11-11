#!/usr/bin/env bash
# Install and enable the systemd user/system service for start-on-boot.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INSTALL_USER="${SUDO_USER:-${USER}}"
HOME_DIR="$(getent passwd "$INSTALL_USER" | cut -d: -f6)"
VENV_DIR="${VENV_DIR:-$HOME_DIR/.venvs/pi-voice-assistant}"
CONFIG_DIR="${CONFIG_DIR:-/etc/pi-voice-assistant}"
SERVICE_NAME="pi-voice-assistant.service"
UNIT_SRC="$REPO_ROOT/systemd/$SERVICE_NAME"
UNIT_DST="/etc/systemd/system/$SERVICE_NAME"

if [[ ! -x "$VENV_DIR/bin/python" ]]; then
  echo "Virtualenv not found at $VENV_DIR. Run scripts/install.sh first." >&2
  exit 1
fi

if [[ ! -f "$CONFIG_DIR/config.env" ]]; then
  echo "Missing $CONFIG_DIR/config.env. Run scripts/install.sh first." >&2
  exit 1
fi

TMP_UNIT="$(mktemp)"
sed \
  -e "s|@USER@|$INSTALL_USER|g" \
  -e "s|@REPO_ROOT@|$REPO_ROOT|g" \
  -e "s|@VENV_DIR@|$VENV_DIR|g" \
  -e "s|@CONFIG_DIR@|$CONFIG_DIR|g" \
  "$UNIT_SRC" > "$TMP_UNIT"

echo "==> Installing $UNIT_DST"
sudo cp "$TMP_UNIT" "$UNIT_DST"
rm -f "$TMP_UNIT"
sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl restart "$SERVICE_NAME"
sudo systemctl --no-pager --full status "$SERVICE_NAME" || true

echo
echo "Service installed. Useful commands:"
echo "  sudo systemctl status $SERVICE_NAME"
echo "  sudo journalctl -u $SERVICE_NAME -f"
echo "  sudo systemctl restart $SERVICE_NAME"
