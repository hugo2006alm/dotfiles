#!/bin/bash
# Wait for Hyprland to start and D-Bus environment variables to be imported
sleep 1

# Kill existing portal processes to force a restart with updated environment
killall -9 xdg-desktop-portal-hyprland 2>/dev/null
killall -9 xdg-desktop-portal-gtk 2>/dev/null
killall -9 xdg-desktop-portal 2>/dev/null

# Restart the portal services using systemd user session
systemctl --user start xdg-desktop-portal-hyprland
systemctl --user start xdg-desktop-portal-gtk
systemctl --user start xdg-desktop-portal
