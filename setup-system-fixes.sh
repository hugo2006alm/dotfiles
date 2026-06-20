#!/bin/bash
if [ "$EUID" -ne 0 ]; then
  echo "Please run this script with sudo: sudo bash setup-system-fixes.sh"
  exit 1
fi

echo "1. Enabling Early KMS in /etc/mkinitcpio.conf..."
sed -i 's/^MODULES=()/MODULES=(amdgpu)/' /etc/mkinitcpio.conf

echo "2. Updating GRUB command line..."
sed -i 's/^GRUB_CMDLINE_LINUX_DEFAULT="loglevel=3 quiet splash"/GRUB_CMDLINE_LINUX_DEFAULT="loglevel=3 quiet splash rd.systemd.show_status=false rd.udev.log_level=3 vt.global_cursor_default=0 vga=current"/' /etc/default/grub

echo "3. Updating greetd config to hide greeter logs..."
sed -i 's|^command = "Hyprland --config /etc/greetd/hyprland-greet.conf"$|command = "Hyprland --config /etc/greetd/hyprland-greet.conf > /dev/null 2>\&1"|' /etc/greetd/config.toml

echo "4. Creating Quiet Hyprland Session desktop entry..."
cat << 'EOF' > /usr/share/wayland-sessions/hyprland-quiet.desktop
[Desktop Entry]
Name=Hyprland (Quiet)
Comment=An intelligent dynamic tiling Wayland compositor
Exec=sh -c "/usr/bin/start-hyprland > /dev/null 2>&1"
Type=Application
DesktopNames=Hyprland
Keywords=tiling;wayland;compositor;
EOF

echo "5. Setting up passwordless sudo for ReGreet theme syncing..."
cat << 'EOF' > /etc/sudoers.d/regreet-theme
hugo2006alm ALL=(ALL) NOPASSWD: /usr/bin/cp /home/hugo2006alm/.config/greetd/regreet.css /etc/greetd/regreet.css
EOF
chmod 0440 /etc/sudoers.d/regreet-theme

echo "6. Applying mkinitcpio and grub (this might take a minute)..."
mkinitcpio -P
grub-mkconfig -o /boot/grub/grub.cfg

echo ""
echo "Done! The system fixes have been applied successfully."
