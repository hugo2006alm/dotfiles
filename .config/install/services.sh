#!/bin/bash
set -e

echo "==> Enabling system services..."
sudo systemctl enable NetworkManager
sudo systemctl enable bluetooth
sudo systemctl enable sshd
sudo systemctl enable paccache.timer

echo "==> Enabling user services..."
systemctl --user enable --now pipewire pipewire-pulse wireplumber
systemctl --user enable --now swayosd-libinput-backend

echo "==> Setting up firewall..."
sudo ufw enable
sudo ufw default deny incoming
sudo ufw default allow outgoing

echo "==> Configuring greetd login manager..."
sudo mkdir -p /etc/greetd
sudo touch /etc/greetd/tuigreet-theme.args
sudo chmod 666 /etc/greetd/tuigreet-theme.args

sudo tee /etc/greetd/config.toml > /dev/null << 'EOF'
[terminal]
vt = 1

[default_session]
command = "sh -c 'tuigreet --cmd start-hyprland --time --greeting \"Welcome to Shade Raid\" --remember --remember-session --asterisks \$(cat /etc/greetd/tuigreet-theme.args 2>/dev/null)'"
user = "greeter"
EOF

sudo systemctl enable greetd
echo "==> Greetd configured on tty1"
