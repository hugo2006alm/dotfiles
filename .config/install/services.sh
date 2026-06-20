#!/bin/bash
set -e

echo "==> Enabling system services..."
sudo systemctl enable NetworkManager
sudo systemctl enable bluetooth
sudo systemctl enable sshd
sudo systemctl enable paccache.timer

echo "==> Enabling user services..."
systemctl --user enable --now pipewire pipewire-pulse wireplumber
sudo systemctl enable swayosd-libinput-backend

echo "==> Setting up firewall..."
sudo ufw enable
sudo ufw default deny incoming
sudo ufw default allow outgoing

echo "==> Configuring greetd login manager..."
sudo mkdir -p /etc/greetd
sudo cp ~/.config/greetd/hyprland-greet.conf /etc/greetd/
sudo touch /etc/greetd/regreet.toml
sudo chmod 666 /etc/greetd/regreet.toml
sudo touch /etc/greetd/regreet-background.jpg
sudo chmod 666 /etc/greetd/regreet-background.jpg
sudo touch /etc/greetd/regreet.css
sudo chmod 666 /etc/greetd/regreet.css

sudo tee /etc/greetd/config.toml > /dev/null << 'EOF'
[terminal]
vt = 1

[default_session]
command = "sh -c 'Hyprland --config /etc/greetd/hyprland-greet.conf > /dev/null 2>&1'"
user = "greeter"
EOF

sudo systemctl enable greetd
echo "==> Greetd configured for ReGreet on tty1"

echo "==> Suppressing Hyprland terminal logs on logout..."
sudo sed -i 's|^Exec=.*|Exec=/bin/sh -c "/usr/bin/start-hyprland > /dev/null 2>\&1"|' /usr/share/wayland-sessions/hyprland.desktop || true

echo "==> Configuring Plymouth sudoers exception..."
echo "hugo2006alm ALL=(root) NOPASSWD: /home/hugo2006alm/dotfiles/.config/themes/sync-plymouth.sh" | sudo tee /etc/sudoers.d/plymouth_sync > /dev/null
sudo chmod 0440 /etc/sudoers.d/plymouth_sync
