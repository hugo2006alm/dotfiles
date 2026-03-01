#!/bin/bash
set -e

echo "==> Enabling system services..."
sudo systemctl enable NetworkManager
sudo systemctl enable bluetooth
sudo systemctl enable sshd
sudo systemctl enable paccache.timer

echo "==> Enabling user services..."
systemctl --user enable --now pipewire pipewire-pulse wireplumber

echo "==> Setting up firewall..."
sudo ufw enable
sudo ufw default deny incoming
sudo ufw default allow outgoing

echo "==> Setting up autologin..."
CURRENT_USER=$(whoami)
sudo mkdir -p /etc/systemd/system/getty@tty1.service.d/
sudo tee /etc/systemd/system/getty@tty1.service.d/autologin.conf > /dev/null << EOF
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin $CURRENT_USER --noclear %I \$TERM
Type=simple
EOF
sudo systemctl daemon-reload
sudo systemctl enable getty@tty1.service

echo "==> Autologin configured for user: $CURRENT_USER on tty1"
