-- Autostart Configuration

hl.on("hyprland.start", function()
    -- Core services
    hl.exec_cmd("awww-daemon")
    hl.exec_cmd("sh -c 'waybar >/dev/null 2>&1 &'")
    hl.exec_cmd("mako")
    hl.exec_cmd("elephant")
    hl.exec_cmd("walker --gapplication-service")
    hl.exec_cmd("nm-applet --indicator")
    hl.exec_cmd("/usr/lib/polkit-gnome/polkit-gnome-authentication-agent-1")
    hl.exec_cmd("wl-paste --watch cliphist store")
    hl.exec_cmd("hyprsunset")
    hl.exec_cmd("hypridle")
    
    -- DBus environment
    hl.exec_cmd("dbus-update-activation-environment --systemd WAYLAND_DISPLAY XDG_CURRENT_DESKTOP XDG_SESSION_DESKTOP XDG_SESSION_TYPE HYPRLAND_INSTANCE_SIGNATURE")
    hl.exec_cmd("systemctl --user import-environment WAYLAND_DISPLAY XDG_CURRENT_DESKTOP XDG_SESSION_DESKTOP XDG_SESSION_TYPE HYPRLAND_INSTANCE_SIGNATURE")
    
    -- Wallpaper
    hl.exec_cmd([[sleep 1 && awww img $HOME/wallpapers/shade-raid/wallpaper_0.jpg --transition-type wipe --transition-angle 30]])
    
    -- Generate drawers config and reload
    hl.exec_cmd("$HOME/.config/hypr/scripts/gen-drawers.sh && hyprctl reload")

    -- Keyring (auto-unlocks on autologin sessions)
    hl.exec_cmd("gnome-keyring-daemon --start --components=secrets")
    
    -- Applications
    hl.exec_cmd("vesktop")
    hl.exec_cmd("spotify")
    hl.exec_cmd("steam -silent")
    hl.exec_cmd("heroic --no-gui")
    hl.exec_cmd("bitwarden")

    -- Start xdg-desktop-portal (must run in Hyprland session context)
    hl.exec_cmd("systemctl --user stop xdg-desktop-portal xdg-desktop-portal-hyprland 2>/dev/null; /usr/lib/xdg-desktop-portal --replace &")
end)
