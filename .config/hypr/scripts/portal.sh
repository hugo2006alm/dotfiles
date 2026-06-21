#!/usr/bin/env bash
sleep 1
killall -e xdg-desktop-portal-hyprland 2>/dev/null || true
killall -e xdg-desktop-portal-gnome 2>/dev/null || true
killall -e xdg-desktop-portal-kde 2>/dev/null || true
killall -e xdg-desktop-portal-lxqt 2>/dev/null || true
killall -e xdg-desktop-portal-wlr 2>/dev/null || true
killall xdg-desktop-portal 2>/dev/null || true

/usr/lib/xdg-desktop-portal-hyprland &
sleep 2
/usr/lib/xdg-desktop-portal &
