#!/bin/bash
# Removes Terminal.
SRC="$(cd "$(dirname "$0")" && pwd)"
if [ "$(id -u)" = "0" ]; then
  echo "Run this as your normal user (not with sudo)."
  exit 1
fi

sudo rm -rf /opt/pi-terminal /usr/local/bin/pi-terminal /usr/share/applications/pi-terminal.desktop \
  /usr/share/icons/hicolor/scalable/apps/pi-terminal.svg
sudo update-desktop-database -q /usr/share/applications 2>/dev/null || true
echo "Terminal removed. Your settings are still in ~/.config/pi-terminal (delete that folder to remove them)."
