#!/usr/bin/env bash

# Clear screen and show title
clear
echo "=== System Update ==="
echo ""

echo "Checking for updates..."
arch_updates=$(checkupdates 2>/dev/null)
aur_updates=$(yay -Qua 2>/dev/null)

# Clean up empty lines
arch_updates=$(echo "$arch_updates" | grep -v "^$")
aur_updates=$(echo "$aur_updates" | grep -v "^$")

arch_count=0
if [ -n "$arch_updates" ]; then
    arch_count=$(echo "$arch_updates" | wc -l)
fi

aur_count=0
if [ -n "$aur_updates" ]; then
    aur_count=$(echo "$aur_updates" | wc -l)
fi

total=$((arch_count + aur_count))

if [ "$total" -eq 0 ]; then
    echo "No updates available. System is up to date."
    echo "Press Enter to close..."
    read -r
    exit 0
fi

echo "Pending updates ($total):"
if [ $arch_count -gt 0 ]; then
    echo ""
    echo "[Pacman]"
    echo "$arch_updates"
fi

if [ $aur_count -gt 0 ]; then
    echo ""
    echo "[AUR]"
    echo "$aur_updates"
fi

echo ""
read -p "Do you want to update now? (y/N) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Running yay -Syu..."
    yay -Syu
    echo ""
    echo "Update completed."
    pkill -RTMIN+8 waybar 2>/dev/null || true
    echo "Press Enter to close..."
    read -r
else
    echo "Update cancelled."
    sleep 1
fi
