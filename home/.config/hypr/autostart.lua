-- Autostart Configuration

-- Shared agent socket for compositor children and D-Bus activation; preserve an
-- agent supplied by a session manager. The unit starts one foreground agent.
local runtime = os.getenv("XDG_RUNTIME_DIR")
if runtime and not os.getenv("SSH_AUTH_SOCK") then
    hl.env("SSH_AUTH_SOCK", runtime .. "/shade-raid-ssh/agent.socket")
end

hl.on("hyprland.start", function()
    -- Core services
    hl.exec_cmd("awww-daemon")
    -- Import environment first, then start persistent apps through user systemd.
    -- Hyprland owns hyprland-session.target and its graphical-session lifetime.
    hl.exec_cmd("dotfiles action session")
    hl.exec_cmd("/usr/lib/polkit-gnome/polkit-gnome-authentication-agent-1")
    -- Elephant's clipboard provider owns persistent history (text and images).
    hl.exec_cmd("hyprsunset")
    hl.exec_cmd("hypridle")
    
    
    -- Initialize gsettings theme/scheme on startup to match active theme
    hl.exec_cmd([=[sh -c '
        THEME=$(cat "${XDG_STATE_HOME:-$HOME/.local/state}/shade-raid/active-theme" 2>/dev/null || cat "$HOME/.config/themes/current" 2>/dev/null || echo shade-raid)
        case "$THEME" in *-dark)
            gsettings set org.gnome.desktop.interface color-scheme "prefer-dark"
            gsettings set org.gnome.desktop.interface gtk-theme "Adwaita-dark"
            gsettings set org.gnome.desktop.interface icon-theme "Papirus-Dark"
        ;;
        *)
            gsettings set org.gnome.desktop.interface color-scheme "prefer-light"
            gsettings set org.gnome.desktop.interface gtk-theme "Adwaita"
            gsettings set org.gnome.desktop.interface icon-theme "Papirus-Light"
        ;;
        esac
    ']=])
    
    -- Wallpaper: poll socket until daemon is ready, then restore last wallpaper
    hl.exec_cmd([[sh -c '
        SOCK="$XDG_RUNTIME_DIR/wayland-1-awww-daemon.sock"
        for i in $(seq 1 10); do
            [ -S "$SOCK" ] && break
            sleep 0.2
        done
        awww restore 2>/dev/null || awww img "$HOME/wallpapers/shade-raid/wallpaper_0.jpg" --transition-type wipe --transition-angle 30
    ']])
    
    -- Generate monitor-aware drawer rules through the dotfiles API.
    -- DrawerAction reloads Hyprland only when the generated config changes.
    hl.exec_cmd("dotfiles action drawer")

    -- Keyring (auto-unlocks on autologin sessions)
    hl.exec_cmd("gnome-keyring-daemon --start --components=secrets")
    

    -- Load personal autostart if present
    local personal_path = os.getenv("HOME") .. "/.config/hypr/autostart-personal.lua"
    local pf = io.open(personal_path, "r")
    if pf then
        pf:close()
        dofile(personal_path)
    end
end)
