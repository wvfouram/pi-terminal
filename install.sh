#!/bin/bash
# Installer for Terminal (Windows 11 style) on Raspberry Pi
set -e
SRC="$(cd "$(dirname "$0")" && pwd)"
if [ "$(id -u)" = "0" ]; then
  echo "Run this as your normal user (not with sudo). It will ask for sudo when needed."
  exit 1
fi

echo "==> Installing packages"
sudo apt-get update || echo "   (apt update had errors, continuing)"
if ! sudo apt-get install -y python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-vte-2.91 fonts-dejavu-core xdg-utils; then
  for p in python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-vte-2.91 fonts-dejavu-core xdg-utils; do
    sudo apt-get install -y "$p" || echo "   (could not install $p)"
  done
fi
sudo apt-get install -y fonts-open-sans || echo "   (Open Sans font not available, using system font)"
for p in ; do
  sudo apt-get install -y "$p" || echo "   ($p not available, skipping)"
done

echo "==> Installing app"
sudo install -d /opt/pi-terminal
sudo install -m 644 "$SRC/pi_terminal.py" /opt/pi-terminal/pi_terminal.py
printf '#!/bin/sh\nexec /usr/bin/python3 /opt/pi-terminal/pi_terminal.py "$@"\n' | sudo tee /usr/local/bin/pi-terminal >/dev/null
sudo chmod 755 /usr/local/bin/pi-terminal

echo "==> Adding menu entry and icon"
sudo install -D -m 644 "$SRC/pi-terminal.svg" /usr/share/icons/hicolor/scalable/apps/pi-terminal.svg
sudo gtk-update-icon-cache -f -t /usr/share/icons/hicolor >/dev/null 2>&1 || true
sudo tee /usr/share/applications/pi-terminal.desktop >/dev/null <<'DESK'
[Desktop Entry]
Type=Application
Name=Terminal
GenericName=Terminal
Comment=Tabbed terminal
Exec=pi-terminal 
Icon=pi-terminal
Terminal=false
Categories=System;TerminalEmulator;GTK;
StartupWMClass=pi-terminal
StartupNotify=true
DESK
sudo update-desktop-database -q /usr/share/applications 2>/dev/null || true

echo
echo "Done. Open Terminal from the menu or run: pi-terminal"
